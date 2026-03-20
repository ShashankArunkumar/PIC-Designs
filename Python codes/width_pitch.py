import gdsfactory as gf
import json
import os
from grating_couplers import create_grating_coupler, get_gc_width

# gdsfactory 9.x requires an active PDK before geometry/layer creation.
try:
    gf.get_active_pdk()
except Exception:
    try:
        gf.gpdk.PDK.activate()
    except Exception:
        from gdsfactory.generic_tech import get_generic_pdk
        get_generic_pdk().activate()

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
    gc_model = wg_params.get("grating_coupler_model", "GC_1550_TE")
    gc_width = get_gc_width(gc_model)
    wg_xs = gf.cross_section.strip(width=wg_width, layer=tuple(layers["waveguide"]))
    gc = create_grating_coupler(gc_model, layer=tuple(layers["waveguide"]))
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
    
    # Check if markers and text are enabled (default to True if not specified)
    enable_markers = params["device_marker"].get("enable_markers", True)
    enable_text = params["device_text"].get("enable_text", True)
    
    # Create marker and text positions for reference (needed even if markers are disabled but text is enabled)
    left_marker_pos = (gc1_ref.ports["o2"].center[0] - marker_offset - marker_size, gc1_ref.ports["o2"].center[1] - marker_size / 2)
    right_marker_pos = (gc2_ref.ports["o2"].center[0] + marker_offset, gc2_ref.ports["o2"].center[1] - marker_size / 2)
    
    # Add markers if enabled
    left_marker_ref = None
    right_marker_ref = None
    if enable_markers:
        # Left marker (input side)
        left_marker = gf.components.rectangle(size=(marker_size, marker_size), layer=tuple(layers["marker"]))
        left_marker_ref = c.add_ref(left_marker)
        left_marker_ref.move(left_marker_pos)
        
        # Right marker (output side)
        right_marker = gf.components.rectangle(size=(marker_size, marker_size), layer=tuple(layers["marker"]))
        right_marker_ref = c.add_ref(right_marker)
        right_marker_ref.move(right_marker_pos)
    
    # Add text if enabled
    if enable_text:
        # Left text
        left_text = gf.components.text(
            text=f"w{int(wg_width*1000)} p{int(grating_period*1000)}",
            size=marker_size,
            layer=tuple(layers["die_text"]),
        )
        left_text_ref = c.add_ref(left_text)
        # If markers exist, position relative to them, otherwise use calculated positions
        if left_marker_ref:
            left_text_ref.move((left_marker_ref.xmin - left_text.size_info.width - text_offset_x, left_marker_ref.ymin + text_offset_y))
        else:
            left_text_ref.move((left_marker_pos[0] - left_text.size_info.width - text_offset_x, left_marker_pos[1] + text_offset_y))
        
        # Right text
        right_text = gf.components.text(
            text=f"w{int(wg_width*1000)} p{int(grating_period*1000)}",
            size=marker_size,
            layer=tuple(layers["die_text"]),
        )
        right_text_ref = c.add_ref(right_text)
        # If markers exist, position relative to them, otherwise use calculated positions
        if right_marker_ref:
            right_text_ref.move((right_marker_ref.xmax + text_offset_x, right_marker_ref.ymin + text_offset_y))
        else:
            right_text_ref.move((right_marker_pos[0] + marker_size + text_offset_x, right_marker_pos[1] + text_offset_y))
    
    return c

def p_cascades():
    y_spacing = p_cascades_params["y_spacing"]
    x_offset = p_cascades_params["x_offset"]
    cascade_spacing = p_cascades_params["cascade_spacing"]
    x0 = p_cascades_params["x0"]
    y0 = p_cascades_params["y0"]
      # Create the top-level component
    c = gf.Component("wp_cascades")
    
    # Create an intermediate "cascades" component to contain all individual cascades
    cascades_component = gf.Component("cascades")
    
    # Create individual cascades and add them to the cascades component
    for j, period in enumerate(periods):
        cascade_name = f"{p_cascades_params['cascade_name_prefix']}{int(period*1000)}"
        cascade = gf.Component(cascade_name)
        for i, width in enumerate(widths):
            dev_name = f"w{int(width*1000)}p{int(period*1000)}"
            dev_cell = waveguide_with_grating_couplers(dev_name, width, period)
            dev_ref = cascade.add_ref(dev_cell)
            dev_ref.move((i * x_offset, -i * y_spacing))
            dev_ref.name = dev_name
        
        # Add each cascade to the intermediate cascades component
        cascade_ref = cascades_component.add_ref(cascade)
        cascade_ref.move((0, -j * cascade_spacing))  # Position cascades vertically within the group
        cascade_ref.name = cascade_name    # Add the cascades component to the top-level component
    cascades_ref = c.add_ref(cascades_component)
    cascades_ref.name = "cascades"
    
    print(f"Debug: Cascades positioned at origin")
    print(f"Debug: Component bbox: {c.bbox()}")
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
    grid_line_width = die_box_params.get("grid_line_width", 0.5)    # Center the die at (0,0): shift the component so its bbox center is at (0,0)
    comp_cx = (xmax + xmin) / 2
    comp_cy = (ymax + ymin) / 2
    component.move((-comp_cx, -comp_cy))
    # Now place die grid, markers, and tag relative to the new origin
    die_xmin = -die_width / 2
    die_ymin = -die_height / 2
    # Snap die_xmin and die_ymin to exact grid points to avoid floating point errors
    die_xmin = -round(die_width / 2 / grid_size) * grid_size
    die_ymin = -round(die_height / 2 / grid_size) * grid_size
    
    # Apply grid offset
    grid_offset_x = 50.0  # Move grid 50 microns to the right
    grid_offset_y = 0.0
    die_xmin += grid_offset_x
    die_ymin += grid_offset_y
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
    print(f"Debug: Before die box - Component bbox: {c.bbox()}")
    
    c = add_die_box_with_grid(c)
    print(f"Debug: After die box - Component bbox: {c.bbox()}")
    print(f"Debug: Grid has been moved 50 microns to the right")
    
    if output_params["show"]:
        c.show()
    
    # Export GDS file
    c.write_gds(output_params["gds_path"])
    print(f"GDS file saved to: {output_params['gds_path']}")