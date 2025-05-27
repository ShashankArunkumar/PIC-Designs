import gdsfactory as gf
import json
import os
import copy

def build_component_from_params(params):
    r = params["geometry"]["r"]
    L = params["geometry"]["L"]
    D = params["geometry"]["D"]
    x = params["geometry"]["x"]
    s = params["geometry"]["s"]
    width = params["geometry"]["width"]
    layer = tuple(params["layers"]["waveguide"])
    text_layer = tuple(params["layers"]["text"])
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
        for i in range(10):
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
        for i in range(10):
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
    final_comp._path_metrics = {'length': path_length, 'x_diff': x_diff}
    
    # ...existing grating coupler and component assembly code...
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
spacing = params["array"]["spacing"]  # micron spacing between devices from JSON
components_with_metrics = []

for i, r in enumerate(r_values):
    # Each ROC element as a cell
    local_params = copy.deepcopy(params)
    local_params["geometry"]["r"] = r
    cell = build_component_from_params(local_params)
    ref = array_comp.add_ref(cell)
    ref.move((0, i * spacing))
    
    # Collect path metrics for uniformity check
    components_with_metrics.append(cell)

# Show or export the array
if __name__ == "__main__":
    # Check that path lengths and x_diff values are different for different r values
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
    
    array_comp.show()
