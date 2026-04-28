import json
from pathlib import Path
import math

import gdsfactory as gf
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


def _load_bend_params() -> dict:
    json_path = Path(__file__).resolve().parents[2] / "Json" / "bend.json"
    if json_path.exists():
        with json_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    # sensible defaults
    return {
        "wg_width": 0.5,
        "bend_radius": 7.0,
        "ring_radius": 10.0,
    }


def create_L200_bend(layer: tuple[int, int]) -> gf.Component:
    """Create a 180-degree Euler bend assembly with total length ~400 um.

    The component omits any L{length} text so labels can be added externally.
    The geometry is extruded using the provided layer.
    """
    params = _load_bend_params()
    wg_width = params.get("wg_width", 0.5)
    bend_radius = params.get("bend_radius", 7.0)

    bend_path = gf.path.euler(radius=bend_radius, angle=180)
    bend_length = bend_path.length()
    target_length = 400.0
    if target_length < bend_length:
        straight_length = 0.0
    else:
        straight_length = 0.5 * (target_length - bend_length)

    xs = gf.cross_section.strip(width=wg_width, layer=layer)

    top = gf.Component()
    s = gf.components.straight(length=straight_length, cross_section=xs)
    bend = bend_path.extrude(xs)

    gc = None
    try:
        # try to load grating from project grating_couplers if available
        from grating_couplers import create_grating_coupler

        gc = create_grating_coupler(layer=layer, port_width=wg_width)
    except Exception:
        gc = None

    # assemble: gc - straight - bend - straight - gc (gc optional)
    if gc is not None:
        gc1 = top << gc
        s1 = top << s
        b = top << bend
        s2 = top << s
        gc2 = top << gc

        s1.connect("o1", b.ports["o1"])
        s2.connect("o1", b.ports["o2"])
        gc1.connect("o1", s1.ports["o2"])
        gc2.connect("o1", s2.ports["o2"])
        top.add_port("opt_in", port=gc1.ports["o2"])
        top.add_port("opt_out", port=gc2.ports["o2"])
    else:
        s1 = top << s
        b = top << bend
        s2 = top << s
        s1.connect("o1", b.ports["o1"])
        s2.connect("o1", b.ports["o2"])
        top.add_port("opt_in", port=s1.ports["o1"])
        top.add_port("opt_out", port=s2.ports["o2"])

    return top


def make_array(values: list[float], out_path: Path, y_spacing: float = 35.0, start_layer: int = 50) -> None:
    """Create an array of 10 bend elements (vertical), write to out_path.
    
    Origin is set to the top-left of the 500 µm enclosing box.
    Numbers are positioned to the left of the grating couplers.
    """
    # Use the output filename (without extension) as the unique component name
    unique_name = out_path.stem
    
    # First pass: build array to determine bbox and box position
    temp = gf.Component(f"{unique_name}_temp")
    refs_data = []  # Store (bend_ref, txt_ref, i, val) for later repositioning
    
    for i, val in enumerate(values):
        layer_num = start_layer + i
        bend_comp = create_L200_bend(layer=(layer_num, 0))
        ref = temp.add_ref(bend_comp)
        ref.move((0, -i * y_spacing))
        
        # Get bend bbox to position text to its left
        bend_bbox = bend_comp.bbox()
        if bend_bbox is not None:
            bend_x_min = bend_bbox.left
        else:
            bend_x_min = -100.0
        
        txt = gf.components.text(text=f"{val:.2f}", size=5.0, layer=(95, 0))
        txt_ref = temp.add_ref(txt)
        txt_ref.move((bend_x_min - 15.0, -i * y_spacing))  # Position to left of bend
        
        refs_data.append((ref, txt_ref, i, val))
    
    # Get current bbox to calculate box dimensions
    temp_bbox = temp.bbox()
    if temp_bbox is None:
        temp_bbox_left = -250
        temp_bbox_bottom = -250
        temp_bbox_right = 250
        temp_bbox_top = 250
    else:
        temp_bbox_left = temp_bbox.left
        temp_bbox_bottom = temp_bbox.bottom
        temp_bbox_right = temp_bbox.right
        temp_bbox_top = temp_bbox.top
    
    # Calculate 500 µm box with padding
    box_x_min = temp_bbox_left - 20
    box_y_min = temp_bbox_bottom - 20
    box_x_max = temp_bbox_right + 20
    box_y_max = temp_bbox_top + 20
    
    # Ensure box is at least 500 µm in both dimensions
    box_width = box_x_max - box_x_min
    box_height = box_y_max - box_y_min
    if box_width < 500:
        center_x = (box_x_min + box_x_max) / 2
        box_x_min = center_x - 250
        box_x_max = center_x + 250
    if box_height < 500:
        center_y = (box_y_min + box_y_max) / 2
        box_y_min = center_y - 250
        box_y_max = center_y + 250
    
    # Calculate offset to move box top-left to origin (0, 0)
    offset_x = -box_x_min
    offset_y = -box_y_max  # Top of box becomes y=0
    
    # Now create final component with offset
    top = gf.Component(unique_name)
    
    for ref, txt_ref, i, val in refs_data:
        # Get the position and apply offset
        bend_comp = create_L200_bend(layer=(start_layer + i, 0))
        bend_ref = top.add_ref(bend_comp)
        bend_ref.move((offset_x, offset_y - i * y_spacing))
        
        # Get bend bbox for text positioning
        bend_bbox = bend_comp.bbox()
        if bend_bbox is not None:
            bend_x_min = bend_bbox.left
        else:
            bend_x_min = -100.0
        
        txt = gf.components.text(text=f"{val:.2f}", size=5.0, layer=(95, 0))
        txt_ref = top.add_ref(txt)
        txt_ref.move((offset_x + bend_x_min - 20.0, (offset_y - i * y_spacing)+ 5.0))  # Position to left of bend, slightly above center of text
    
    # Add 500 µm enclosing box
    box = gf.components.rectangle(
        size=(500.0, 500.0),
        layer=(99, 0)
    )
    box_ref = top.add_ref(box)
    box_ref.move((offset_x + box_x_min, offset_y + box_y_min))
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    top.write_gds(out_path)
    print(f"Wrote: {out_path}")
    top.show()


def _frange(start: float) -> list[float]:
    # produce 10 values with 0.05 step
    return [round(start + 0.05 * i, 3) for i in range(10)]


def main() -> None:
    project_dir = _configure_project_dir()
    out_dir = project_dir / "build" / "gds"
    out_dir.mkdir(parents=True, exist_ok=True)

    arrays = [
        (_frange(1.20), out_dir / "dosetest_array1.gds", 50),
        (_frange(1.70), out_dir / "dosetest_array2.gds", 60),
        (_frange(2.20), out_dir / "dosetest_array3.gds", 70),
        (_frange(2.70), out_dir / "dosetest_array4.gds", 80),
    ]

    # make sure PDK active
    try:
        gf.get_active_pdk()
    except Exception:
        try:
            gf.gpdk.PDK.activate()
        except Exception:
            from gdsfactory.generic_tech import get_generic_pdk

            get_generic_pdk().activate()

    for vals, path, start_layer in arrays:
        make_array(vals, path, y_spacing=35.0, start_layer=start_layer)


if __name__ == "__main__":
    main()
