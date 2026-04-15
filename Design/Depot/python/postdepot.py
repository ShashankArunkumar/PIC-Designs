import json
import math
import subprocess
import sys
from pathlib import Path

import kfactory.conf as kf_conf


def _find_setup_dir(start: Path) -> Path | None:
    for parent in start.resolve().parents:
        candidate = parent / "Setup"
        if candidate.exists():
            return candidate
    return None


def _configure_project_dir() -> Path:
    setup_dir = _find_setup_dir(Path(__file__))
    if setup_dir is not None:
        kf_conf.config.__dict__["project_dir"] = setup_dir
        return setup_dir

    fallback = Path(__file__).resolve().parents[1]
    kf_conf.config.__dict__["project_dir"] = fallback
    return fallback


def _normalize_cells(config: object) -> list[dict]:
    if isinstance(config, list):
        return config

    if isinstance(config, dict):
        if "cells" in config and isinstance(config["cells"], list):
            return config["cells"]

        required = {"letter", "number"}
        if required.issubset(config.keys()):
            return [config]

    raise ValueError(
        "postdepot.json must be a list of cells, a dict with key 'cells', "
        "or a single cell object."
    )


def _extract_nw_coordinates(cell: dict) -> dict:
    for key in ("NW coordinates", "NW_coordinates", "nw_coordinates", "nwCoordinates"):
        if key in cell:
            nw = cell[key]
            break
    else:
        raise ValueError(
            "Each cell entry must include NW coordinates under one of: "
            "'NW coordinates', 'NW_coordinates', 'nw_coordinates', 'nwCoordinates'."
        )

    if not isinstance(nw, dict):
        raise ValueError("NW coordinates must be an object with keys A, B, and C.")

    normalized = {}
    for point_name in ("A", "B", "C"):
        if point_name not in nw:
            raise ValueError(f"NW coordinates missing point '{point_name}'.")
        point = nw[point_name]
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError(
                f"NW point '{point_name}' must be [x, y] (2 values), got: {point!r}"
            )
        normalized[point_name] = (float(point[0]), float(point[1]))

    return normalized


def _calculate_slope(nw_coordinates: dict) -> float:
    """Calculate the slope of the line through point A and the midpoint of BC.
    
    Args:
        nw_coordinates: Dict with keys 'A', 'B', 'C', each mapping to (x, y) tuple.
    
    Returns:
        Slope as a float. Returns None if the line is vertical (dx == 0).
    """
    a = nw_coordinates["A"]
    b = nw_coordinates["B"]
    c = nw_coordinates["C"]
    
    # Midpoint of B and C
    midpoint_bc = ((b[0] + c[0]) / 2.0, (b[1] + c[1]) / 2.0)
    
    # Slope from A to midpoint of BC
    dx = midpoint_bc[0] - a[0]
    dy = midpoint_bc[1] - a[1]
    
    if dx == 0:
        return None  # Vertical line
    
    slope = dy / dx
    return slope


def _calculate_vector_angle_0_360(nw_coordinates: dict) -> float:
    """Calculate the direction angle from midpoint of BC to A (0-360 degrees).
    
    Origin: midpoint of BC
    Direction: vector from midpoint BC to A
    Angle: measured in standard 4-quadrant coordinate system (0-360°)
    
    Args:
        nw_coordinates: Dict with keys 'A', 'B', 'C', each mapping to (x, y) tuple.
    
    Returns:
        Angle in degrees (0-360 range).
    """
    a = nw_coordinates["A"]
    b = nw_coordinates["B"]
    c = nw_coordinates["C"]
    
    # Midpoint of B and C (origin of our coordinate system)
    origin = ((b[0] + c[0]) / 2.0, (b[1] + c[1]) / 2.0)
    
    # Vector from origin to A
    dx = a[0] - origin[0]
    dy = a[1] - origin[1]
    
    # Use atan2 to get angle in correct quadrant (-180 to 180 degrees)
    angle_radians = math.atan2(dy, dx)
    angle_degrees = math.degrees(angle_radians)
    
    # Normalize to 0-360 range
    if angle_degrees < 0:
        angle_degrees += 360.0
    
    return angle_degrees


def _determine_zone(angle_degrees: float) -> int:
    """Determine which zone the angle falls into.
    
    Args:
        angle_degrees: Angle in degrees (0-360 range)
    
    Returns:
        Zone number (1, 2, 3, or 4)
        Zone 1: 315 to 45 degrees (right direction)
        Zone 2: 45 to 135 degrees (up direction)
        Zone 3: 135 to 225 degrees (left direction)
        Zone 4: 225 to 315 degrees (down direction)
    """
    angle = angle_degrees % 360.0
    
    if (angle >= 315) or (angle < 45):
        return 1
    elif 45 <= angle < 135:
        return 2
    elif 135 <= angle < 225:
        return 3
    else:  # 225 <= angle < 315
        return 4


def _calculate_euler_bend_angle(angle_degrees: float) -> float:
    """Calculate the Euler bend turn angle based on the waveguide angle and zone.
    
    Args:
        angle_degrees: Waveguide direction angle in degrees (0-360)
    
    Returns:
        Bend turn angle in degrees
        Formula: zone_angle - waveguide_angle, where:
            Zone 1: 0 - angle
            Zone 2: 90 - angle
            Zone 3: 180 - angle
            Zone 4: 270 - angle
    """
    zone = _determine_zone(angle_degrees)
    
    zone_angles = {
        1: 0,
        2: 90,
        3: 180,
        4: 270,
    }
    
    bend_angle = zone_angles[zone] - angle_degrees
    
    return bend_angle


def _calculate_waveguide_geometry(
    nw_coordinates: dict,
    waveguide_config: dict,
) -> dict:
    """Calculate waveguide geometry based on A, B, C points.
    
    The waveguide follows the line from A to midpoint of BC, with:
    - A reference point at the midpoint of BC (centered)
    - Extends backwards (prenanowire_length) before the midpoint
    - Extends forwards (postnanowire_length) after point A
    
    Args:
        nw_coordinates: Dict with keys 'A', 'B', 'C', each mapping to (x, y) tuple.
        waveguide_config: Dict with keys 'width', 'prenanowire_length', 'postnanowire_length'.
    
    Returns:
        Dict containing:
            - 'start': (x, y) tuple for waveguide start (before midpoint BC)
            - 'end': (x, y) tuple for waveguide end (after point A)
            - 'width': waveguide width in microns
            - 'center': (x, y) tuple of midpoint BC (the center reference point)
            - 'angle': direction angle in degrees (0-360)
            - 'zone': zone number (1-4) based on angle
            - 'bend_angle': Euler bend turn angle in degrees
    """
    a = nw_coordinates["A"]
    b = nw_coordinates["B"]
    c = nw_coordinates["C"]
    
    # Midpoint of B and C
    midpoint_bc = ((b[0] + c[0]) / 2.0, (b[1] + c[1]) / 2.0)
    
    # Vector from midpoint BC to A
    dx = a[0] - midpoint_bc[0]
    dy = a[1] - midpoint_bc[1]
    
    # Distance from midpoint BC to A
    distance_to_a = math.sqrt(dx * dx + dy * dy)
    
    # Unit vector in direction from midpoint BC to A
    ux = dx / distance_to_a
    uy = dy / distance_to_a
    
    # Extract waveguide parameters
    width = waveguide_config.get("width", 0.5)
    prenanowire = waveguide_config.get("prenanowire_length", 5.0)
    postnanowire = waveguide_config.get("postnanowire_length", 1.0)
    
    # Calculate start point: prenanowire_length BEFORE midpoint BC
    # (opposite direction from A)
    start_x = midpoint_bc[0] - ux * prenanowire
    start_y = midpoint_bc[1] - uy * prenanowire
    
    # Calculate end point: postnanowire_length AFTER point A
    end_x = a[0] + ux * postnanowire
    end_y = a[1] + uy * postnanowire
    
    # Calculate angle (direction from midpoint BC to A)
    angle_radians = math.atan2(dy, dx)
    angle_degrees = math.degrees(angle_radians)
    if angle_degrees < 0:
        angle_degrees += 360.0
    
    # Determine zone and calculate bend angle
    zone = _determine_zone(angle_degrees)
    bend_angle = _calculate_euler_bend_angle(angle_degrees)
    
    # Extract all bend and waveguide parameters
    bend_radius = waveguide_config.get("bend_radius", 8.5)
    bend_180_radius = waveguide_config.get("bend_180_radius", bend_radius)
    straight_wg_length_1 = waveguide_config.get("straight_wg_length_1", 20.0)
    straight_wg_length_2 = waveguide_config.get("straight_wg_length_2", straight_wg_length_1)

    bend_180_sigh_word = str(waveguide_config.get("180_bend_sigh", "positive")).strip().lower()
    if bend_180_sigh_word == "positive":
        bend_180_sign = 1
    elif bend_180_sigh_word == "negative":
        bend_180_sign = -1
    else:
        raise ValueError("waveguide['180_bend_sigh'] must be either 'positive' or 'negative'.")

    final_waveguide_length = waveguide_config.get("final_waveguide_length", 15.0)
    grating_coupler_model = waveguide_config.get("grating_coupler_model", "GC_1550_TE")
    
    # Track current position and direction as we build the path
    current_pos = (end_x, end_y)
    current_angle_rad = math.atan2(uy, ux)
    
    # === EULER BEND 1 ===
    bend1_start = current_pos
    bend1_angle = bend_angle
    bend1_angle_rad = math.radians(bend1_angle)
    exit_angle_rad = current_angle_rad + bend1_angle_rad
    exit_ux = math.cos(exit_angle_rad)
    exit_uy = math.sin(exit_angle_rad)
    bend1_end_x = current_pos[0] + exit_ux * bend_radius
    bend1_end_y = current_pos[1] + exit_uy * bend_radius
    bend1_end = (bend1_end_x, bend1_end_y)
    
    # === STRAIGHT WAVEGUIDE 1 ===
    current_pos = bend1_end
    current_angle_rad = exit_angle_rad
    exit_ux_1 = math.cos(current_angle_rad)
    exit_uy_1 = math.sin(current_angle_rad)
    straight1_end_x = current_pos[0] + exit_ux_1 * straight_wg_length_1
    straight1_end_y = current_pos[1] + exit_uy_1 * straight_wg_length_1
    straight1_end = (straight1_end_x, straight1_end_y)
    
    # === EULER BEND 180 (±180 degrees) ===
    current_pos = straight1_end
    bend180_angle = 180 * bend_180_sign
    bend180_angle_rad = math.radians(bend180_angle)
    exit_angle_rad = current_angle_rad + bend180_angle_rad
    exit_ux_180 = math.cos(exit_angle_rad)
    exit_uy_180 = math.sin(exit_angle_rad)
    bend180_end_x = current_pos[0] + exit_ux_180 * bend_180_radius
    bend180_end_y = current_pos[1] + exit_uy_180 * bend_180_radius
    bend180_end = (bend180_end_x, bend180_end_y)
    
    # === STRAIGHT WAVEGUIDE 2 ===
    current_pos = bend180_end
    current_angle_rad = exit_angle_rad
    exit_ux_2 = math.cos(current_angle_rad)
    exit_uy_2 = math.sin(current_angle_rad)
    straight2_end_x = current_pos[0] + exit_ux_2 * straight_wg_length_2
    straight2_end_y = current_pos[1] + exit_uy_2 * straight_wg_length_2
    straight2_end = (straight2_end_x, straight2_end_y)
    
    # === EULER BEND INVERSE (negative of first bend) ===
    current_pos = straight2_end
    bend_inv_angle = -bend_angle
    bend_inv_angle_rad = math.radians(bend_inv_angle)
    exit_angle_rad = current_angle_rad + bend_inv_angle_rad
    exit_ux_inv = math.cos(exit_angle_rad)
    exit_uy_inv = math.sin(exit_angle_rad)
    bend_inv_end_x = current_pos[0] + exit_ux_inv * bend_radius
    bend_inv_end_y = current_pos[1] + exit_uy_inv * bend_radius
    bend_inv_end = (bend_inv_end_x, bend_inv_end_y)
    
    # === FINAL STRAIGHT WAVEGUIDE ===
    current_pos = bend_inv_end
    current_angle_rad = exit_angle_rad
    exit_ux_final = math.cos(current_angle_rad)
    exit_uy_final = math.sin(current_angle_rad)
    final_wg_end_x = current_pos[0] + exit_ux_final * final_waveguide_length
    final_wg_end_y = current_pos[1] + exit_uy_final * final_waveguide_length
    final_wg_end = (final_wg_end_x, final_wg_end_y)
    
    # === GRATING COUPLER position ===
    gc_position = final_wg_end
    
    return {
        "start": (start_x, start_y),
        "end": (end_x, end_y),
        "center": midpoint_bc,
        "width": width,
        "angle": angle_degrees,
        "zone": zone,
        "bend_angle": bend_angle,
        "bend_radius": bend_radius,
        "bend_180_radius": bend_180_radius,
        "bend1_start": bend1_start,
        "bend1_end": bend1_end,
        "bend1_angle": bend1_angle,
        "straight1_start": bend1_end,
        "straight1_end": straight1_end,
        "straight1_length": straight_wg_length_1,
        "bend180_start": straight1_end,
        "bend180_end": bend180_end,
        "bend180_angle": bend180_angle,
        "straight2_start": bend180_end,
        "straight2_end": straight2_end,
        "straight2_length": straight_wg_length_2,
        "bend_inv_start": straight2_end,
        "bend_inv_end": bend_inv_end,
        "bend_inv_angle": bend_inv_angle,
        "final_wg_start": bend_inv_end,
        "final_wg_end": final_wg_end,
        "final_wg_length": final_waveguide_length,
        "gc_position": gc_position,
        "gc_model": grating_coupler_model,
    }


def _add_waveguide_to_cell(component: object, waveguide_geometry: dict) -> None:
    """Add a waveguide to the component based on calculated geometry."""
    import gdsfactory as gf
    import random
    
    start = waveguide_geometry["start"]
    end = waveguide_geometry["end"]
    width = waveguide_geometry["width"]
    
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.sqrt(dx * dx + dy * dy)
    
    ux = dx / length
    uy = dy / length
    px = -uy
    py = ux
    hw = width / 2.0
    
    corner1 = (start[0] + px * hw, start[1] + py * hw)
    corner2 = (start[0] - px * hw, start[1] - py * hw)
    corner3 = (end[0] - px * hw, end[1] - py * hw)
    corner4 = (end[0] + px * hw, end[1] + py * hw)
    
    waveguide = gf.Component(f"waveguide_{random.randint(10000, 99999)}")
    waveguide.add_polygon([corner1, corner2, corner3, corner4], layer=(1, 0))
    component.add_ref(waveguide)


def _add_euler_bend_to_cell(component: object, waveguide_geometry: dict, bend_key: str = "bend1") -> None:
    """Add an Euler bend to the component."""
    import gdsfactory as gf
    import random
    
    start_key = f"{bend_key}_start"
    angle_key = f"{bend_key}_angle"
    
    if start_key not in waveguide_geometry:
        return
    
    bend_start = waveguide_geometry[start_key]
    bend_angle = waveguide_geometry[angle_key]
    bend_radius = waveguide_geometry["bend_radius"]
    width = waveguide_geometry["width"]
    
    if bend_key == "bend1":
        start_angle = waveguide_geometry["angle"]
    elif bend_key == "bend180":
        start_angle = waveguide_geometry["angle"] + math.radians(waveguide_geometry["bend1_angle"])
    elif bend_key == "bend_inv":
        start_angle = waveguide_geometry["angle"] + math.radians(waveguide_geometry["bend180_angle"])
    else:
        start_angle = waveguide_geometry["angle"]
    
    euler_bend = gf.components.bend_euler_all_angle(
        radius=bend_radius,
        angle=bend_angle,
        width=width,
    )
    
    bend = gf.Component(f"{bend_key}_{random.randint(10000, 99999)}")
    bend_ref = bend.add_ref_off_grid(euler_bend)
    bend_ref.move(bend_start)
    bend_ref.rotate(math.degrees(start_angle), center=bend_start)
    
    component.add_ref(bend)


def _add_straight_wg_to_cell(component: object, waveguide_geometry: dict, wg_key: str = "straight1") -> None:
    """Add a straight waveguide section to the component."""
    import gdsfactory as gf
    import random
    
    start_key = f"{wg_key}_start"
    end_key = f"{wg_key}_end"
    
    if start_key not in waveguide_geometry:
        return
    
    start = waveguide_geometry[start_key]
    end = waveguide_geometry[end_key]
    width = waveguide_geometry["width"]
    
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.sqrt(dx * dx + dy * dy)
    
    if length > 0:
        ux = dx / length
        uy = dy / length
    else:
        ux, uy = 1, 0
    
    px = -uy
    py = ux
    hw = width / 2.0
    
    corner1 = (start[0] + px * hw, start[1] + py * hw)
    corner2 = (start[0] - px * hw, start[1] - py * hw)
    corner3 = (end[0] - px * hw, end[1] - py * hw)
    corner4 = (end[0] + px * hw, end[1] + py * hw)
    
    waveguide = gf.Component(f"{wg_key}_{random.randint(10000, 99999)}")
    waveguide.add_polygon([corner1, corner2, corner3, corner4], layer=(1, 0))
    component.add_ref(waveguide)


def _add_grating_coupler_to_cell(component: object, waveguide_geometry: dict) -> None:
    """Add a grating coupler to the component."""
    import gdsfactory as gf
    import random
    
    gc_position = waveguide_geometry["gc_position"]
    
    gc = gf.Component(f"grating_coupler_{random.randint(10000, 99999)}")
    gc_size = 10.0
    gc.add_polygon(
        [
            (-gc_size / 2, -gc_size / 2),
            (gc_size / 2, -gc_size / 2),
            (gc_size / 2, gc_size / 2),
            (-gc_size / 2, gc_size / 2),
        ],
        layer=(1, 0),
    )
    
    gc_ref = component.add_ref(gc)
    gc_ref.move(gc_position)


def _build_one_cell_in_subprocess(
    *,
    cell_py_path: Path,
    gds_path: Path,
    letter: str,
    number: int,
    nw_coordinates: dict,
    slope: float,
    waveguide_geometry: dict,
) -> None:
    # A fresh interpreter avoids gdsfactory duplicate-name collisions when
    # existing cell.py uses fixed component names (for example marker_8x8).
    worker_code = r'''
import importlib.util
import json
import math
import sys
import random
from pathlib import Path

import gdsfactory as gf

payload = json.loads(sys.stdin.read())
cell_py_path = Path(payload["cell_py_path"])
gds_path = Path(payload["gds_path"])

spec = importlib.util.spec_from_file_location("postdepot_cell_runtime", cell_py_path)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to import existing cell module from {cell_py_path}")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

letter = payload["letter"]
number = int(payload["number"])
nw_coordinates = payload["nw_coordinates"]
slope = payload.get("slope")  # Slope through A and midpoint of BC
waveguide_geometry = payload.get("waveguide_geometry")  # Waveguide parameters

if not hasattr(module, "create_outline"):
    raise RuntimeError("Existing cell.py must define create_outline().")

# Use globals to set letter, number, num_rows, num_cols for create_outline()
module.letter = letter
module.number = number
module.num_rows = 3  # Default from cell.py
module.num_cols = 3  # Default from cell.py

component = module.create_outline()

# Add NW triangle here (cell.py create_outline intentionally excludes it).
a = nw_coordinates["A"]
b = nw_coordinates["B"]
c = nw_coordinates["C"]
component.add_polygon([a, b, c], layer=(24, 0))

def _calculate_vector_angle_0_360(nw_coords):
    """Calculate the direction angle from midpoint of BC to A (0-360 degrees)."""
    a = nw_coords["A"]
    b = nw_coords["B"]
    c = nw_coords["C"]
    origin = ((b[0] + c[0]) / 2.0, (b[1] + c[1]) / 2.0)
    dx = a[0] - origin[0]
    dy = a[1] - origin[1]
    angle_radians = math.atan2(dy, dx)
    angle_degrees = math.degrees(angle_radians)
    if angle_degrees < 0:
        angle_degrees += 360.0
    return angle_degrees

# Add waveguide sections if geometry is provided
if waveguide_geometry:
    width = waveguide_geometry["width"]
    
    # Section 0: Main waveguide (from start to end, before bends) - manual polygon
    start = waveguide_geometry["start"]
    end = waveguide_geometry["end"]
    
    dx_wg = end[0] - start[0]
    dy_wg = end[1] - start[1]
    length_wg = math.sqrt(dx_wg * dx_wg + dy_wg * dy_wg)
    
    ux = dx_wg / length_wg
    uy = dy_wg / length_wg
    px = -uy
    py = ux
    hw = width / 2.0
    
    corner1 = (start[0] + px * hw, start[1] + py * hw)
    corner2 = (start[0] - px * hw, start[1] - py * hw)
    corner3 = (end[0] - px * hw, end[1] - py * hw)
    corner4 = (end[0] + px * hw, end[1] + py * hw)
    
    waveguide_comp = gf.Component(f"waveguide_main_{random.randint(10000, 99999)}")
    waveguide_comp.add_polygon([corner1, corner2, corner3, corner4], layer=(1, 0))
    component.add_ref(waveguide_comp)

    # Sections 1-7: port-connected chain from bend1 onward
    bend_radius = waveguide_geometry["bend_radius"]
    bend_180_radius = waveguide_geometry["bend_180_radius"]
    bend1_angle = waveguide_geometry["bend1_angle"]
    bend180_angle = waveguide_geometry["bend180_angle"]
    bend_inv_angle = waveguide_geometry["bend_inv_angle"]
    straight1_length = waveguide_geometry["straight1_length"]
    straight2_length = waveguide_geometry["straight2_length"]
    final_length = waveguide_geometry["final_wg_length"]

    bend_cell = gf.Component(f"waveguide_chain_{random.randint(10000, 99999)}")

    bend1 = gf.components.bend_euler_all_angle(
        radius=bend_radius,
        angle=bend1_angle,
        width=width,
        layer=(1, 0),
    )
    bend180 = gf.components.bend_euler(
        radius=bend_180_radius,
        angle=bend180_angle,
        width=width,
        layer=(1, 0),
    )
    bend_inv = gf.components.bend_euler_all_angle(
        radius=bend_radius,
        angle=bend_inv_angle,
        width=width,
        layer=(1, 0),
    )
    s1_base = gf.components.straight(length=straight1_length, width=width)
    s2_base = gf.components.straight(length=straight2_length, width=width)
    s3_base = gf.components.straight(length=final_length, width=width)

    b1 = bend_cell.add_ref_off_grid(bend1)
    s1 = bend_cell << s1_base
    s1.connect("o1", b1.ports["o2"])

    b = bend_cell << bend180
    b.connect("o1", s1.ports["o2"])

    s2 = bend_cell << s2_base
    s2.connect("o1", b.ports["o2"])

    b2 = bend_cell.add_ref_off_grid(bend_inv)
    b2.connect("o1", s2.ports["o2"])

    s3 = bend_cell << s3_base
    s3.connect("o1", b2.ports["o2"])

    bend_cell.add_port("o1", port=b1.ports["o1"])
    bend_cell.add_port("o2", port=s3.ports["o2"])

    # Position the full chain so bend1 starts where the main segment ends
    chain_ref = component.add_ref_off_grid(bend_cell)
    start_angle_deg = waveguide_geometry["angle"]
    bend1_start = waveguide_geometry["bend1_start"]
    chain_ref.rotate(start_angle_deg, center=(0, 0))
    chain_ref.move(bend1_start)

    # Load real grating coupler from Design/Python codes/grating_couplers.py
    gc_py_path = cell_py_path.parents[2] / "Python codes" / "grating_couplers.py"
    if not gc_py_path.exists():
        raise FileNotFoundError(f"Missing grating coupler generator: {gc_py_path}")

    gc_spec = importlib.util.spec_from_file_location("postdepot_gc_runtime", gc_py_path)
    if gc_spec is None or gc_spec.loader is None:
        raise RuntimeError(f"Unable to import grating coupler module from {gc_py_path}")

    gc_module = importlib.util.module_from_spec(gc_spec)
    gc_spec.loader.exec_module(gc_module)

    requested_gc = waveguide_geometry.get("gc_model")
    try:
        gc_component = gc_module.create_grating_coupler(name=requested_gc, layer=(1, 0), port_width=width)
    except Exception as exc:
        # Fallback to the JSON default model if requested model is missing/invalid.
        gc_component = gc_module.create_grating_coupler(name=None, layer=(1, 0), port_width=width)
        print(f"Warning: failed to load GC model '{requested_gc}', using default model. Details: {exc}")

    gc_ref = component.add_ref_off_grid(gc_component)
    gc_ref.connect("o1", chain_ref.ports["o2"])

component.write_gds(gds_path)
component.show()
print(f"Generated: {gds_path}")

angle_deg = _calculate_vector_angle_0_360(nw_coordinates)
print(f"Angle (vector midpoint BC to A): {angle_deg:.2f}")
if waveguide_geometry:
    print(f"Waveguide: start={waveguide_geometry['start']}, end={waveguide_geometry['end']}, width={waveguide_geometry['width']}µm, angle={waveguide_geometry['angle']:.2f}°, zone={waveguide_geometry['zone']}, bend_angle={waveguide_geometry['bend_angle']:.2f}°")
'''

    payload = {
        "cell_py_path": str(cell_py_path),
        "gds_path": str(gds_path),
        "letter": letter,
        "number": number,
        "nw_coordinates": nw_coordinates,
        "slope": slope,
        "waveguide_geometry": waveguide_geometry,
    }

    result = subprocess.run(
        [sys.executable, "-c", worker_code],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Failed to build one cell with existing cell.py.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    if result.stdout.strip():
        print(result.stdout.strip())


def main() -> None:
    project_dir = _configure_project_dir()

    script_dir = Path(__file__).resolve().parent
    depot_dir = script_dir.parent

    config_path = depot_dir / "Json" / "postdepot.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing configuration file: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        raw_config = json.load(f)

    cells = _normalize_cells(raw_config)

    existing_cell_py = script_dir / "cell.py"
    if not existing_cell_py.exists():
        raise FileNotFoundError(f"Missing existing cell.py: {existing_cell_py}")

    gds_out_dir = project_dir / "build" / "gds"
    gds_out_dir.mkdir(parents=True, exist_ok=True)

    for cell in cells:
        letter = str(cell["letter"])
        number = int(cell["number"])
        nw_coordinates = _extract_nw_coordinates(cell)
        slope = _calculate_slope(nw_coordinates)
        
        # Extract waveguide configuration if present
        waveguide_config = cell.get("waveguide", {})
        if waveguide_config:
            waveguide_geometry = _calculate_waveguide_geometry(nw_coordinates, waveguide_config)
        else:
            waveguide_geometry = None

        _build_one_cell_in_subprocess(
            cell_py_path=existing_cell_py,
            gds_path=gds_out_dir / f"postdepot_{letter}{number}.gds",
            letter=letter,
            number=number,
            nw_coordinates=nw_coordinates,
            slope=slope,
            waveguide_geometry=waveguide_geometry,
        )
        angle_deg = _calculate_vector_angle_0_360(nw_coordinates)
        print(f"Cell {letter}{number}: angle = {angle_deg:.2f}")


if __name__ == "__main__":
    main()
