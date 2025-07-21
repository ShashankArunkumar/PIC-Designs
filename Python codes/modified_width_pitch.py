import gdsfactory as gf
import numpy as np
import uuid  # Add this import at the top of the file

def grating_waveguide(name, wg_width, angle, length):
    """
    Create a waveguide with grating couplers on both ends and text annotations.

    Args:
        name (str): Name of the component.
        wg_width (float): Width of the waveguide.
        angle (float): Angle in degrees to display next to the left grating coupler.
        length (float): Length of the waveguide.

    Returns:
        gf.Component: Component with waveguide, grating couplers, and text annotations.
    """
    neff = 1.607155  # Effective refractive index
    grating_period = 0.532 / (neff - np.sin(np.radians(angle)))  
    wg_length = length  # Use the dynamic length parameter
    grating_n_periods = 40  # Hardcoded number of grating periods
    grating_fill_factor = 0.5  # Hardcoded grating fill factor
    grating_taper_length_gc = 26.0  # Hardcoded grating taper length
    grating_taper_angle_gc = 30.0  # Hardcoded grating taper angle
    grating_wavelength_gc = 0.532  # Hardcoded grating wavelength
    grating_fiber_angle_gc = 15.0  # Hardcoded grating fiber angle
    grating_polarization_gc = "te"  # Hardcoded grating polarization

    wg_xs = gf.cross_section.strip(width=wg_width, layer=(1, 0))
    gc_xs = gf.cross_section.strip(width=wg_width, layer=(1, 0))

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

    wg = gf.components.straight(length=wg_length, cross_section=wg_xs)

    c = gf.Component(name=name)
    wg_ref = c.add_ref(wg)
    gc1_ref = c.add_ref(gc)
    gc2_ref = c.add_ref(gc)

    # Connect left side
    gc1_ref.connect("o1", wg_ref.ports["o1"])

    # Connect right side
    gc2_ref.connect("o1", wg_ref.ports["o2"])

    # Add ports
    c.add_port("opt1", port=gc1_ref.ports["o2"])
    c.add_port("opt2", port=gc2_ref.ports["o2"])

    # Add text next to the grating couplers
    text_layer = (10, 0)  # Define the layer for the text
    text_content_right = f"w{int(wg_width*1000)}p{int(grating_period*1000)}"
    text_content_left = f"{angle} Deg"  # Replace degree symbol with 'degrees'

    # Add text near the left grating coupler
    text_left = gf.components.text(
        text=text_content_left,
        size=10,
        layer=text_layer,
    )
    text_left_ref = c.add_ref(text_left)
    text_left_ref.move((gc1_ref.x - 75, gc1_ref.y))

    # Add text near the right grating coupler
    text_right = gf.components.text(
        text=text_content_right,
        size=10,
        layer=text_layer,
    )
    text_right_ref = c.add_ref(text_right)
    text_right_ref.move((gc2_ref.x + 50, gc2_ref.y))

    return c

def waveguide_mixed_coupler(name, wg_width, angle, length):
    """
    Create a waveguide with mixed couplers: elliptical on the left and rectangular on the right.

    Args:
        name (str): Name of the component.
        wg_width (float): Width of the waveguide.
        angle (float): Angle in degrees to calculate the grating period.
        length (float): Length of the waveguide.

    Returns:
        gf.Component: Component with mixed couplers and waveguide.
    """
    neff = 1.607155  # Effective refractive index
    grating_period = 0.532 / (neff - np.sin(np.radians(angle)))  # Calculate grating period

    wg_length = length  # Use the dynamic length parameter
    grating_n_periods = 40  # Hardcoded number of grating periods
    grating_fill_factor = 0.5  # Hardcoded grating fill factor

    wg_xs = gf.cross_section.strip(width=wg_width, layer=(1, 0))
    gc_xs = gf.cross_section.strip(width=wg_width, layer=(1, 0))

    # Create elliptical grating coupler for the left side
    gc_elliptical = gf.components.grating_coupler_elliptical_uniform(
        n_periods=grating_n_periods,
        period=grating_period,
        fill_factor=grating_fill_factor,
        taper_length=26.0,
        taper_angle=30.0,  # Restore taper angle to 30 degrees for elliptical grating coupler
        wavelength=0.532,
        fiber_angle=15.0,
        polarization="te",
        cross_section=gc_xs,
    )

    # Define a custom cross-section with the desired width
    custom_xs = gf.cross_section.strip(width=wg_width, layer=(1, 0))

    # Create rectangular grating coupler for the right side with refined parameters
    gc_rectangular = gf.components.grating_coupler_rectangular(
        n_periods=grating_n_periods, 
        period=grating_period, 
        fill_factor=0.5, 
        width_grating=wg_width,  # Match the waveguide width
        length_taper=0, 
        polarization='te', 
        wavelength=0.532, 
        taper='taper', 
        layer_slab='SLAB150', 
        cross_section=custom_xs  # Use the custom cross-section
    )

    wg = gf.components.straight(length=wg_length, cross_section=wg_xs)

    c = gf.Component(name=name)
    wg_ref = c.add_ref(wg)
    gc1_ref = c.add_ref(gc_elliptical)
    gc2_ref = c.add_ref(gc_rectangular)

    # Connect left side
    gc1_ref.connect("o1", wg_ref.ports["o1"])

    # Connect right side
    gc2_ref.connect("o1", wg_ref.ports["o2"])

    # Add ports
    c.add_port("opt1", port=gc1_ref.ports["o2"])
    c.add_port("opt2", port=gc2_ref.ports["o2"])

    # Add text next to the grating couplers for waveguide mixed coupler
    text_layer = (10, 0)  # Define the layer for the text
    text_content_right = f"w{int(wg_width*1000)}p{int(grating_period*1000)}"
    text_content_left = f"{angle} Deg"  # Replace degree symbol with 'degrees'

    # Add text near the left grating coupler
    text_left = gf.components.text(
        text=text_content_left,
        size=10,
        layer=text_layer,
    )
    text_left_ref = c.add_ref(text_left)
    text_left_ref.move((gc1_ref.x - 75, gc1_ref.y))

    # Add text near the right grating coupler
    text_right = gf.components.text(
        text=text_content_right,
        size=10,
        layer=text_layer,
    )
    text_right_ref = c.add_ref(text_right)
    text_right_ref.move((gc2_ref.x + 75, gc2_ref.y))

    return c

def create_die(waveguides, spacing=50):
    """
    Create a die with a cascade of waveguides arranged vertically.

    Args:
        waveguides (list): List of dictionaries specifying waveguide parameters.
            Each dictionary should have keys: 'type', 'length', 'angle', 'wg_width'.
        spacing (float): Vertical spacing between waveguides.

    Returns:
        gf.Component: Component representing the die.
    """
    die = gf.Component(name="die")
    y_offset = 0

    for index, params in enumerate(waveguides):
        waveguide_type = params['type']
        length = params['length']
        angle = params['angle']
        wg_width = params['wg_width']

        if waveguide_type == "grating_waveguide":
            wg = grating_waveguide(name=f"grating_{angle}", wg_width=wg_width, angle=angle, length=length)
        elif waveguide_type == "waveguide_mixed_coupler":
            wg = waveguide_mixed_coupler(name=f"mixed_{angle}", wg_width=wg_width, angle=angle, length=length)
        else:
            raise ValueError(f"Unknown waveguide type: {waveguide_type}")

        # Name the waveguides by their angle, length, and type
        waveguide_name = f"{waveguide_type}_{angle}deg_{length}um"
        wg.name = waveguide_name

        wg_ref = die.add_ref(wg)

        # Place waveguides horizontally in a single row
        x_offset = -500 if index % 2 == 0 else 500  # Left column for odd, right column for even
        x_offset *= 2  # Ensure 1000-micron separation between columns
        y_offset = (index // 2) * 150  # Stack waveguides vertically within each column
        wg_ref.move((x_offset, y_offset))

    # Removed the explicit call to `add_die_box_with_grid` to avoid duplicate grids
    return die

def add_die_box_with_grid(component, die_name=None, die_number=None):
    grid_size = 500  # 500 microns grid size
    die_layer = (2, 0)  # Layer for die box
    grid_layer = (3, 0)  # Layer for grid lines
    tag_layer = (4, 0)  # Layer for die name
    marker_layer = (5, 0)  # Layer for e-beam markers

    # Prioritize die_number for naming
    if die_number is not None:
        die_name = f"Die {die_number}"
    elif die_name is None:
        die_name = "Die"

    # Ensure die_name is a string
    die_name = str(die_name)

    marker_size = 8  # Size of e-beam markers
    marker_offset = 18  # Offset for e-beam markers

    # Ensure grid_size is defined and passed correctly
    grid_size_nm = grid_size * 1000  # Convert microns to nanometers
    # Use bbox properties directly
    bbox = component.bbox()
    xmin, ymin, xmax, ymax = bbox.left, bbox.bottom, bbox.right, bbox.top
    width = xmax - xmin
    height = ymax - ymin

    # Calculate die dimensions
    die_width = (int((width + grid_size - 1) // grid_size)) * grid_size
    die_height = (int((height + grid_size - 1) // grid_size)) * grid_size

    n_x = int(die_width // grid_size)
    n_y = int(die_height // grid_size)

    # Center the die at (0,0)
    comp_cx = (xmax + xmin) / 2
    comp_cy = (ymax + ymin) / 2
    component.move((-comp_cx, -comp_cy))

    # Apply grid offset
    grid_offset_x = 50.0  # Move grid 50 microns to the right
    grid_offset_y = 0.0
    die_xmin = -round(die_width / 2 / grid_size) * grid_size + grid_offset_x
    die_ymin = -round(die_height / 2 / grid_size) * grid_size + grid_offset_y

    # Generate a unique identifier if die_number is not provided
    unique_id = die_number if die_number is not None else str(uuid.uuid4())

    # Create grid lines
    die_grid = gf.Component(f"Die_Grid_{unique_id}")
    for i in range(n_x + 1):
        x = i * grid_size
        die_grid.add_ref(
            gf.components.rectangle(
                size=(1, die_height), layer=grid_layer
            )
        ).move((x - 0.5, 0))
    for j in range(n_y + 1):
        y = j * grid_size
        die_grid.add_ref(
            gf.components.rectangle(
                size=(die_width, 1), layer=grid_layer
            )
        ).move((0, y - 0.5))
    die_grid_ref = component.add_ref(die_grid)
    die_grid_ref.move((die_xmin, die_ymin))

    # Add e-beam alignment markers
    e_beam_markers = gf.Component(f"E_beam_markers_{unique_id}")
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

    # Add die name
    tag = gf.Component(f"Tag_{unique_id}")
    text = gf.components.text(text=die_name, size=50, layer=tag_layer)
    text_ref = tag.add_ref(text)
    text_ref.move((50, die_height - 100))
    tag_ref = component.add_ref(tag)
    tag_ref.move((die_xmin, die_ymin))

    return component

def get_component(width=None, die_number=None):
    """
    Generate the main component for placement.

    Args:
        width (float, optional): Width of the waveguide. Defaults to None.
        die_number (int, optional): Die number for labeling. Defaults to None.

    Returns:
        tuple: (gf.Component, str) - The component and its die name.
    """
    # Use the provided width or default to 0.4
    wg_width = width if width is not None else 0.4

    # Example waveguides for the die
    waveguides = [
        {"type": "grating_waveguide", "length": 500, "angle": 30, "wg_width": wg_width},
        {"type": "grating_waveguide", "length": 1000, "angle": 30, "wg_width": wg_width},
        {"type": "waveguide_mixed_coupler", "length": 500, "angle": 30, "wg_width": wg_width},
        {"type": "waveguide_mixed_coupler", "length": 1000, "angle": 30, "wg_width": wg_width},
        {"type": "grating_waveguide", "length": 500, "angle": 45, "wg_width": wg_width},
        {"type": "grating_waveguide", "length": 1000, "angle": 45, "wg_width": wg_width},
        {"type": "waveguide_mixed_coupler", "length": 500, "angle": 45, "wg_width": wg_width},
        {"type": "waveguide_mixed_coupler", "length": 1000, "angle": 45, "wg_width": wg_width},
    ]

    # Create the die component
    die = create_die(waveguides)

    # Generate die name based on die_number
    die_name = f"Die {die_number}" if die_number is not None else "ModifiedWidthPitchDie"

    # Return the component and its die name
    return die, die_name

if __name__ == "__main__":
    # Create and display the grating waveguide component
    c1 = grating_waveguide(name="grating_waveguide", wg_width=0.4, angle=30, length=4000)

    # Create and display the waveguide mixed coupler component
    c2 = waveguide_mixed_coupler(name="waveguide_mixed_coupler", wg_width=0.4, angle=30, length=4000)

    # Create a parent component to arrange them vertically
    parent_component = gf.Component(name="layout")
    c1_ref = parent_component.add_ref(c1)
    c2_ref = parent_component.add_ref(c2)

    # Arrange components vertically
    c2_ref.move((0, c1_ref.ymax + 10))  # Add a small gap between components

    # Display the parent component
    parent_component.show()

    # Example usage: Create a die with a cascade of waveguides
    waveguides = [
        {"type": "grating_waveguide", "length": 500, "angle": 30, "wg_width": 0.4},
        {"type": "grating_waveguide", "length": 1000, "angle": 30, "wg_width": 0.4},
        {"type": "waveguide_mixed_coupler", "length": 500, "angle": 30, "wg_width": 0.4},
        {"type": "waveguide_mixed_coupler", "length": 1000, "angle": 30, "wg_width": 0.4},
        {"type": "grating_waveguide", "length": 500, "angle": 45, "wg_width": 0.4},
        {"type": "grating_waveguide", "length": 1000, "angle": 45, "wg_width": 0.4},
        {"type": "waveguide_mixed_coupler", "length": 500, "angle": 45, "wg_width": 0.4},
        {"type": "waveguide_mixed_coupler", "length": 1000, "angle": 45, "wg_width": 0.4},
        
    ]

    die = create_die(waveguides)
    die.show()
