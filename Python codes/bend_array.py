import os
import copy
import json

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"  # Prevent .pyc file creation

import gdsfactory as gf

from bend import create_gc_u_turn_element, load_bend_params


# gdsfactory 9.x requires an active PDK before geometry/layer creation.
try:
    gf.get_active_pdk()
except Exception:
    try:
        gf.gpdk.PDK.activate()
    except Exception:
        from gdsfactory.generic_tech import get_generic_pdk

        get_generic_pdk().activate()


def generate_lengths(start: int = 300, stop: int = 1800, step: int = 100) -> list[float]:
    """Generate inclusive approximate-length values."""
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


def add_waveguide_width_text(
    component: gf.Component,
    wg_width: float,
    text_layer: tuple[int, int],
    text_size: float = 20.0,
    offset_x: float = 25.0,
    offset_y: float = -25.0,
) -> None:
    """Add plain top-left text label with W-prefixed width."""
    width_nm = int(round(wg_width * 1000))
    label = component << gf.components.text(
        text=f"W{width_nm}",
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


def load_bend_array_params(json_path: str) -> dict:
    with open(json_path, "r") as f:
        return json.load(f)


def build_effective_bend_params(base_params: dict, array_params: dict) -> dict:
    """Merge bend defaults with array-level bend overrides."""
    effective = copy.deepcopy(base_params)
    overrides = array_params.get("bend_element", {})
    if not overrides:
        return effective

    for key in (
        "wg_width",
        "bend_radius",
        "ring_radius",
        "text_size",
        "taper_length",
        "grating_coupler_model",
    ):
        if key in overrides:
            effective[key] = overrides[key]

    if "layers" in overrides:
        layer_overrides = overrides["layers"]
        effective_layers = effective.setdefault("layers", {})
        for layer_key, layer_value in layer_overrides.items():
            effective_layers[layer_key] = layer_value

    return effective


def create_bend_array(base_params: dict, array_params: dict) -> gf.Component:
    """Create bend array from JSON-configured layout and spacing parameters."""
    effective_params = build_effective_bend_params(base_params, array_params)
    array_cfg = array_params.get("array", {})
    length_cfg = array_cfg.get("lengths", {})
    grid_cfg = array_cfg.get("grid", {})
    marker_cfg = array_cfg.get("alignment_marks", {})
    label_cfg = array_cfg.get("width_label", {})
    placement_cfg = array_cfg.get("placement", {})

    lengths = generate_lengths(
        int(length_cfg.get("start", 300)),
        int(length_cfg.get("stop", 1800)),
        int(length_cfg.get("step", 100)),
    )
    width_nm = int(round(float(effective_params["wg_width"]) * 1000))
    array_name = f"w{width_nm}"
    array = gf.Component(array_name)

    bend_layers = effective_params["layers"]
    array_layers = array_params.get("layers", {})
    grid_layer = tuple(array_layers.get("grid", [98, 0]))
    marker_layer = tuple(array_layers.get("marker", [95, 0]))
    label_text_layer = tuple(array_layers.get("text", bend_layers.get("text", [4, 0])))
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

    add_waveguide_width_text(
        component=array,
        wg_width=float(effective_params["wg_width"]),
        text_layer=label_text_layer,
        text_size=float(label_cfg.get("size", max(16.0, float(effective_params.get("text_size", 16.0))))),
        offset_x=float(label_cfg.get("offset_x", 25.0)),
        offset_y=float(label_cfg.get("offset_y", -25.0)),
    )

    start_x = float(placement_cfg.get("start_x", 180.0))
    start_y = float(placement_cfg.get("start_y", -220.0))
    local_y_spacing = float(array_cfg.get("y_spacing", 130.0))
    top_cell_prefix = str(array_cfg.get("top_cell_prefix", "L"))
    current_y = start_y

    for length in lengths:
        params = copy.deepcopy(effective_params)
        params["approximate_length"] = float(length)
        params["top_cell_name"] = f"{top_cell_prefix}{int(length)}"

        bend = create_gc_u_turn_element(
            wg_width=params["wg_width"],
            approximate_length=params["approximate_length"],
            bend_radius=params["bend_radius"],
            ring_radius=params["ring_radius"],
            layers={
                "waveguide": tuple(bend_layers["waveguide"]),
                "ring": tuple(bend_layers["ring"]),
                "text": tuple(bend_layers["text"]),
            },
            top_cell_name=params["top_cell_name"],
            text_size=params["text_size"],
            taper_length=params["taper_length"],
            grating_coupler_model=params["grating_coupler_model"],
        )

        ref = array << bend
        ref.move((start_x, current_y))
        current_y -= local_y_spacing

    return array


if __name__ == "__main__":
    bend_json_path = os.path.join(os.path.dirname(__file__), "..", "Json", "bend.json")
    array_json_path = os.path.join(os.path.dirname(__file__), "..", "Json", "bend_array.json")
    bend_params = load_bend_params(bend_json_path)
    bend_array_params = load_bend_array_params(array_json_path)

    bend_array = create_bend_array(bend_params, bend_array_params)

    output_name = bend_array_params.get("array", {}).get("output_name", "bend_array.gds")
    output_path = os.path.join(os.path.dirname(__file__), "..", "build", "gds", output_name)
    bend_array.write_gds(output_path)
    print(f"Bend array GDS written to: {output_path}")
    bend_array.show()
