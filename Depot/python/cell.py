import gdsfactory as gf

def create_die_with_grid():
    """
    Create a grid of 200x200 micron boxes within a 600x600 micron area on a separate layer.

    Returns:
        gf.Component: The grid component.
    """
    die_size = (600, 600)  # Die box dimensions in microns
    grid_size = 200  # Grid box size in microns

    grid_layer = (2, 0)  # Layer for the grid lines

    # Create the top-level component for the device block
    device_block = gf.Component("Device_Block")

    # Add the grid as a subcomponent under the device block
    grid_component = gf.Component("Grid")

    # Add the grid lines with the top-left corner as the origin
    for x in range(0, die_size[0] + 1, grid_size):
        grid_component.add_ref(
            gf.components.rectangle(size=(0.5, die_size[1]), layer=grid_layer)
        ).move((x - 0.25, -die_size[1]))  # Center the vertical gridline

    for y in range(0, die_size[1] + 1, grid_size):
        grid_component.add_ref(
            gf.components.rectangle(size=(die_size[0], 0.5), layer=grid_layer)
        ).move((0, -y - 0.25))  # Center the horizontal gridline

    # Add the grid component to the device block
    device_block.add_ref(grid_component)

    # Create a separate component for device markers
    device_markers = gf.Component("Device_Markers")

    # Add text "A1" to the device markers component
    text_layer = (3, 0)  # Layer for the text
    text = gf.components.text(text="A1", size=60, layer=text_layer)
    device_markers.add_ref(text).move((70, -136))

    # Create a horizontal arrow shape
    arrow = gf.Component("Arrow")
    arrow.add_polygon([
        (0, 15), (80, 10), (80, 40), (120,0 ), (80, -40), (80, -10), (0, -15)
    ], layer=(4, 0))

    # Rotate the arrow by 45 degrees and place it in the bottom-left box
    arrow_45 = device_markers.add_ref(arrow)
    arrow_45.rotate(45)
    arrow_45.move((112, -488))

    # Rotate the arrow by 135 degrees and place it in the bottom-right box
    arrow_135 = device_markers.add_ref(arrow)
    arrow_135.rotate(135)
    arrow_135.move((488, -488))

    # Define the layer for alignment boxes
    edge_box_layer = (5, 0)  # Layer for the edge boxes

    # Create a separate component for alignment boxes
    alignment = gf.Component("Alignment")

    # Add 8x8 boxes at a distance of 20 microns from the edges of the 600x600 box
    box_size = 8  # Size of the edge box in microns
    offset = 20  # Distance from the border in microns

    # Adjust alignment boxes to be 20 microns away from the gridlines at the corners of the four 200x200 boxes
    # Add alignment boxes to all four corners of each of the four 200x200 boxes
    # Correct alignment boxes to be in the correct corners of the 200x200 boxes
    # Adjust alignment boxes to remove specific markers
    for i in range(2):  # Iterate over rows (top and bottom)
        for j in range(2):  # Iterate over columns (left and right)
            base_x = j * 2 * grid_size  # Adjust for correct column spacing
            base_y = -i * 2 * grid_size  # Adjust for correct row spacing

            # Top-left corner of the 200x200 box (skip for bottom-right box)
            if not (i == 1 and j == 1):
                alignment.add_ref(
                    gf.components.rectangle(size=(box_size, box_size), layer=edge_box_layer)
                ).move((base_x + offset, base_y - offset))

            # Top-right corner of the 200x200 box (skip for bottom-left box)
            if not (i == 1 and j == 0):
                alignment.add_ref(
                    gf.components.rectangle(size=(box_size, box_size), layer=edge_box_layer)
                ).move((base_x + grid_size - offset - box_size, base_y - offset))

            # Bottom-left corner of the 200x200 box (skip for top-right box)
            if not (i == 0 and j == 1):
                alignment.add_ref(
                    gf.components.rectangle(size=(box_size, box_size), layer=edge_box_layer)
                ).move((base_x + offset, base_y - grid_size + offset))

            # Bottom-right corner of the 200x200 box (skip for top-left box)
            if not (i == 0 and j == 0):
                alignment.add_ref(
                    gf.components.rectangle(size=(box_size, box_size), layer=edge_box_layer)
                ).move((base_x + grid_size - offset - box_size, base_y - grid_size + offset))

    # Add the alignment component to the device markers hierarchy
    device_markers.add_ref(alignment)

    # Add the device markers component to the device block
    device_block.add_ref(device_markers)

    # Create a separate component for the L element
    l_element = gf.Component("L_Element")

    # Add three 0.5x0.5 micron squares in an L shape to the L element
    l_shape_layer = (6, 0)  # Layer for the L shape squares
    square_size = 0.5  # Size of each square in microns
    spacing = 9  # Center-to-center distance in microns

    # Bottom-left square
    l_element.add_ref(
        gf.components.rectangle(size=(square_size, square_size), layer=l_shape_layer)
    ).move((0, 0))

    # Bottom-right square
    l_element.add_ref(
        gf.components.rectangle(size=(square_size, square_size), layer=l_shape_layer)
    ).move((spacing, 0))

    # Top-left square
    l_element.add_ref(
        gf.components.rectangle(size=(square_size, square_size), layer=l_shape_layer)
    ).move((0, spacing))

    # Move the L element to the center of the middle 200x200 box
    center_x = die_size[0] / 2 - spacing / 2
    center_y = -die_size[1] / 2  - spacing / 2
    l_element_ref = device_markers.add_ref(l_element)
    l_element_ref.move((center_x, center_y))

    # Define NW_origin as the bottom-left corner of the bottom-left box of the L element
    NW_origin = (center_x, center_y)

    return device_block

if __name__ == "__main__":
    # Generate the grid
    grid = create_die_with_grid()

    # Display the grid
    grid.show()