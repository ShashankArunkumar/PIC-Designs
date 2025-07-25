import gdsfactory as gf
import json
import random  # Import the random module

# Define the Devise_origin point
Devise_origin = (250, -250)

# Define a new NW_origin point
NW_origin = (Devise_origin[0] - 4.75, Devise_origin[1] - 4.75)

def create_filled_box():
    """
    Create a 0.5x0.5 micron filled box renamed as NW_marker with a unique name.

    Returns:
        gf.Component: The filled box component.
    """
    filled_box = gf.Component(f"NW_marker_{letter}{number}")
    filled_box.add_polygon([
        (0, 0),
        (0.5, 0),
        (0.5, 0.5),
        (0, 0.5),
        (0, 0)
    ], layer=(3, 0))
    return filled_box

def create_outline():
    """
    Create the outline of a 500x500 box with the top-left corner at the origin.

    Returns:
        gf.Component: The outline component.
    """
    # Create a new component for the outline with a unique name
    outline = gf.Component(f"500_box_{letter}{number}")

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
        Create a single 8x8 marker box with a unique name.

        Returns:
            gf.Component: The marker component.
        """
        marker = gf.Component(f"Marker_{letter}{number}")
        marker_size = 8
        marker.add_polygon([
            (-marker_size / 2, marker_size / 2),
            (marker_size / 2, marker_size / 2),
            (marker_size / 2, -marker_size / 2),
            (-marker_size / 2, -marker_size / 2),
            (-marker_size / 2, marker_size / 2)
        ], layer=(97, 0))
        return marker

    # Create the marker component
    marker = create_marker()

    # Define marker positions
    marker_positions = [
        (20, -20),(130,-20),(20,-130),  # Top-left corner
        (480, -20),(370,-20),(480,-130),  # Top-right corner
        (20, -480),(20,-370),(130,-480),  # Bottom-left corner
        (480, -480),(370,-480),(480,-370),  # Bottom-right corner
    ]

    # Create the top-level component
    top_level = gf.Component(f"{letter}{number}")

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

    # Recreate the grid of 200x200 boxes centered at Devise_origin
    def create_grid(num_rows=3, num_cols=4, grid_box_size=200):
        """
        Create a grid of boxes with dynamic rows, columns, and box size.

        Args:
            num_rows (int): Number of rows in the grid.
            num_cols (int): Number of columns in the grid.
            grid_box_size (int): Size of each grid box.

        Returns:
            list: Positions for the grid.
        """
        border_width = 0.005  # Adjust border width as needed

        # Define positions for the grid with translation by (200, 200)
        grid_positions = [
            (Devise_origin[0] + (col - 1) * grid_box_size + 200, Devise_origin[1] + (row - 1) * grid_box_size + 200)
            for row in range(-(num_rows // 2), (num_rows // 2) + 1)  # Rows based on variables
            for col in range(-(num_cols // 2), (num_cols // 2) + 1)  # Columns based on variables
        ]

        return grid_positions

    # Create the grid box component
    def create_grid_box(grid_box_size=200):
        """
        Create a grid box with a specified size.

        Args:
            grid_box_size (int): Size of the grid box.

        Returns:
            gf.Component: The grid box component.
        """
        # Append a random number to the component name to ensure uniqueness
        grid_box = gf.Component(f"Grid_Box_{random.randint(1000, 9999)}")

        # Top edge
        grid_box.add_polygon([
            (-grid_box_size / 2, grid_box_size / 2 - border_width / 2),
            (grid_box_size / 2, grid_box_size / 2 - border_width / 2),
            (grid_box_size / 2, grid_box_size / 2 + border_width / 2),
            (-grid_box_size / 2, grid_box_size / 2 + border_width / 2),
            (-grid_box_size / 2, grid_box_size / 2 - border_width / 2)
        ], layer=(4, 0))

        # Bottom edge
        grid_box.add_polygon([
            (-grid_box_size / 2, -grid_box_size / 2 + border_width / 2),
            (grid_box_size / 2, -grid_box_size / 2 + border_width / 2),
            (grid_box_size / 2, -grid_box_size / 2 - border_width / 2),
            (-grid_box_size / 2, -grid_box_size / 2 - border_width / 2),
            (-grid_box_size / 2, -grid_box_size / 2 + border_width / 2)
        ], layer=(4, 0))

        # Left edge
        grid_box.add_polygon([
            (-grid_box_size / 2 + border_width / 2, grid_box_size / 2),
            (-grid_box_size / 2 - border_width / 2, grid_box_size / 2),
            (-grid_box_size / 2 - border_width / 2, -grid_box_size / 2),
            (-grid_box_size / 2 + border_width / 2, -grid_box_size / 2),
            (-grid_box_size / 2 + border_width / 2, grid_box_size / 2)
        ], layer=(4, 0))

        # Right edge
        grid_box.add_polygon([
            (grid_box_size / 2 - border_width / 2, grid_box_size / 2),
            (grid_box_size / 2 + border_width / 2, grid_box_size / 2),
            (grid_box_size / 2 + border_width / 2, -grid_box_size / 2),
            (grid_box_size / 2 - border_width / 2, -grid_box_size / 2),
            (grid_box_size / 2 - border_width / 2, grid_box_size / 2)
        ], layer=(4, 0))

        return grid_box

    # Create the grid box component
    grid_box = create_grid_box()

    # Add grid boxes to the top-level component
    for position in create_grid(num_rows, num_cols):
        top_level.add_ref(grid_box).move(position)

    # Add a text component at position (75, -75)
    def create_text_component(letter='A', number=1):
        """
        Create a text component that adds visible text to the GDS file using `text`.

        Args:
            letter (str): The letter input for the text.
            number (int): The number input for the text.

        Returns:
            gf.Component: The text component.
        """
        text = f"{letter}{number}"
        text_component = gf.components.text(text=text, size=50, position=(0, 0), justify='left', layer=(5, 0))

        return text_component

    # Create the text component with default values
    text_component = create_text_component(letter=letter, number=number)

    # Add the text component to the top-level component at a visible position
    top_level.add_ref(text_component).move((40, -100))

    # Define a polygon in the shape of an arrow mark
    def create_arrow():
        """
        Create an arrow-shaped polygon.

        Returns:
            gf.Component: The arrow component.
        """
        # Append a random number to the component name to ensure uniqueness
        arrow = gf.Component(f"Arrow_{random.randint(1000, 9999)}")
        arrow.add_polygon([
            (0, 65),  # Tip of the arrow
            (-40, 25),  # Left edge of the arrowhead
            (-10, 25),  # Left base of the arrowhead
            (-15, -50),  # Left bottom of the tail
            (15, -50),  # Right bottom of the tail
            (10, 25),  # Right base of the arrowhead
            (40, 25),  # Right edge of the arrowhead
            
        ], layer=(7, 0))
        return arrow

    # Create the arrow component
    arrow = create_arrow()

    # Add the arrow to the top-level component, rotate it 45 degrees, and place it at (80, -420)
    arrow_ref = top_level.add_ref(arrow)
    arrow_ref.rotate(-45)
    arrow_ref.move((90, -410))

    # Duplicate the arrow, rotate it by 45 degrees, and place it at (420, -420)
    arrow_ref_duplicate = top_level.add_ref(arrow)
    arrow_ref_duplicate.rotate(45)
    arrow_ref_duplicate.move((410, -410))

    # Return the top-level component
    return top_level

# Load configuration from cell.json
with open("c:/Users/Admin/Desktop/Codes for Design/Depot/Json/cell.json", "r") as config_file:
    config = json.load(config_file)

letter = config["letter"]
number = config["number"]
num_rows = config["num_rows"]
num_cols = config["num_cols"]

if __name__ == "__main__":
    # Create the outline
    outline = create_outline()

    # Display the outline
    outline.show()