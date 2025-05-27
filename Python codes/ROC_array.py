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
        Q = gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=-90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=90)
        Q += gf.path.euler(radius=r, angle=-90)
        
        J = Q.length()
        K = Q.points[-1][0] - Q.points[0][0]
    else:
        J = 0
        K = 0
    u = (D - K - 2*x)/2
    a = (L - 2*x - 4*H - J - 2*u) / 4

    # Path construction (do NOT use P.append(start_point))
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
        # Add the bends as in ROC.py
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=-90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=90)
        P += gf.path.euler(radius=r, angle=-90)
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
    # Shift the entire path by (-taper_length, 0) to set the origin as in ROC.py
    P = P.move(origin=(0, 0), destination=(-taper_length, 0))

    cell_name = f"w{int(width*1000)}r{r}"
    final_comp = gf.Component(cell_name)
    wg = gf.path.extrude(P, cross_section=cross_section)
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
for i, r in enumerate(r_values):
    # Each ROC element as a cell
    local_params = copy.deepcopy(params)
    local_params["geometry"]["r"] = r
    cell = build_component_from_params(local_params)
    ref = array_comp.add_ref(cell)
    ref.move((0, i * spacing))

# Show or export the array
if __name__ == "__main__":
    # For uniformity check, collect path lengths and x-coordinate differences
    # Use the already created cells to avoid duplicate cell names
    path_lengths = []
    x_diffs = []
    for i, r in enumerate(r_values):
        # Get parameters for this r value
        local_params = copy.deepcopy(params)
        local_params["geometry"]["r"] = r
        
        # Calculate path metrics without creating new components
        r_val = local_params["geometry"]["r"]
        L = local_params["geometry"]["L"]
        D = local_params["geometry"]["D"]
        x = local_params["geometry"]["x"]
        s = local_params["geometry"]["s"]
        width = local_params["geometry"]["width"]
        layer = tuple(local_params["layers"]["waveguide"])
        taper_length = local_params["taper"]["length"]
        cross_section = gf.cross_section.strip(width=width, layer=layer)
        bend_180 = gf.path.euler(radius=s, angle=180)
        H = bend_180.length()
        
        if r_val > 0:
            Q = gf.path.euler(radius=r_val, angle=-90)
            for _ in range(39):
                Q += gf.path.euler(radius=r_val, angle=90 if (_ % 2 == 0) else -90)
            J = Q.length()
            K = Q.points[-1][0] - Q.points[0][0]
        else:
            J = 0
            K = 0
        u = (D - K - 2*x)/2
        a = (L - 2*x - 4*H - J - 2*u) / 4
        
        P = gf.Path()
        P += gf.path.straight(length=x)
        P += gf.path.straight(length=a)
        P += gf.path.euler(radius=s, angle=-180)
        P += gf.path.straight(length=a)
        P += gf.path.euler(radius=s, angle=180)
        P += gf.path.straight(length=u)
        if r_val == 0:
            bends_x = K
            P += gf.path.straight(length=bends_x)
        else:
            for _ in range(40):
                P += gf.path.euler(radius=r_val, angle=-90 if (_ % 2 == 0) else 90)
            P += gf.path.straight(length=u)
            P += gf.path.euler(radius=s, angle=180)
            P += gf.path.straight(length=a)
            P += gf.path.euler(radius=s, angle=-180)
            P += gf.path.straight(length=a)
            P += gf.path.straight(length=x)
        P = P.move(origin=(0, 0), destination=(-taper_length, 0))
        total_length = P.length()
        
        # Create a temporary component for calculating final x coordinate
        temp_comp = gf.Component(f"temp_{r}")
        wg = gf.path.extrude(P, cross_section=cross_section)
        wg_ref = temp_comp << wg
        final_x = wg_ref.ports["o2"].center[0]
        x_diff = final_x - D
        path_lengths.append(total_length)
        x_diffs.append(x_diff)
    
    # Check uniformity
    if all(abs(l - path_lengths[0]) < 1e-6 for l in path_lengths) and all(abs(x - x_diffs[0]) < 1e-6 for x in x_diffs):
        print("Path length uniformity verified")
    else:
        print("Path length error")
    array_comp.show()
