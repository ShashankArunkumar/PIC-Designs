import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Prevent .pyc file creation

import gdsfactory as gf
from pathlib import Path
import kfactory.conf as kf_conf

# Route gdsfactory build artifacts to Setup/build.
for _parent in Path(__file__).resolve().parents:
    _setup_dir = _parent / "Setup"
    if _setup_dir.exists():
        kf_conf.config.__dict__["project_dir"] = _setup_dir
        breakimport numpy as np
import json
from grating_couplers import create_grating_coupler, get_gc_params, get_gc_width

# gdsfactory 9.x requires an active PDK before geometry/layer creation.
try:
    gf.get_active_pdk()
except Exception:
    try:
        gf.gpdk.PDK.activate()
    except Exception:
        from gdsfactory.generic_tech import get_generic_pdk
        get_generic_pdk().activate()

# Load parameters from JSON file
json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Json", "length.json")
with open(json_path, 'r') as f:
    config = json.load(f)

params = config["parameters"]

# Extract parameters
L = params["geometry"]["L"]  # Total waveguide length
D = params["geometry"]["D"]  # Horizontal distance between output coupler ports
R = params["geometry"]["bend_radius"]  # 90° bend radius
width = params["geometry"]["width"]
layer = tuple(params["layers"]["waveguide"])
text_layer = tuple(params["layers"]["text"])
text_size = params["text"]["size"]
text_offset_left = params["text"]["offset_left"]
text_offset_right = params["text"]["offset_right"]
enable_text = params["text"]["enable"]
taper_length = params["taper"]["length"]
grating_coupler_model = params.get("grating_coupler_model", "GC_1550_TE")
grating_coupler_config = get_gc_params(grating_coupler_model)

# Define the cross_section for extrusion
cross_section = gf.cross_section.strip(width=width, layer=layer)


def calculate_dimensions(
    total_length: float,
    coupler_distance: float,
    bend_radius: float,
    taper_length_value: float,
) -> tuple[float, float, float]:
    """Solve x, y, z from the updated path constraints including tapers."""
    z_value = total_length / 5
    x_value = (coupler_distance - z_value - 4 * bend_radius + 70 - 2 * taper_length_value) / 10
    y_value = (total_length - 10 * x_value - z_value + 70 - 2 * taper_length_value) / 4

    if x_value <= 0:
        raise ValueError(
            f"Computed x must be positive. Received x={x_value:.3f} for L={total_length}, D={coupler_distance}, R={bend_radius}, taper={taper_length_value}."
        )
    if y_value <= 0:
        raise ValueError(
            f"Computed y must be positive. Received y={y_value:.3f} for L={total_length}, D={coupler_distance}, R={bend_radius}, taper={taper_length_value}."
        )

    return x_value, y_value, z_value


def build_length_path(
    total_length: float,
    coupler_distance: float,
    bend_radius: float,
    taper_length_value: float,
) -> tuple[gf.Path, tuple[float, float, float]]:
    """Create the parametric path and return it with solved dimensions."""
    x_value, y_value, z_value = calculate_dimensions(
        total_length, coupler_distance, bend_radius, taper_length_value
    )

    path = gf.Path()
    path += gf.path.straight(length=5 * x_value +45)
    path += gf.path.euler(radius=bend_radius, angle=-90)
    path += gf.path.straight(length=2 * y_value)
    path += gf.path.euler(radius=bend_radius, angle=90)
    path += gf.path.straight(length = z_value -160)
    path += gf.path.euler(radius=bend_radius, angle=90)
    path += gf.path.straight(length=2 * y_value)
    path += gf.path.euler(radius=bend_radius, angle=-90)
    path += gf.path.straight(length=5 * x_value+45)

    return path, (x_value, y_value, z_value)


def report_dimensions(
    total_length: float,
    coupler_distance: float,
    bend_radius: float,
    taper_length_value: float,
) -> None:
    """Print solved dimensions and geometry checks for one device."""
    x_value, y_value, z_value = calculate_dimensions(
        total_length, coupler_distance, bend_radius, taper_length_value
    )
    total_horizontal_straight = 10 * x_value + z_value - 70
    total_vertical_straight = 4 * y_value
    taper_contribution = 2 * taper_length_value
    bend_horizontal_contribution = 4 * bend_radius
    radius_bend_contribution = 4 * (np.pi / 2) * bend_radius
    total_straight_no_tapers = total_horizontal_straight + total_vertical_straight
    total_straight_with_tapers = total_straight_no_tapers + taper_contribution
    total_horizontal_with_bends = total_horizontal_straight + bend_horizontal_contribution
    total_horizontal_with_tapers = total_horizontal_with_bends + taper_contribution
    total_path_length = total_straight_with_tapers + radius_bend_contribution
    path, _ = build_length_path(
        total_length, coupler_distance, bend_radius, taper_length_value
    )
    endpoint_x = path.points[-1][0]
    endpoint_y = path.points[-1][1]

    print(f"Scaling parameter x: {x_value:.4f} µm")
    print(f"Scaling parameter y: {y_value:.4f} µm")
    print(f"Scaling parameter z (from z = L / 5): {z_value:.4f} µm")
    print(f"\nComponent lengths:")
    print(f"  Side horizontal each (5x + 45): {5 * x_value + 45:.2f} µm")
    print(f"  Middle horizontal (z - 140): {z_value - 140:.2f} µm")
    print(f"  2y (vertical): {2 * y_value:.2f} µm")
    print(f"  Taper each side: {taper_length_value:.2f} µm")
    print(f"\nVerification:")
    print(f"  Horizontal straight (10x + z - 50): {total_horizontal_straight:.2f} µm")
    print(f"  Bend horizontal contribution (4R): {bend_horizontal_contribution:.2f} µm")
    print(f"  Taper horizontal contribution (2T): {taper_contribution:.2f} µm")
    print(f"  Total horizontal including tapers: {total_horizontal_with_tapers:.2f} µm (Target D: {coupler_distance:.2f} µm)")
    print(f"  Vertical straight (4y): {total_vertical_straight:.2f} µm")
    print(f"  Total straight with tapers: {total_straight_with_tapers:.2f} µm (Target L: {total_length:.2f} µm)")
    print(f"  Bend arc length (2πR): {radius_bend_contribution:.2f} µm")
    print(f"  Full path length including bends: {total_path_length:.2f} µm")
    print(f"\nPath endpoint: ({endpoint_x:.2f}, {endpoint_y:.2f}) µm")
    print(
        f"Expected coupler distance with tapers: {coupler_distance:.2f} µm "
        f"(match: {abs((endpoint_x + taper_contribution) - coupler_distance) < 0.1})"
    )


def build_length_element(
    length_value: float,
    distance_value: float,
    grating_coupler_model: str = "GC_1550_TE",
    layer: tuple = (1, 0),
    bend_radius: float | None = None,
    waveguide_width: float | None = None,
    taper_length_value: float | None = None,
) -> gf.Component:
    """
    Build a single length element with parametric L and D values.
    
    Parameters:
    -----------
    length_value : float
        Straight-section constraint used to derive z, x, and y.
    distance_value : float
        Horizontal distance between coupler ports including tapers.
    grating_coupler_model : str
        Name of the grating coupler model to use.
    layer : tuple
        Layer for waveguide geometry.
    
    Returns:
    --------
    component : gf.Component
        Complete device with grating couplers and tapers.
    """
    # Local parameters for this element
    L_local = length_value
    D_local = distance_value
    R_local = bend_radius if bend_radius is not None else R
    width_local = waveguide_width if waveguide_width is not None else width
    layer_local = layer
    taper_length_local = taper_length_value if taper_length_value is not None else taper_length
    
    cross_section_local = gf.cross_section.strip(width=width_local, layer=layer_local)
    P_local, _ = build_length_path(L_local, D_local, R_local, taper_length_local)
    
    component = gf.Component("length_element")
    
    # Create and add waveguide
    wg = gf.path.extrude(P_local, cross_section=cross_section_local)
    wg_ref = component << wg
    
    # Create taper and grating coupler
    gc = create_grating_coupler(grating_coupler_model, layer=layer_local)
    gc_width = get_gc_width(grating_coupler_model)
    
    taper = gf.components.taper(
        length=taper_length_local,
        width1=gc_width,
        width2=width_local,
        layer=layer_local,
    )
    
    # Add left grating coupler and taper
    taper_left = component << taper
    gc_left = component << gc
    taper_left.connect("o2", wg_ref.ports["o1"])
    gc_left.connect("o1", taper_left.ports["o1"])
    
    # Add right grating coupler and taper
    taper_right = component << taper
    gc_right = component << gc
    taper_right.connect("o2", wg_ref.ports["o2"])
    gc_right.connect("o1", taper_right.ports["o1"])
    
    return component


if __name__ == "__main__":
    report_dimensions(L, D, R, taper_length)

    # Create and display the component
    device = build_length_element(length_value=L, distance_value=D, grating_coupler_model=grating_coupler_model, layer=layer)
    
    # Print port information
    print("\n--- Port Information ---")
    for port_name in device.ports:
        port = device.ports[port_name]
        print(f"Port {port_name}: position={port.center}, angle={port.angle:.1f}°")
    
    # Visualize
    device.show()

