import gdsfactory as gf

def create_outline():
    """
    Create the outline of a 500x500 box with the top-left corner at the origin.

    Returns:
        gf.Component: The outline component.
    """
    # Create a new component for the outline
    outline = gf.Component("500_box")

    # Define the size of the box
    width, height = 500, 500

    # Adjust the coordinates to center the rectangle, accounting for the border width
    border_width = 0.005

    # Top edge
    outline.add_polygon([
        (0, border_width / 2),
        (width, border_width / 2),
        (width, -border_width / 2),
        (0, -border_width / 2),
        (0, border_width / 2)
    ], layer=(1, 0))

    # Bottom edge
    outline.add_polygon([
        (0, -height + border_width / 2),
        (width, -height + border_width / 2),
        (width, -height - border_width / 2),
        (0, -height - border_width / 2),
        (0, -height + border_width / 2)
    ], layer=(1, 0))

    # Left edge
    outline.add_polygon([
        (border_width / 2, 0),
        (-border_width / 2, 0),
        (-border_width / 2, -height),
        (border_width / 2, -height),
        (border_width / 2, 0)
    ], layer=(1, 0))

    # Right edge
    outline.add_polygon([
        (width - border_width / 2, 0),
        (width + border_width / 2, 0),
        (width + border_width / 2, -height),
        (width - border_width / 2, -height),
    ], layer=(1, 0))

    # Define a reusable marker component
    def create_marker():
        """
        Create a single 8x8 marker box.

        Returns:
            gf.Component: The marker component.
        """
        marker = gf.Component("Marker")
        marker_size = 8
        marker.add_polygon([
            (-marker_size / 2, marker_size / 2),
            (marker_size / 2, marker_size / 2),
            (marker_size / 2, -marker_size / 2),
            (-marker_size / 2, -marker_size / 2),
            (-marker_size / 2, marker_size / 2)
        ], layer=(2, 0))
        return marker

    # Create the marker component
    marker = create_marker()

    # Define marker positions
    marker_positions = [
        (20, -20),(20,20),(-20,20),(-20,-20),  # Top-left corner
        (480, -20),(520,20),(520,-20),(480,20),  # Top-right corner
        (20, -480),(-20,-520),(20,-520),(-20,-480),  # Bottom-left corner
        (480, -480),(520,-480),(520,-520),(480,-520),  # Bottom-right corner
    ]

    # Create the top-level component
    top_level = gf.Component("Top_Level")

    # Add the outline as a subcomponent of the top-level component
    outline_ref = top_level.add_ref(outline)

    # Add markers as subcomponents of the top-level component
    for position in marker_positions:
        top_level.add_ref(marker).move(position)

    # Create the filled box component
    filled_box = create_filled_box()

    # Define positions relative to Devise_origin
    filled_box_positions = [
        (Devise_origin[0] - 4.5, Devise_origin[1] - 4.5),
        (Devise_origin[0] - 4.5, Devise_origin[1] + 4.5),
        (Devise_origin[0] + 4.5, Devise_origin[1] - 4.5),
        (Devise_origin[0] - 4.5, Devise_origin[1] - 8),
        (Devise_origin[0] - 8, Devise_origin[1] - 4.5)
    ]

    # Add filled boxes to the top-level component
    for position in filled_box_positions:
        top_level.add_ref(filled_box).move(position)

    # Return the top-level component
    return top_level

# Define a 0.5x0.5 micron filled box
def create_filled_box():
    """
    Create a 0.5x0.5 micron filled box.

    Returns:
        gf.Component: The filled box component.
    """
    filled_box = gf.Component("Filled_Box")
    filled_box.add_polygon([
        (0, 0),
        (0.5, 0),
        (0.5, 0.5),
        (0, 0.5),
        (0, 0)
    ], layer=(3, 0))
    return filled_box

# Define the Devise_origin point
Devise_origin = (250, -250)

if __name__ == "__main__":
    # Create the outline
    outline = create_outline()

    # Display the outline
    outline.show()