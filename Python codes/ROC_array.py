import gdsfactory as gf
import json
import os
import copy

def add_die_box_with_grid(component, die_name=None, params=None):
    """Add a die box with 500µm grid around the component"""
    if params is None:
        return component
        
    die_box_params = params.get("die_box", {})
    die_text_params = params.get("die_text", {})
    e_beam_marker_params = params.get("e_beam_marker", {})
    layers = params.get("layers", {})
    
    grid_size = die_box_params.get("grid_size", 500.0)
    die_layer = tuple(layers.get("die_box", [99, 0]))
    grid_layer = tuple(layers.get("die_grid", [98, 0]))
    tag_layer = tuple(layers.get("die_text", [3, 0]))
    marker_layer = tuple(layers.get("e_beam_marker", [95, 0]))    # Determine the original component name (ROC_array specific: w{width})
    width = params["geometry"]["width"]
    width_nm = int(width * 1000)
    original_die_name = f"w{width_nm}"
    
    # Handle die name conflicts - if die_name is provided and different from original, show both
    if die_name is None:
        # Use original name
        final_die_name = original_die_name
    elif isinstance(die_name, int):
        # Placement system provided a die number - show both names
        placement_name = f"Die {die_name}"
        final_die_name = f"{original_die_name} / {placement_name}"
    elif die_name != original_die_name:
        # Different name provided - show both
        final_die_name = f"{original_die_name} / {die_name}"
    else:
        # Same name - use it
        final_die_name = die_name
        marker_size = e_beam_marker_params.get("size", 8.0)
        marker_offset = e_beam_marker_params.get("offset", 45.0)
    
    bbox = component.bbox()
    xmin, ymin, xmax, ymax = bbox.left, bbox.bottom, bbox.right, bbox.top
    width = xmax - xmin
    height = ymax - ymin
    die_width = ((int((width // grid_size) + 1) if width % grid_size != 0 else int(width // grid_size)) + 1) * grid_size
    die_height = ((int((height // grid_size) + 1) if height % grid_size != 0 else int(height // grid_size)) + 1) * grid_size
    n_x = int(die_width // grid_size)
    n_y = int(die_height // grid_size)
    grid_line_width = die_box_params.get("grid_line_width", 0.002)    # Get displacement values to position array within the grid
    displacement = params.get("array", {}).get("displacement", {"x": 0, "y": 0})
    displacement_x = displacement.get("x", 0)
    displacement_y = displacement.get("y", 0)
    
    # Center the die at (0,0): shift the component so its bbox center is at (0,0)
    comp_cx = (xmax + xmin) / 2
    comp_cy = (ymax + ymin) / 2
    component.move((-comp_cx, -comp_cy))
    
    # Apply displacement to position array within the grid (after centering)
    if displacement_x != 0 or displacement_y != 0:
        component.move((displacement_x, displacement_y))
    
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
    
    e_beam_markers = gf.Component("E_beam_markers")
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
    text = gf.components.text(text=final_die_name, size=die_text_params.get("text_size", 50), layer=tag_layer)
    text_ref = tag.add_ref(text)
    text_ref.move((die_text_params.get("offset_x", 150), die_height - die_text_params.get("offset_y", 150)))
    tag_ref = component.add_ref(tag)
    tag_ref.move((die_xmin, die_ymin))
    
    return component

def build_component_from_params(params):
    r = params["geometry"]["r"]
    L = params["geometry"]["L"]
    D = params["geometry"]["D"]
    x = params["geometry"]["x"]
    s = params["geometry"]["s"]
    width = params["geometry"]["width"]
    layer = tuple(params["layers"]["waveguide"])
    # Use device text layer from text section if specified, otherwise fall back to global text layer
    text_layer = tuple(params["text"].get("layer", params["layers"]["text"]))
    text_size = params["text"]["size"]
    text_offset_left = params["text"]["offset_left"]
    text_offset_right = params["text"]["offset_right"]
    taper_length = params["taper"]["length"]
    enable_text = params["text"]["enable"]
    grating_coupler_config = params["grating_coupler"]
    
    cross_section = gf.cross_section.strip(width=width, layer=layer)
    bend_180 = gf.path.euler(radius=s, angle=180)
    H = bend_180.length()
    I = bend_180.points[-1][1] - bend_180.points[0][1]
    
    if r > 0:
        # Create Q path with 10 S-bend units (40 total bends)
        # Each S-bend unit: -90, +90, +90, -90 (returns to same y, advances in x)
        Q = gf.Path()
        for i in range(12):
            Q += gf.path.euler(radius=r, angle=-90)
            Q += gf.path.euler(radius=r, angle=90)
            Q += gf.path.euler(radius=r, angle=90)
            Q += gf.path.euler(radius=r, angle=-90)
        
        J = Q.length()
        K = Q.points[-1][0] - Q.points[0][0]
    else:
        J = 0
        K = 0

    # Constraint Equations
    u = (D - K - 2*x)/2
    a = (L - 2*x - 4*H - J - 2*u) / 4

    # Path construction 
    P = gf.Path()
    P += gf.path.straight(length=x)
    P += gf.path.straight(length=a)
    P += gf.path.euler(radius=s, angle=-180)
    P += gf.path.straight(length=a)
    P += gf.path.euler(radius=s, angle=180)
    P += gf.path.straight(length=u)
    if r == 0:
        bends_x = K
        P += gf.path.straight(length=bends_x)
    else:
        for i in range(12):
            P += gf.path.euler(radius=r, angle=-90)
            P += gf.path.euler(radius=r, angle=90)
            P += gf.path.euler(radius=r, angle=90)
            P += gf.path.euler(radius=r, angle=-90)
    
    P += gf.path.straight(length=u)
    P += gf.path.euler(radius=s, angle=180)
    P += gf.path.straight(length=a)
    P += gf.path.euler(radius=s, angle=-180)
    P += gf.path.straight(length=a)
    P += gf.path.straight(length=x)

    cell_name = f"w{int(width*1000)}r{r}"
    final_comp = gf.Component(cell_name)
    wg = gf.path.extrude(P, cross_section=cross_section)
    wg_ref = final_comp << wg
    
    # Store path metrics for uniformity checking
    path_length = P.length()
    x_diff = P.points[-1][0] - P.points[0][0]
    final_comp._path_metrics = {'length': path_length, 'x_diff': x_diff}    # ...existing grating coupler and component assembly code...
    wg_ref = final_comp << wg
    grating_n_periods = grating_coupler_config["n_periods"]
    grating_period = grating_coupler_config["period"]
    grating_fill_factor = grating_coupler_config["fill_factor"]
    grating_taper_length_gc = grating_coupler_config["taper_length"]
    grating_taper_angle_gc = grating_coupler_config["taper_angle"]
    grating_wavelength_gc = grating_coupler_config["wavelength"]
    grating_fiber_angle_gc = grating_coupler_config["fiber_angle"]
    grating_polarization_gc = grating_coupler_config["polarization"]
    gc_width = grating_coupler_config.get("width", 0.5)
    gc_xs = gf.cross_section.strip(width=gc_width, layer=layer)
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
        width2=width,
        layer=layer,
    )
    taper_left = final_comp << taper
    gc_left = final_comp << gc
    taper_left.connect("o2", wg_ref.ports["o1"])
    gc_left.connect("o1", taper_left.ports["o1"])
    if enable_text:
        text_left = final_comp << gf.components.text(
            text=f"w{int(width*1000)}r{r}",
            size=text_size,
            layer=text_layer
        )
        text_left.move(origin=text_left.center, destination=(gc_left.ports["o1"].center[0] + text_offset_left, gc_left.ports["o1"].center[1]))
    taper_right = final_comp << taper
    gc_right = final_comp << gc
    taper_right.connect("o2", wg_ref.ports["o2"])
    gc_right.connect("o1", taper_right.ports["o1"])
    if enable_text:        
        text_right = final_comp << gf.components.text(
            text=f"w{int(width*1000)}r{r}",
            size=text_size,
            layer=text_layer
        )
        text_right.move(origin=text_right.center, destination=(gc_right.ports["o1"].center[0] + text_offset_right, gc_right.ports["o1"].center[1]))
      # Center the component at its bounding box center (set origin to bbox center)
    bbox = final_comp.bbox()
    center_x = (bbox.right + bbox.left) / 2
    center_y = (bbox.top + bbox.bottom) / 2
    final_comp.move((-center_x, -center_y))
    
    return final_comp

# Load parameters from JSON file
json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Json", "ROC_array.json")
with open(json_path, 'r') as f:
    config = json.load(f)
params = config["parameters"]

# Extract width for naming
width = params["geometry"]["width"]
width_nm = int(width * 1000)

# Range of r values from JSON
r_values = params["geometry"]["r_values"]

# Create the array component
array_comp = gf.Component(f"w{width_nm}")
spacing_config = params["array"]["spacing"]  # Can be single value or list
components_with_metrics = []

# Handle both single spacing value and list of spacing values
if isinstance(spacing_config, (int, float)):
    # Uniform spacing - use same spacing for all devices
    spacing_list = [spacing_config] * (len(r_values) - 1)
elif isinstance(spacing_config, list):
    # Custom spacing - use provided list
    spacing_list = spacing_config
    # If list is shorter than needed, repeat the last value
    while len(spacing_list) < len(r_values) - 1:
        spacing_list.append(spacing_list[-1])
    # If list is longer than needed, truncate it
    spacing_list = spacing_list[:len(r_values) - 1]
else:
    # Fallback to default spacing
    spacing_list = [200] * (len(r_values) - 1)

# Place devices with custom spacing
current_y_position = 0
for i, r in enumerate(r_values):
    # Each ROC element as a cell
    local_params = copy.deepcopy(params)
    local_params["geometry"]["r"] = r
    cell = build_component_from_params(local_params)
    ref = array_comp.add_ref(cell)
    ref.move((0, current_y_position))
    
    # Collect path metrics for uniformity check
    components_with_metrics.append(cell)
    
    # Update position for next device (except for the last device)
    if i < len(r_values) - 1:
        current_y_position += spacing_list[i]

def get_component():
    """Function for placement system compatibility - returns (component, die_name)"""
    # Return the array component and its width-based die name
    return array_comp, f"w{width_nm}"

def p_cascades():
    """Alternative function name for placement system compatibility - returns (component, die_name)"""
    return get_component()

# Show or export the array
if __name__ == "__main__":
    # Check that path lengths and x_diff values are uniform for different r values
    if len(components_with_metrics) > 1:
        first_metrics = components_with_metrics[0]._path_metrics
        first_length = first_metrics['length']
        first_x_diff = first_metrics['x_diff']
        
        # Check if lengths are correctly uniform (should be same for different r values)
        lengths_are_uniform = all(abs(comp._path_metrics['length'] - first_length) < 1e-10 
                                for comp in components_with_metrics)
        x_diffs_are_uniform = all(abs(comp._path_metrics['x_diff'] - first_x_diff) < 1e-10 
                                for comp in components_with_metrics)
        
        if lengths_are_uniform and x_diffs_are_uniform:
            print("Path length uniformity verified")
        else:
            print("Path length error")
            for i, comp in enumerate(components_with_metrics):
                metrics = comp._path_metrics
                print(f"  r={r_values[i]}: length={metrics['length']:.10f}, x_diff={metrics['x_diff']:.10f}")
    
    # Add grid box around the array with width-specific die name
    die_name = f"w{width_nm}"
    array_with_grid = add_die_box_with_grid(array_comp, die_name=die_name, params=params)
    
    array_with_grid.show()
