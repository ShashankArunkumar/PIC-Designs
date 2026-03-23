import os
import copy
import json

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"  # Prevent .pyc file creation

import gdsfactory as gf
from pathlib import Path
import kfactory.conf as kf_conf

# Route gdsfactory build artifacts to Setup/build.
for _parent in Path(__file__).resolve().parents:
    _setup_dir = _parent / "Setup"
    if _setup_dir.exists():
        kf_conf.config.__dict__["project_dir"] = _setup_dir
        break
from length import build_length_element


# gdsfactory 9.x requires an active PDK before geometry/layer creation.
try:
    gf.get_active_pdk()
except Exception:
    try:
        gf.gpdk.PDK.activate()
    except Exception:
        from gdsfactory.generic_tech import get_generic_pdk

        get_generic_pdk().activate()


def generate_lengths(start: int = 1000, stop: int = 2400, step: int = 100) -> list[float]:
    """Generate inclusive L values."""
    return [float(value) for value in range(start, stop + 1, step)]


def add_fixed_grid(
    component: gf.Component,
    grid_size: float = 500.0,
    n_boxes: int = 5,
    grid_layer: tuple[int, int] = (98, 0),
    grid_line_width: float = 0.5,
) -> tuple[float, float]:
    """Add a fixed n_boxes x n_boxes grid with top-left corner at the origin."""
    total_size = grid_size * n_boxes
    grid = gf.Component()

    for i in range(n_boxes + 1):
        x = i * grid_size
        vline = grid << gf.components.rectangle(
            size=(grid_line_width, total_size), layer=grid_layer
        )
        vline.move((x - grid_line_width / 2, -total_size))

    for j in range(n_boxes + 1):
        y = -j * grid_size
        hline = grid << gf.components.rectangle(
            size=(total_size, grid_line_width), layer=grid_layer
        )
        hline.move((0, y - grid_line_width / 2))

    component << grid
    return total_size, total_size


def add_d_distance_text(
    component: gf.Component,
    d_distance: float,
    text_layer: tuple[int, int],
    text_size: float = 20.0,
    offset_x: float = 25.0,
    offset_y: float = -25.0,
) -> None:
    """Add plain top-left text label with D-prefixed distance."""
    distance_int = int(round(d_distance))
    label = component << gf.components.text(
        text=f"D{distance_int}",
        size=text_size,
        layer=text_layer,
    )
    # Move text so its top-left sits near the top-left grid origin.
    label.move(origin=(label.xmin, label.ymax), destination=(offset_x, offset_y))


def add_corner_alignment_marks(
    component: gf.Component,
    total_size: float,
    marker_layer: tuple[int, int],
    marker_size: float = 8.0,
    center_offset: float = 20.0,
    cluster_spacing: float = 20.0,
) -> None:
    """Add 3-marker corner clusters: corner mark + two inward marks."""
    marks = gf.Component()
    corners = [
        # (corner marker center), (inward x direction), (inward y direction)
        ((center_offset, -center_offset), (1.0, 0.0), (0.0, -1.0)),
        ((total_size - center_offset, -center_offset), (-1.0, 0.0), (0.0, -1.0)),
        ((center_offset, -(total_size - center_offset)), (1.0, 0.0), (0.0, 1.0)),
        ((total_size - center_offset, -(total_size - center_offset)), (-1.0, 0.0), (0.0, 1.0)),
    ]
    for (cx, cy), (dx1, dy1), (dx2, dy2) in corners:
        positions = [
            (cx, cy),
            (cx + cluster_spacing * dx1, cy + cluster_spacing * dy1),
            (cx + cluster_spacing * dx2, cy + cluster_spacing * dy2),
        ]
        for px, py in positions:
            m = marks << gf.components.rectangle(
                size=(marker_size, marker_size), layer=marker_layer, centered=True
            )
            m.move((px, py))
    component << marks


def load_length_array_params(json_path: str) -> dict:
    with open(json_path, "r") as f:
        return json.load(f)


def create_length_array(array_params: dict) -> gf.Component:
    """Create length array from JSON-configured layout and spacing parameters."""
    array_cfg = array_params.get("array", {})
    length_cfg = array_cfg.get("lengths", {})
    grid_cfg = array_cfg.get("grid", {})
    marker_cfg = array_cfg.get("alignment_marks", {})
    label_cfg = array_cfg.get("distance_label", {})
    placement_cfg = array_cfg.get("placement", {})

    lengths = generate_lengths(
        int(length_cfg.get("start", 1000)),
        int(length_cfg.get("stop", 2400)),
        int(length_cfg.get("step", 100)),
    )
    
    d_distance = float(array_params.get("length_element", {}).get("D", 600))
    d_int = int(round(d_distance))
    array_name = f"d{d_int}"
    array = gf.Component(array_name)

    array_layers = array_params.get("layers", {})
    length_layers = array_params.get("length_element", {}).get("layers", {})
    grid_layer = tuple(array_layers.get("grid", [98, 0]))
    marker_layer = tuple(array_layers.get("marker", [95, 0]))
    label_text_layer = tuple(array_layers.get("text", length_layers.get("text", [4, 0])))
    waveguide_layer = tuple(length_layers.get("waveguide", [1, 0]))

    total_w, _ = add_fixed_grid(
        component=array,
        grid_size=float(grid_cfg.get("box_size", 500.0)),
        n_boxes=int(grid_cfg.get("boxes", 5)),
        grid_layer=grid_layer,
        grid_line_width=float(grid_cfg.get("line_width", 0.5)),
    )

    add_corner_alignment_marks(
        component=array,
        total_size=total_w,
        marker_layer=marker_layer,
        marker_size=float(marker_cfg.get("size", 8.0)),
        center_offset=float(marker_cfg.get("offset_from_grid", 20.0)),
        cluster_spacing=float(marker_cfg.get("cluster_spacing", 20.0)),
    )

    add_d_distance_text(
        component=array,
        d_distance=d_distance,
        text_layer=label_text_layer,
        text_size=float(label_cfg.get("size", 25.0)),
        offset_x=float(label_cfg.get("offset_x", 100.0)),
        offset_y=float(label_cfg.get("offset_y", -100.0)),
    )

    start_x = float(placement_cfg.get("start_x", 180.0))
    start_y = float(placement_cfg.get("start_y", -220.0))
    local_y_spacing = float(array_cfg.get("y_spacing", 130.0))
    top_cell_prefix = str(array_cfg.get("top_cell_prefix", "L"))
    bend_radius = float(array_params.get("length_element", {}).get("bend_radius", 10.0))
    waveguide_width = float(array_params.get("length_element", {}).get("width", 0.3))
    taper_length_value = float(array_params.get("length_element", {}).get("taper_length", 20.0))
    grating_coupler_model = array_params.get("length_element", {}).get("grating_coupler_model", "GC_1550_TE")
    current_y = start_y

    for length in lengths:
        top_cell_name = f"{top_cell_prefix}{int(length)}"

        length_element = build_length_element(
            length_value=length,
            distance_value=d_distance,
            grating_coupler_model=grating_coupler_model,
            layer=waveguide_layer,
            bend_radius=bend_radius,
            waveguide_width=waveguide_width,
            taper_length_value=taper_length_value,
        )
        
        # Override component name
        length_element.name = top_cell_name

        ref = array << length_element
        ref.move((start_x, current_y))
        current_y -= local_y_spacing

    return array


if __name__ == "__main__":
    array_json_path = os.path.join(
        os.path.dirname(__file__), "..", "Json", "length_array.json"
    )
    array_params = load_length_array_params(array_json_path)

    length_array = create_length_array(array_params)

    length_array.show()

