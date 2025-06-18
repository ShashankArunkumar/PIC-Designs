import numpy as np
import gdsfactory as gf

# Check the gdsfactory version
print(f"Using gdsfactory version: {gf.__version__}")

#TODO:
# Euler 
# Straight to transition

# Default parameters
distance_bw_couplers = 3300  
length_of_the_coupler = 165
bend_radius = 20
ebm_field_size = 200
waveguide_width = 0.556
total_waveguide_length = 10000

# Create a spiral waveguide component with grating couplers
def create_spiral_with_couplers(
    distance_bw_couplers=3300,
    length_of_the_coupler=165,
    bend_radius=20,
    ebm_field_size=200,
    waveguide_width=0.556,
    total_waveguide_length=10000,
    layer=(1, 0)
) -> gf.Component:
    """
    Create a spiral waveguide component with grating couplers.
    
    Args:
        distance_bw_couplers (float): Distance between couplers (default: 3300)
        length_of_the_coupler (float): Length of the coupler (default: 165)
        bend_radius (float): Bend radius (default: 20)
        ebm_field_size (float): EBM field size (default: 200)
        waveguide_width (float): Width of the waveguide (default: 0.556)
        total_waveguide_length (float): Total length of the waveguide (default: 10000)
        layer (tuple): Layer specification (default: (1, 0))
        
    Returns:
        Component: A gdsfactory component containing the spiral with grating couplers
    """
    # Parameter calculations
    r = bend_radius
    d = distance_bw_couplers
    g = length_of_the_coupler
    f = ebm_field_size
    k = total_waveguide_length
    w = waveguide_width
    
    # Create the component first so we can add ports
    c = gf.Component(f"spiral_element_r{r:.1f}_w{w:.3f}")
    
    # Distance and displacement equations
    s = 0.1 * f
    m = 0.09 * f
    a = f - g
    n = ((k - d - s - 10 * (np.pi) * r + (2 * g) - 40 * m) / (8 * s)) + 37 / 8
    b = d - (a + s + ((n + 3) * s) + 2 * g)
    
    # Define the cross-section for extrusion
    cs = gf.cross_section.strip(width=w, layer=layer)
    
    P = gf.Path()
    
    # Define the starting position for the path
    start_point = (-(a+10*s), 6*m)
    
    # Initialize the path at the start point
    P = gf.path.straight(length=0.01)  # Create minimal path to start
    P.move(origin=(0,0), destination=start_point)
    
    P += gf.path.straight(length=a)
    P += gf.path.straight(length=s)    
    P += gf.path.straight(length=n*s)  
    P += gf.path.arc(radius=r, angle=-90) 
    P += gf.path.straight(length=7*m)  
    P += gf.path.arc(radius=r, angle=-90) 
    P += gf.path.straight(length=(n-2)*s)  
    P += gf.path.arc(radius=r, angle=-90)
    P += gf.path.straight(length=5*m)  
    P += gf.path.arc(radius=r, angle=-90) 
    P += gf.path.straight(length=(n-4)*s)  
    P += gf.path.arc(radius=r, angle=-90) 
    P += gf.path.straight(length=3*m)  
    P += gf.path.arc(radius=r, angle=-90) 
    P += gf.path.straight(length=(n-6)*s)  
    P += gf.path.arc(radius=r, angle=-90)
    P += gf.path.straight(length=m)  
    P += gf.path.arc(radius=r, angle=-90) 
    P += gf.path.straight(length=2*s)  
    P += gf.path.arc(radius=r, angle=-90)
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=(n-11)*s) 
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=m)  
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=(n-6)*s)
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=3*m)  
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=(n-4)*s)
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=5*m)  
    P += gf.path.arc(radius=r, angle=90) 
    P += gf.path.straight(length=(n-2)*s)
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=7*m)  
    P += gf.path.arc(radius=r, angle=90)  
    P += gf.path.straight(length=(n)*s)
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=8*m)  
    P += gf.path.arc(radius=r, angle=-90)
    P += gf.path.straight(length=b)
    
    # Get the final position of the path
    end_point = P.points[-1]
    
    # Add ports to the component
    c.add_port(name="o1", center=start_point, width=w, orientation=180, layer=layer)
    c.add_port(name="o2", center=end_point, width=w, orientation=0, layer=layer)
    
    # Extrude the path with the defined cross-section
    wg = gf.path.extrude(P, cross_section=cs)
    
    # Add the extruded waveguide to the component
    wg_ref = c << wg
    
    # Add grating couplers to the component
    try:
        # Create a grating coupler
        try:
            # First attempt with elliptical uniform grating coupler
            gc = gf.components.grating_coupler_elliptical_uniform(
                width_waveguide=w,
                polarization="te",
                wavelength=1.55,
                fiber_angle=15,
                layer=layer
            )
            print("Using elliptical uniform grating coupler")
        except Exception:
            # Fallback to a simpler grating coupler if the elliptical one fails
            print("Elliptical grating coupler failed, trying simpler grating coupler")
            gc = gf.components.grating_coupler_te(
                layer=layer,
                width=w
            )
        
        # Input grating coupler (left/west)
        gc_in = c << gc
        gc_in.rotate(180)  # Rotate to face left (input side)
        gc_in.move(origin=gc_in.ports["o1"].center, destination=start_point)
        
        # Output grating coupler (right/east)
        gc_out = c << gc
        gc_out.move(origin=gc_out.ports["o1"].center, destination=end_point)
        
        # Add references to the grating couplers in the component
        c.add_ref(gc_in, name="gc_in")
        c.add_ref(gc_out, name="gc_out")
        
        # Add new ports at the grating coupler fiber interfaces
        if "o2" in gc_in.ports:
            c.add_port("optical_in", port=gc_in.ports["o2"])
        
        if "o2" in gc_out.ports:
            c.add_port("optical_out", port=gc_out.ports["o2"])
            
        c.info["has_grating_couplers"] = True
        print("Added grating couplers successfully")
    except Exception as e:
        print(f"Warning: Could not add grating couplers: {e}")
        c.info["has_grating_couplers"] = False
    
    return c

def create_spiral_with_couplers(
    distance_bw_couplers=3300,
    length_of_the_coupler=165,
    bend_radius=20,
    ebm_field_size=200,
    waveguide_width=0.556,
    total_waveguide_length=10000,
    layer=(1, 0)
) -> gf.Component:
    """
    Create a spiral waveguide component with grating couplers.
    
    Args:
        distance_bw_couplers (float): Distance between couplers (default: 3300)
        length_of_the_coupler (float): Length of the coupler (default: 165)
        bend_radius (float): Bend radius (default: 20)
        ebm_field_size (float): EBM field size (default: 200)
        waveguide_width (float): Width of the waveguide (default: 0.556)
        total_waveguide_length (float): Total length of the waveguide (default: 10000)
        layer (tuple): Layer specification (default: (1, 0))
        
    Returns:
        Component: A gdsfactory component containing the spiral with grating couplers
    """
    # Parameter calculations
    r = bend_radius
    d = distance_bw_couplers
    g = length_of_the_coupler
    f = ebm_field_size
    k = total_waveguide_length
    w = waveguide_width
    
    # Create the component first so we can add ports
    c = gf.Component(f"spiral_element_r{r:.1f}_w{w:.3f}")
    
    # Distance and displacement equations
    s = 0.1 * f
    m = 0.09 * f
    a = f - g
    n = ((k - d - s - 10 * (np.pi) * r + (2 * g) - 40 * m) / (8 * s)) + 37 / 8
    b = d - (a + s + ((n + 3) * s) + 2 * g)
    
    # Define the cross-section for extrusion
    cs = gf.cross_section.strip(width=w, layer=layer)
    
    P = gf.Path()
    
    # Define the starting position for the path
    start_point = (-(a+10*s), 6*m)
    
    # Initialize the path at the start point
    P = gf.path.straight(length=0.01)  # Create minimal path to start
    P.move(origin=(0,0), destination=start_point)
    
    P += gf.path.straight(length=a)
    P += gf.path.straight(length=s)    
    P += gf.path.straight(length=n*s)  
    P += gf.path.arc(radius=r, angle=-90) 
    P += gf.path.straight(length=7*m)  
    P += gf.path.arc(radius=r, angle=-90) 
    P += gf.path.straight(length=(n-2)*s)  
    P += gf.path.arc(radius=r, angle=-90)
    P += gf.path.straight(length=5*m)  
    P += gf.path.arc(radius=r, angle=-90) 
    P += gf.path.straight(length=(n-4)*s)  
    P += gf.path.arc(radius=r, angle=-90) 
    P += gf.path.straight(length=3*m)  
    P += gf.path.arc(radius=r, angle=-90) 
    P += gf.path.straight(length=(n-6)*s)  
    P += gf.path.arc(radius=r, angle=-90)
    P += gf.path.straight(length=m)  
    P += gf.path.arc(radius=r, angle=-90) 
    P += gf.path.straight(length=2*s)  
    P += gf.path.arc(radius=r, angle=-90)
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=(n-11)*s) 
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=m)  
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=(n-6)*s)
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=3*m)  
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=(n-4)*s)
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=5*m)  
    P += gf.path.arc(radius=r, angle=90) 
    P += gf.path.straight(length=(n-2)*s)
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=7*m)  
    P += gf.path.arc(radius=r, angle=90)  
    P += gf.path.straight(length=(n)*s)
    P += gf.path.arc(radius=r, angle=90)
    P += gf.path.straight(length=8*m)  
    P += gf.path.arc(radius=r, angle=-90)
    P += gf.path.straight(length=b)
    
    # Get the final position of the path
    end_point = P.points[-1]
    
    # Add ports to the component
    c.add_port(name="o1", center=start_point, width=w, orientation=180, layer=layer)
    c.add_port(name="o2", center=end_point, width=w, orientation=0, layer=layer)
    
    # Extrude the path with the defined cross-section
    wg = gf.path.extrude(P, cross_section=cs)
    
    # Add the extruded waveguide to the component
    wg_ref = c << wg
    
    # Add grating couplers to the component
    try:
        # Create a grating coupler
        try:
            # First attempt with elliptical uniform grating coupler
            gc = gf.components.grating_coupler_elliptical_uniform(
                width_waveguide=w,
                polarization="te",
                wavelength=1.55,
                fiber_angle=15,
                layer=layer
            )
            print("Using elliptical uniform grating coupler")
        except Exception:
            # Fallback to a simpler grating coupler if the elliptical one fails
            print("Elliptical grating coupler failed, trying simpler grating coupler")
            gc = gf.components.grating_coupler_te(
                layer=layer,
                width=w
            )
        
        # Input grating coupler (left/west)
        gc_in = c << gc
        gc_in.rotate(180)  # Rotate to face left (input side)
        gc_in.move(origin=gc_in.ports["o1"].center, destination=start_point)
        
        # Output grating coupler (right/east)
        gc_out = c << gc
        gc_out.move(origin=gc_out.ports["o1"].center, destination=end_point)
        
        # Add references to the grating couplers in the component
        c.add_ref(gc_in, name="gc_in")
        c.add_ref(gc_out, name="gc_out")
        
        # Add new ports at the grating coupler fiber interfaces
        if "o2" in gc_in.ports:
            c.add_port("optical_in", port=gc_in.ports["o2"])
        
        if "o2" in gc_out.ports:
            c.add_port("optical_out", port=gc_out.ports["o2"])
            
        c.info["has_grating_couplers"] = True
        print("Added grating couplers successfully")
    except Exception as e:
        print(f"Warning: Could not add grating couplers: {e}")
        c.info["has_grating_couplers"] = False
    
    return c

# Functions for placement system compatibility
def get_component(width=None):
    """Function for placement system compatibility - returns (component, die_name)"""
    # Use provided width or fall back to default
    wg_width = width if width is not None else waveguide_width
    
    # Create spiral component with the specified width
    spiral_comp = create_spiral_with_couplers(
        distance_bw_couplers=distance_bw_couplers,
        length_of_the_coupler=length_of_the_coupler,
        bend_radius=bend_radius,
        ebm_field_size=ebm_field_size,
        waveguide_width=wg_width,
        total_waveguide_length=total_waveguide_length
    )
    
    # Create die name based on width
    width_nm = int(wg_width * 1000)
    die_name = f"spiral_w{width_nm}"
    
    return spiral_comp, die_name

def p_cascades(width=None):
    """Alternative function name for placement system compatibility - returns (component, die_name)"""
    return get_component(width=width)

# Create the spiral component with grating couplers for standalone use
spiral = create_spiral_with_couplers(
    distance_bw_couplers=distance_bw_couplers,
    length_of_the_coupler=length_of_the_coupler,
    bend_radius=bend_radius,
    ebm_field_size=ebm_field_size,
    waveguide_width=waveguide_width,
    total_waveguide_length=total_waveguide_length
)

# Example usage
if __name__ == "__main__":
    # Display some information about the component
    print(f"Component name: {spiral.name}")
    
    # Check component ports
    try:
        print("Checking component ports...")
        if hasattr(spiral, 'ports') and spiral.ports:
            port_names = []
            for port_name, port in spiral.ports.items():
                port_names.append(port_name)
                print(f"Port: {port_name}, at position {port.center}, orientation {port.orientation}")
            print(f"Component ports: {port_names}")
        else:
            print("Component has no ports")
    except Exception as e:
        print(f"Error listing ports: {e}")
          # Show the component (without plotting)
    print("Showing component...")
    try:
        # Show the component in the viewer
        spiral.show()
    except Exception as e:
        print(f"Error showing component: {e}")
        
    # Write the component to a GDS file
    try:
        print("Writing component to GDS file...")
        spiral.write_gds("spiral_with_gratings.gds")
        print("GDS file saved as 'spiral_with_gratings.gds'")
    except Exception as e:
        print(f"Error writing GDS: {e}")
