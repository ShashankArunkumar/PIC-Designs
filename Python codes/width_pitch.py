import gdsfactory as gf
import json
import os

def generate_range(start, stop, step):
    n = int(round((stop - start) / step)) + 1
    return [round(start + i * step, 6) for i in range(n)]

# Load parameters from JSON
json_path = os.path.join(os.path.dirname(__file__), "..", "Json", "width_pitch.json")
with open(json_path, "r") as f:
    params = json.load(f)

layers = params["layers"]
wg_params = params["waveguide_with_grating_couplers"]
p_cascades_params = params["p_cascades"]
e_beam_marker_params = params["e_beam_marker"]
die_box_params = params["die_box"]
die_text_params = params["die_text"]
output_params = params["output"]
device_marker_params = params["device_marker"]
device_text_params = params["device_text"]

widths = generate_range(
    p_cascades_params["wg_width_start"],
    p_cascades_params["wg_width_stop"],
    p_cascades_params["wg_width_step"],
)
periods = generate_range(
    p_cascades_params["period_start"],
    p_cascades_params["period_stop"],
    p_cascades_params["period_step"],
)

def waveguide_with_grating_couplers(name, wg_width, grating_period):
    wg_length = wg_params["wg_length"]
    taper_length = wg_params["taper_length"]
    grating_n_periods = wg_params["grating_n_periods"]
    grating_fill_factor = wg_params["grating_fill_factor"]
    grating_taper_length_gc = wg_params["grating_taper_length_gc"]
    grating_taper_angle_gc = wg_params["grating_taper_angle_gc"]
    grating_wavelength_gc = wg_params["grating_wavelength_gc"]
    grating_fiber_angle_gc = wg_params["grating_fiber_angle_gc"]
    grating_polarization_gc = wg_params["grating_polarization_gc"]
    gc_width = wg_params.get("grating_coupler_width", 0.5)  # Default to 0.5 if not specified
    wg_xs = gf.cross_section.strip(width=wg_width, layer=tuple(layers["waveguide"]))
    gc_xs = gf.cross_section.strip(width=gc_width, layer=tuple(layers["waveguide"]))
    gc = gf.components.grating_coupler_elliptical_uniform(
        n_periods=grating_n_periods,
        period=grating_period,
        fill_factor=grating_fill_factor,
        taper_length=grating_taper_length_gc,
        taper_angle=grating_taper_angle_gc,
        wavelength=grating_wavelength_gc,
        fiber_angle=grating_fiber_angle_gc,
        polarization=grating_polarization_gc,
        cross_section=gc_xs,
    )
    taper = gf.components.taper(
        length=taper_length,
        width1=gc_width,
        width2=wg_width,
        layer=tuple(layers["waveguide"]),
    )
    wg = gf.components.straight(length=wg_length, cross_section=wg_xs)
    c = gf.Component(name=f"w{int(wg_width*1000)}p{int(grating_period*1000)}")
    wg_ref = c.add_ref(wg)
    taper1_ref = c.add_ref(taper)
    gc1_ref = c.add_ref(gc)
    taper2_ref = c.add_ref(taper)
    gc2_ref = c.add_ref(gc)
    # Connect left side
    taper1_ref.connect("o2", wg_ref.ports["o1"])
    gc1_ref.connect("o1", taper1_ref.ports["o1"])
    # Connect right side
    taper2_ref.connect("o2", wg_ref.ports["o2"])
    gc2_ref.connect("o1", taper2_ref.ports["o1"])
    c.add_port("opt1", port=gc1_ref.ports["o2"])
    c.add_port("opt2", port=gc2_ref.ports["o2"])
    # Device marker and text parameters (left and right)
    marker_size = params["device_marker"]["size"]
    marker_offset = params["device_marker"]["offset"]
    text_offset_x = params["device_text"]["offset_x"]
    text_offset_y = params["device_text"]["offset_y"]
    # Left marker (input side)
    left_marker = gf.components.rectangle(size=(marker_size, marker_size), layer=tuple(layers["marker"]))
    left_marker_ref = c.add_ref(left_marker)
    left_marker_ref.move((gc1_ref.ports["o2"].center[0] - marker_offset - marker_size, gc1_ref.ports["o2"].center[1] - marker_size / 2))
    # Left text
    left_text = gf.components.text(
        text=f"w{int(wg_width*1000)} p{int(grating_period*1000)}",
        size=marker_size,
        layer=tuple(layers["die_text"]),
    )
    left_text_ref = c.add_ref(left_text)
    left_text_ref.move((left_marker_ref.xmin - left_text.size_info.width - text_offset_x, left_marker_ref.ymin + text_offset_y))
    # Right marker (output side)
    right_marker = gf.components.rectangle(size=(marker_size, marker_size), layer=tuple(layers["marker"]))
    right_marker_ref = c.add_ref(right_marker)
    right_marker_ref.move((gc2_ref.ports["o2"].center[0] + marker_offset, gc2_ref.ports["o2"].center[1] - marker_size / 2))
    # Right text
    right_text = gf.components.text(
        text=f"w{int(wg_width*1000)} p{int(grating_period*1000)}",
        size=marker_size,
        layer=tuple(layers["die_text"]),
    )
    right_text_ref = c.add_ref(right_text)
    right_text_ref.move((right_marker_ref.xmax + text_offset_x, right_marker_ref.ymin + text_offset_y))
    return c

def p_cascades():
    y_spacing = p_cascades_params["y_spacing"]
    x_offset = p_cascades_params["x_offset"]
    cascade_spacing = p_cascades_params["cascade_spacing"]
    x0 = p_cascades_params["x0"]
    y0 = p_cascades_params["y0"]
    c = gf.Component("wp_cascades")
    for j, period in enumerate(periods):
        cascade_name = f"{p_cascades_params['cascade_name_prefix']}{int(period*1000)}"
        cascade = gf.Component(cascade_name)
        for i, width in enumerate(widths):
            dev_name = f"w{int(width*1000)}p{int(period*1000)}"
            dev_cell = waveguide_with_grating_couplers(dev_name, width, period)
            dev_ref = cascade.add_ref(dev_cell)
            dev_ref.move((i * x_offset, -i * y_spacing))
            dev_ref.name = dev_name
        cascade_ref = c.add_ref(cascade)
        cascade_ref.move((x0, y0 - j * cascade_spacing))
        cascade_ref.name = cascade_name
    die_name = die_text_params["name_prefix"] + "1"
    return c, die_name

def add_die_box_with_grid(component, die_name=None):
    grid_size = die_box_params["grid_size"]
    die_layer = tuple(layers["die_box"])
    grid_layer = tuple(layers["die_grid"])
    tag_layer = tuple(layers["die_text"])
    marker_layer = tuple(layers["e_beam_marker"])
    # Allow die_name override, otherwise use default
    if die_name is None:
        die_name = die_text_params["name_prefix"] + "1"
    # If die_name is an integer, format as Die number (no brackets)
    if isinstance(die_name, int):
        die_name = f"Die {die_name}"
    marker_size = e_beam_marker_params["size"]
    marker_offset = e_beam_marker_params["offset"]
    bbox = component.bbox()
    xmin, ymin, xmax, ymax = bbox.left, bbox.bottom, bbox.right, bbox.top
    width = xmax - xmin
    height = ymax - ymin
    die_width = ((int((width // grid_size) + 1) if width % grid_size != 0 else int(width // grid_size)) + 1) * grid_size
    die_height = ((int((height // grid_size) + 1) if height % grid_size != 0 else int(height // grid_size)) + 1) * grid_size
    n_x = int(die_width // grid_size)
    n_y = int(die_height // grid_size)
    grid_line_width = die_box_params.get("grid_line_width", 0.5)
    # Center the die at (0,0): shift the component so its bbox center is at (0,0)
    comp_cx = (xmax + xmin) / 2
    comp_cy = (ymax + ymin) / 2
    component.move((-comp_cx, -comp_cy))
    # Now place die grid, markers, and tag relative to the new origin
    die_xmin = -die_width / 2
    die_ymin = -die_height / 2
    # Snap die_xmin and die_ymin to exact grid points to avoid floating point errors
    die_xmin = -round(die_width / 2 / grid_size) * grid_size
    die_ymin = -round(die_height / 2 / grid_size) * grid_size
    die_grid = gf.Component("Die_Grid")
    for i in range(n_x + 1):
        x = i * grid_size
        die_grid.add_ref(
            gf.components.rectangle(
                size=(grid_line_width, die_height), layer=grid_layer
            )
        ).move((x - grid_line_width / 2, 0))
    for j in range(n_y + 1):
        y = j * grid_size
        die_grid.add_ref(
            gf.components.rectangle(
                size=(die_width, grid_line_width), layer=grid_layer
            )
        ).move((0, y - grid_line_width / 2))
    die_grid_ref = component.add_ref(die_grid)
    die_grid_ref.move((die_xmin, die_ymin))
    e_beam_markers = gf.Component("E beam markers")
    for i in range(n_x + 1):
        for j in range(n_y + 1):
            x = i * grid_size
            y = j * grid_size
            marker1 = gf.components.rectangle(size=(marker_size, marker_size), layer=marker_layer)
            marker1_ref = e_beam_markers.add_ref(marker1)
            marker1_ref.move((x - marker_offset - marker_size, y + marker_offset))
            marker2 = gf.components.rectangle(size=(marker_size, marker_size), layer=marker_layer)
            marker2_ref = e_beam_markers.add_ref(marker2)
            marker2_ref.move((x + marker_offset, y + marker_offset))
            marker3 = gf.components.rectangle(size=(marker_size, marker_size), layer=marker_layer)
            marker3_ref = e_beam_markers.add_ref(marker3)
            marker3_ref.move((x - marker_offset - marker_size, y - marker_offset - marker_size))
            marker4 = gf.components.rectangle(size=(marker_size, marker_size), layer=marker_layer)
            marker4_ref = e_beam_markers.add_ref(marker4)
            marker4_ref.move((x + marker_offset, y - marker_offset - marker_size))
    e_beam_markers_ref = component.add_ref(e_beam_markers)
    e_beam_markers_ref.move((die_xmin, die_ymin))
    tag = gf.Component("Tag")
    text = gf.components.text(text=die_name, size=die_text_params["text_size"], layer=tag_layer)
    text_ref = tag.add_ref(text)
    text_ref.move((die_text_params["offset_x"], die_height - die_text_params["offset_y"]))
    tag_ref = component.add_ref(tag)
    tag_ref.move((die_xmin, die_ymin))
    return component

if __name__ == "__main__":
    c, die_name = p_cascades()
    c = add_die_box_with_grid(c)
    if output_params["show"]:
        c.show()
    c.write_gds(output_params["gds_path"])
    # Prevent OASIS file creation (do not call write_oas or set oas_path anywhere)
