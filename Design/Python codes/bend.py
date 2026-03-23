import os
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"  # Prevent .pyc file creation
import math
import hashlib
import json

import gdsfactory as gf
from pathlib import Path
import kfactory.conf as kf_conf

# Route gdsfactory build artifacts to Setup/build.
for _parent in Path(__file__).resolve().parents:
    _setup_dir = _parent / "Setup"
    if _setup_dir.exists():
        kf_conf.config.__dict__["project_dir"] = _setup_dir
        breakfrom grating_couplers import create_grating_coupler, get_gc_width

# gdsfactory 9.x requires an active PDK before geometry/layer creation.
try:
    gf.get_active_pdk()
except Exception:
    try:
        gf.gpdk.PDK.activate()
    except Exception:
        from gdsfactory.generic_tech import get_generic_pdk
        get_generic_pdk().activate()


def create_gc_u_turn_element(
    wg_width: float = 0.5,
    approximate_length: float = 106.7,
    bend_radius: float = 8.5,
    ring_radius: float = 10.0,
    layers: dict[str, tuple[int, int]] | None = None,
    top_cell_name: str = "Top",
    text_size: float = 30.0,
    taper_length: float = 20.0,
    grating_coupler_model: str = "GC_1550_TE",
) -> gf.Component:
    """Creates: grating coupler -> straight -> 180 bend -> straight -> grating coupler."""
    layers = layers or {
        "waveguide": (1, 0),
        "ring": (3, 0),
        "text": (4, 0),
    }
    waveguide_layer = tuple(layers["waveguide"])
    ring_layer = tuple(layers["ring"])
    text_layer = tuple(layers["text"])

    tag_seed = (
        f"{approximate_length:.3f}_{bend_radius:.3f}_{ring_radius:.3f}_"
        f"{wg_width:.3f}_{grating_coupler_model}"
    )
    cell_tag = hashlib.md5(tag_seed.encode("ascii")).hexdigest()[:6]
    bend_cell = gf.Component()

    # Derive straight length from the target total length.
    bend_path = gf.path.euler(radius=bend_radius, angle=180)
    bend_length = bend_path.length()
    if approximate_length < bend_length:
        raise ValueError(
            f"approximate_length must be >= bend_length ({bend_length:.2f} um)."
        )
    straight_length = 0.5 * (approximate_length - bend_length)

    wg_xs = gf.cross_section.strip(width=wg_width, layer=waveguide_layer)
    gc_width = get_gc_width(grating_coupler_model)
    gc = create_grating_coupler(grating_coupler_model, layer=waveguide_layer)
    s = gf.components.straight(length=straight_length, cross_section=wg_xs)
    # Build a 180-degree Euler bend and extrude it to a waveguide.
    bend_180 = bend_path.extrude(wg_xs)

    gc1 = bend_cell << gc
    s1 = bend_cell << s
    b = bend_cell << bend_180
    s2 = bend_cell << s
    gc2 = bend_cell << gc

    # Match the grating width to waveguide width when needed.
    if abs(gc_width - wg_width) > 1e-9:
        taper = gf.components.taper(
            length=taper_length,
            width1=gc_width,
            width2=wg_width,
            layer=waveguide_layer,
        )
        t1 = bend_cell << taper
        t2 = bend_cell << taper

        s1.connect("o1", b.ports["o1"])
        s2.connect("o1", b.ports["o2"])

        t1.connect("o2", s1.ports["o2"])
        gc1.connect("o1", t1.ports["o1"])

        t2.connect("o2", s2.ports["o2"])
        gc2.connect("o1", t2.ports["o1"])
    else:
        s1.connect("o1", b.ports["o1"])
        s2.connect("o1", b.ports["o2"])
        gc1.connect("o1", s1.ports["o2"])
        gc2.connect("o1", s2.ports["o2"])

    bend_cell.add_port("opt_in", port=gc1.ports["o2"])
    bend_cell.add_port("opt_out", port=gc2.ports["o2"])

    # Use auto-generated unique cell names to avoid collisions across mixed scripts.
    top = gf.Component()
    bend_ref = top << bend_cell
    bend_ref.move(origin=bend_ref.ports["opt_in"].center, destination=(0, 0))
    top.add_port("opt_in", port=bend_ref.ports["opt_in"])
    top.add_port("opt_out", port=bend_ref.ports["opt_out"])

    # Build ring in a unique helper cell.
    ring_cell = gf.Component()
    ring_width = max(wg_width, 0.2)
    outer_circle = gf.components.circle(radius=ring_radius, layer=ring_layer)
    inner_circle = gf.components.circle(radius=ring_radius - ring_width, layer=ring_layer)
    ring = gf.boolean(A=outer_circle, B=inner_circle, operation="A-B", layer=ring_layer)
    _ = ring_cell << ring
    ring_ref = top << ring_cell
    ring_ref.move(origin=(0, 0), destination=(0, 8.5))

    # Build text in a unique helper cell and place at (-25, 8.5).
    length_value = 2 * straight_length + bend_length
    length_label = int(round(length_value))
    text_cell = gf.Component()
    length_text = text_cell << gf.components.text(
        text=f"{length_label}",
        size=text_size,
        layer=text_layer,
    )
    length_text.move(origin=length_text.center, destination=(0, 0))
    text_ref = top << text_cell
    text_ref.move(origin=text_ref.center, destination=(-25.0, 8.5))

    return top


def load_bend_params(json_path: str) -> dict:
    with open(json_path, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    json_path = os.path.join(os.path.dirname(__file__), "..", "Json", "bend.json")
    params = load_bend_params(json_path)
    bend_component = create_gc_u_turn_element(
        wg_width=params["wg_width"],
        approximate_length=params["approximate_length"],
        bend_radius=params["bend_radius"],
        ring_radius=params["ring_radius"],
        layers={
            "waveguide": tuple(params["layers"]["waveguide"]),
            "ring": tuple(params["layers"]["ring"]),
            "text": tuple(params["layers"]["text"]),
        },
        top_cell_name=params["top_cell_name"],
        text_size=params["text_size"],
        taper_length=params["taper_length"],
        grating_coupler_model=params["grating_coupler_model"],
    )

    bend_component.show()

