import gdsfactory as gf
import matplotlib.pyplot as plt
import numpy as np
import json
import os
from typing import Tuple

# Load parameters from JSON file
json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Json", "ROC.json")
with open(json_path, 'r') as f:
    config = json.load(f)

params = config["parameters"]

# Parameters
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

# Define the cross_section for extrusion and S-bend
cross_section = gf.cross_section.strip(width=width, layer=layer)

#param
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
# constraint equations
u = (D - K - 2*x)/2
a = (L - 2*x - 4*H - J - 2*u) / 4
# Create the final path with calculated parameters
c = gf.Component("path_only")


# Define the starting position for the path
start_point = (-taper_length, 0)

# Create path starting from this point
P = gf.Path()
P += gf.path.straight(length=x)
P += gf.path.straight(length=a)
P += gf.path.euler(radius=s, angle=-180)
P += gf.path.straight(length=a)
P += gf.path.euler(radius=s, angle=180)
P += gf.path.straight(length=u)

# Add bends or straight depending on r
if r == 0:
    # Replace all Euler bends with a single straight of equivalent total x displacement
    # Calculate total x displacement of the bends section (when r>0)
    bends_x = K  # K is the x displacement of the Q path
    P += gf.path.straight(length=bends_x)
else:
    # Add the bends as usual
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


if __name__ == "__main__":
    # === ROC Element ===
    cell_name = f"w{int(width*1000)}r{r}"
    cross_section = gf.cross_section.strip(width=width, layer=layer)
    final_comp = gf.Component(cell_name)
    wg = gf.path.extrude(P, cross_section=cross_section)
    wg_ref = final_comp << wg    # Add grating couplers and tapers to both ends
    # Create grating coupler with parameters from JSON (following width_pitch.py approach)
    grating_n_periods = grating_coupler_config["n_periods"]
    grating_period = grating_coupler_config["period"]
    grating_fill_factor = grating_coupler_config["fill_factor"]
    grating_taper_length_gc = grating_coupler_config["taper_length"]
    grating_taper_angle_gc = grating_coupler_config["taper_angle"]
    grating_wavelength_gc = grating_coupler_config["wavelength"]
    grating_fiber_angle_gc = grating_coupler_config["fiber_angle"]
    grating_polarization_gc = grating_coupler_config["polarization"]
    gc_width = grating_coupler_config.get("width", 0.5)  # Default to 0.5 if not specified
    
    # Create cross sections
    wg_xs = gf.cross_section.strip(width=width, layer=layer)
    gc_xs = gf.cross_section.strip(width=gc_width, layer=layer)
    
    if grating_coupler_config["type"] == "grating_coupler_elliptical_uniform":
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
    else:
        gc = gf.components.grating_coupler_elliptical_uniform()  # fallback
    
    taper = gf.components.taper(
        length=taper_length,
        width1=gc_width,
        width2=width,
        layer=layer,
    )

    # Left side
    taper_left = final_comp << taper
    gc_left = final_comp << gc
    taper_left.connect("o2", wg_ref.ports["o1"])
    gc_left.connect("o1", taper_left.ports["o1"])
    
    # Add text labels if enabled
    if enable_text:
        # Add text 100 microns to the left of the left grating coupler
        text_left = final_comp << gf.components.text(
            text=f"w{int(width*1000)}r{r}",
            size=text_size,
            layer=text_layer
        )
        text_left.move(origin=text_left.center, destination=(gc_left.ports["o1"].center[0] + text_offset_left, gc_left.ports["o1"].center[1]))

    # Right side
    taper_right = final_comp << taper
    gc_right = final_comp << gc
    taper_right.connect("o2", wg_ref.ports["o2"])
    gc_right.connect("o1", taper_right.ports["o1"])
    
    # Add text labels if enabled
    if enable_text:
        # Add text to the right of the right grating coupler
        text_right = final_comp << gf.components.text(
            text=f"w{int(width*1000)}r{r}",
            size=text_size,
            layer=text_layer
        )
        text_right.move(origin=text_right.center, destination=(gc_right.ports["o1"].center[0] + text_offset_right, gc_right.ports["o1"].center[1]))

    final_coordinate_after_end = wg_ref.ports["o2"].center
    total_length = P.length()
    print(f"\n=== FINAL PATH RESULTS ===")
    print(f"  Target total length (L): {L} µm")
    print(f"  Actual total length: {total_length:.2f} µm")
    print(f"  Length difference: {total_length - L:.2f} µm")    
    print(f"  Target D coordinate: {D}")
    print(f"  Actual final x-coordinate: {final_coordinate_after_end[0]:.2f}")
    print(f"  X-coordinate difference: {final_coordinate_after_end[0] - D:.2f}")
    print(f"  Final y-coordinate: {final_coordinate_after_end[1]:.2f}")
    final_comp.show()

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
        for _ in range(39):
            Q += gf.path.euler(radius=r, angle=90 if (_ % 2 == 0) else -90)
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
    if r == 0:
        bends_x = K
        P += gf.path.straight(length=bends_x)
    else:
        for _ in range(40):
            P += gf.path.euler(radius=r, angle=-90 if (_ % 2 == 0) else 90)
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
    # Grating coupler params
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
    # Left side
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
    # Right side
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