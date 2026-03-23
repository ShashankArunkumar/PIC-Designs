import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Prevent .pyc file creation

import gdsfactory as gf
from pathlib import Path
import kfactory.conf as kf_conf

# Route gdsfactory build artifacts to Setup/build.
for _parent in Path(__file__).resolve().parents:
    _setup_dir = _parent / "Setup"
    if _setup_dir.exists():
        kf_conf.config.__dict__["project_dir"] = _setup_dir
        breakimport matplotlib.pyplot as plt
import numpy as np
import json
from typing import Tuple
from grating_couplers import create_grating_coupler, get_gc_params, get_gc_width

# gdsfactory 9.x requires an active PDK before geometry/layer creation.
try:
    gf.get_active_pdk()
except Exception:
    try:
        gf.gpdk.PDK.activate()
    except Exception:
        from gdsfactory.generic_tech import get_generic_pdk
        get_generic_pdk().activate()

# Define global parameter
n = 0.7

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
grating_coupler_model = params.get("grating_coupler_model", "GC_1550_TE")
grating_coupler_config = get_gc_params(grating_coupler_model)

# Define the cross_section for extrusion and S-bend
cross_section = gf.cross_section.strip(width=width, layer=layer)

#param
bend_180 = gf.path.euler(radius=s, angle=180)
H = bend_180.length()

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

# Create the final path with calculated parameters
c = gf.Component("path_only")


# Define the starting position for the path
start_point = (0, 0)

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


if __name__ == "__main__":
    # Create the array of ROC devices
    n_values = [round(0.7 + i * 0.1, 1) for i in range(27)]  # Generate n values from 0.7 to 3.2 in steps of 0.1
    array_comp = gf.Component("roc_array")

    # Initialize taper and grating coupler for array creation
    gc = create_grating_coupler(grating_coupler_model, layer=layer)
    gc_width = get_gc_width(grating_coupler_model)

    taper = gf.components.taper(
        length=taper_length,
        width1=gc_width,
        width2=width,
        layer=layer,
    )

    # Load array spacing parameters
    array_spacing = params.get("array_spacing", {"x_diff": 50, "y_diff": 100})
    x_diff = array_spacing["x_diff"]
    y_diff = array_spacing["y_diff"]

    for index, n in enumerate(n_values):
        cell_name = f"{n}"
        cross_section = gf.cross_section.strip(width=width, layer=layer)
        final_comp = gf.Component(cell_name)
        wg = gf.path.extrude(P, cross_section=cross_section)
        wg_ref = final_comp << wg

        # Add grating couplers and tapers to both ends
        taper_left = final_comp << taper
        gc_left = final_comp << gc
        taper_left.connect("o2", wg_ref.ports["o1"])
        gc_left.connect("o1", taper_left.ports["o1"])

        taper_right = final_comp << taper
        gc_right = final_comp << gc
        taper_right.connect("o2", wg_ref.ports["o2"])
        gc_right.connect("o1", taper_right.ports["o1"])

        # Add text labels if enabled
        if enable_text:
            # Reverting back to using the number n instead of rectangles
            text_left = final_comp << gf.components.text(
                text=f"n{n}",
                size=text_size,
                layer=text_layer
            )
            text_left.move(origin=text_left.center, destination=(gc_left.ports["o1"].center[0] + text_offset_left / 2, gc_left.ports["o1"].center[1]))

            text_right = final_comp << gf.components.text(
                text=f"{n}",
                size=text_size,
                layer=text_layer
            )
            text_right.move(origin=text_right.center, destination=(gc_right.ports["o1"].center[0] + text_offset_right / 2, gc_right.ports["o1"].center[1]))

        # Place the device in the array column by column
        column_index = index % 3  # Determine the column index
        row_index = index // 3  # Determine the row based on index
        array_comp.add_ref(final_comp).move((column_index * x_diff, -row_index * y_diff))  # Use x_diff and y_diff for spacing

    array_comp.show()

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
    grating_coupler_model = params.get("grating_coupler_model", "GC_1550_TE")
    grating_coupler_config = get_gc_params(grating_coupler_model)

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
    cell_name = f"{n}"
    final_comp = gf.Component(cell_name)
    wg = gf.path.extrude(P, cross_section=cross_section)
    wg_ref = final_comp << wg
    gc = create_grating_coupler(grating_coupler_model, layer=layer)
    gc_width = get_gc_width(grating_coupler_model)
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
            text=f"n{n}",
            size=text_size,
            layer=text_layer
        )
        text_left.move(origin=text_left.center, destination=(gc_left.ports["o1"].center[0] + text_offset_left / 2, gc_left.ports["o1"].center[1]))
    # Right side
    taper_right = final_comp << taper
    gc_right = final_comp << gc
    taper_right.connect("o2", wg_ref.ports["o2"])
    gc_right.connect("o1", taper_right.ports["o1"])
    if enable_text:
        text_right = final_comp << gf.components.text(
            text=f"{n}",
            size=text_size,
            layer=text_layer
        )
        text_right.move(origin=text_right.center, destination=(gc_right.ports["o1"].center[0] + text_offset_right / 2, gc_right.ports["o1"].center[1]))
    return final_comp

def get_component():
    """
    Returns the main component (die) with the array of ROC devices for placement.
    """
    # Create the main die component
    main_component = gf.Component("ROC_Die")

    # Create the array of ROC devices
    n_values = [round(0.7 + i * 0.1, 1) for i in range(27)]  # Generate n values from 0.7 to 3.2 in steps of 0.1
    array_comp = gf.Component("roc_array")

    # Initialize taper and grating coupler for array creation
    gc = create_grating_coupler(grating_coupler_model, layer=layer)
    gc_width = get_gc_width(grating_coupler_model)

    taper = gf.components.taper(
        length=taper_length,
        width1=gc_width,
        width2=width,
        layer=layer,
    )

    # Load array spacing parameters
    array_spacing = params.get("array_spacing", {"x_diff": 50, "y_diff": 100})
    x_diff = array_spacing["x_diff"]
    y_diff = array_spacing["y_diff"]

    for index, n in enumerate(n_values):
        cell_name = f"n{n}"
        cross_section = gf.cross_section.strip(width=width, layer=layer)
        final_comp = gf.Component(cell_name)
        wg = gf.path.extrude(P, cross_section=cross_section)
        wg_ref = final_comp << wg

        # Add grating couplers and tapers to both ends
        taper_left = final_comp << taper
        gc_left = final_comp << gc
        taper_left.connect("o2", wg_ref.ports["o1"])
        gc_left.connect("o1", taper_left.ports["o1"])

        taper_right = final_comp << taper
        gc_right = final_comp << gc
        taper_right.connect("o2", wg_ref.ports["o2"])
        gc_right.connect("o1", taper_right.ports["o1"])

        # Add text labels if enabled
        if enable_text:
            # Reverting back to using the number n instead of rectangles
            text_left = final_comp << gf.components.text(
                text=f"n{n}",
                size=text_size,
                layer=text_layer
            )
            text_left.move(origin=text_left.center, destination=(gc_left.ports["o1"].center[0] + text_offset_left / 2, gc_left.ports["o1"].center[1]))

            text_right = final_comp << gf.components.text(
                text=f"{n}",
                size=text_size,
                layer=text_layer
            )
            text_right.move(origin=text_right.center, destination=(gc_right.ports["o1"].center[0] + text_offset_right / 2, gc_right.ports["o1"].center[1]))

        # Place the device in the array column by column
        column_index = index % 3  # Determine the column index
        row_index = index // 3  # Determine the row based on index
        array_comp.add_ref(final_comp).move((column_index * x_diff, -row_index * y_diff))  # Use x_diff and y_diff for spacing

    # Add the existing array_comp to the main component
    array_ref = main_component.add_ref(array_comp)

    # Return the die component and its name
    return main_component, "ROC_Die"
