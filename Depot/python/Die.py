import gdsfactory as gf
import importlib.util
import os
import random
import json

def create_6mm_box(unique_name="6mm_box_boundary"):
    """
    Create a 6mm x 6mm box boundary using four rectangles for the sides.

    Args:
        unique_name (str): A unique name for the box boundary component.

    Returns:
        gf.Component: The 6mm x 6mm box boundary component.
    """
    # Append a random number to the unique name to ensure uniqueness
    unique_name = f"{unique_name}_{random.randint(1000, 9999)}"

    # Create a new component for the box boundary
    box_boundary = gf.Component(unique_name)

    # Define the size of the box and the thickness of the boundaries
    box_size = 6000  # 6mm in microns
    boundary_thickness = 10  # Thickness of the boundary in microns

    # Top boundary
    box_boundary.add_polygon([
        (-box_size / 2, box_size / 2 - boundary_thickness / 2),
        (box_size / 2, box_size / 2 - boundary_thickness / 2),
        (box_size / 2, box_size / 2 + boundary_thickness / 2),
        (-box_size / 2, box_size / 2 + boundary_thickness / 2),
    ], layer=(1, 0))

    # Bottom boundary
    box_boundary.add_polygon([
        (-box_size / 2, -box_size / 2 - boundary_thickness / 2),
        (box_size / 2, -box_size / 2 - boundary_thickness / 2),
        (box_size / 2, -box_size / 2 + boundary_thickness / 2),
        (-box_size / 2, -box_size / 2 + boundary_thickness / 2),
    ], layer=(1, 0))

    # Left boundary
    box_boundary.add_polygon([
        (-box_size / 2 - boundary_thickness / 2, box_size / 2),
        (-box_size / 2 + boundary_thickness / 2, box_size / 2),
        (-box_size / 2 + boundary_thickness / 2, -box_size / 2),
        (-box_size / 2 - boundary_thickness / 2, -box_size / 2),
    ], layer=(1, 0))

    # Right boundary
    box_boundary.add_polygon([
        (box_size / 2 - boundary_thickness / 2, box_size / 2),
        (box_size / 2 + boundary_thickness / 2, box_size / 2),
        (box_size / 2 + boundary_thickness / 2, -box_size / 2),
        (box_size / 2 - boundary_thickness / 2, -box_size / 2),
    ], layer=(1, 0))

    return box_boundary

def add_grid_to_6mm_box(box_boundary):
    """
    Add grid lines of 500x500 micron boxes inside the 6mm x 6mm box boundary.

    Args:
        box_boundary (gf.Component): The 6mm x 6mm box boundary component.

    Returns:
        gf.Component: The updated component with grid lines.
    """
    # Define the grid box size in microns
    grid_box_size = 500

    # Calculate the number of grid lines (6mm / 500 microns = 12 boxes per side)
    num_boxes_per_side = int(6000 / grid_box_size)

    # Add vertical grid lines
    for i in range(-num_boxes_per_side // 2, num_boxes_per_side // 2 + 1):
        x = i * grid_box_size
        box_boundary.add_polygon([
            (x - 0.005, -3000),
            (x + 0.005, -3000),
            (x + 0.005, 3000),
            (x - 0.005, 3000),
        ], layer=(2, 0))

    # Add horizontal grid lines
    for i in range(-num_boxes_per_side // 2, num_boxes_per_side // 2 + 1):
        y = i * grid_box_size
        box_boundary.add_polygon([
            (-3000, y - 0.005),
            (3000, y - 0.005),
            (3000, y + 0.005),
            (-3000, y + 0.005),
        ], layer=(2, 0))

    return box_boundary

def add_filled_boxes_to_edges(grid_component, coordinates_cell):
    """
    Add 8x8 filled boxes at the center of every 500x500 grid box, but only on the first row, first column, last row, and last column.
    The boxes are moved 250 microns inside from all directions and grouped under a cell called coordinates.
    Additionally, print the coordinates centered about the x position of each box.

    Args:
        grid_component (gf.Component): The grid component to which the filled boxes will be added.
        coordinates_cell (gf.Component): The cell to group all filled boxes under.

    Returns:
        gf.Component: The updated grid component with filled boxes.
    """
    # Update filled boxes to stop at 2250 and -2250, with an interval of 250 microns
    grid_box_size = 250
    box_size = 8

    # Add filled boxes to the first row
    y = 2250
    for x in range(-2250, 2251, grid_box_size):
        box = gf.Component(f"box_{x}_{y}_{random.randint(1000, 9999)}")
        box.add_polygon([
            (x - box_size / 2, y - box_size / 2),
            (x + box_size / 2, y - box_size / 2),
            (x + box_size / 2, y + box_size / 2),
            (x - box_size / 2, y + box_size / 2),
        ], layer=(5, 0))
        coordinates_cell.add_ref(box)

        # Add text for coordinates centered about the x position
        text = gf.components.text(text=f"({int(x)}, {int(y)})", size=8, position=(x, y - 50), justify="center", layer=(6, 0))
        coordinates_cell.add_ref(text)

    # Add filled boxes to the last row
    y = -2250
    for x in range(-2250, 2251, grid_box_size):
        box = gf.Component(f"box_{x}_{y}_{random.randint(1000, 9999)}")
        box.add_polygon([
            (x - box_size / 2, y - box_size / 2),
            (x + box_size / 2, y - box_size / 2),
            (x + box_size / 2, y + box_size / 2),
            (x - box_size / 2, y + box_size / 2),
        ], layer=(5, 0))
        coordinates_cell.add_ref(box)

        # Add text for coordinates centered about the x position
        text = gf.components.text(text=f"({int(x)}, {int(y)})", size=8, position=(x, y - 50), justify="center", layer=(6, 0))
        coordinates_cell.add_ref(text)

    # Add filled boxes to the first column
    x = -2250
    for y in range(-2250, 2251, grid_box_size):
        box = gf.Component(f"box_{x}_{y}_{random.randint(1000, 9999)}")
        box.add_polygon([
            (x - box_size / 2, y - box_size / 2),
            (x + box_size / 2, y - box_size / 2),
            (x + box_size / 2, y + box_size / 2),
            (x - box_size / 2, y + box_size / 2),
        ], layer=(5, 0))
        coordinates_cell.add_ref(box)

        # Add text for coordinates centered about the x position
        text = gf.components.text(text=f"({int(x)}, {int(y)})", size=8, position=(x, y - 50), justify="center", layer=(6, 0))
        coordinates_cell.add_ref(text)

    # Add filled boxes to the last column
    x = 2250
    for y in range(-2250, 2251, grid_box_size):
        box = gf.Component(f"box_{x}_{y}_{random.randint(1000, 9999)}")
        box.add_polygon([
            (x - box_size / 2, y - box_size / 2),
            (x + box_size / 2, y - box_size / 2),
            (x + box_size / 2, y + box_size / 2),
            (x - box_size / 2, y + box_size / 2),
        ], layer=(5, 0))
        coordinates_cell.add_ref(box)

        # Add text for coordinates centered about the x position
        text = gf.components.text(text=f"({int(x)}, {int(y)})", size=8, position=(x, y - 50), justify="center", layer=(6, 0))
        coordinates_cell.add_ref(text)

    return grid_component

def create_corner():
    """
    Create an L-shaped polygon for die corners.

    Returns:
        gf.Component: The corner component.
    """
    # Create a new component for the corner
    corner = gf.Component("Corner")

    # Define the dimensions of the L shape
    arm_length = 750  # Length of each arm in microns
    arm_width = 100   # Width of each arm in microns

    # Define the L shape using two rectangles
    # Horizontal arm
    corner.add_polygon([
        (0, 0),
        (arm_length, 0),
        (arm_length, arm_width),
        (0, arm_width),
    ], layer=(98, 0))

    # Vertical arm
    corner.add_polygon([
        (0, 0),
        (arm_width, 0),
        (arm_width, arm_length),
        (0, arm_length),
    ], layer=(98, 0))

    return corner

# Function to dynamically load and place the top-level component from cell.py
def place_cell_component(letter, number, x, y):
    # Load cell.py dynamically
    cell_path = os.path.join(os.path.dirname(__file__), "cell.py")
    spec = importlib.util.spec_from_file_location("cell", cell_path)
    cell = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cell)

    # Update the letter and number variables in cell.py
    cell.letter = letter
    cell.number = number

    # Generate the top-level component
    top_level_component = cell.create_outline()

    # Append a random number to the component name to ensure uniqueness
    random_suffix = random.randint(1000, 9999)
    top_level_component.name = f"{top_level_component.name}_{random_suffix}"

    # Place the component at the specified coordinates
    top_level_component_ref = top_layer.add_ref(top_level_component)
    top_level_component_ref.move((x, y))

if __name__ == "__main__":
    # Create the top-level component with the name as the Die_number variable
    top_layer = gf.Component("Top_Layer")

    # Create a cell to group all filled boxes
    coordinates_cell = gf.Component("coordinates")

    # Create the grid
    grid = add_grid_to_6mm_box(create_6mm_box("grid_box"))

    # Add filled boxes to the edges of the grid and group them under the coordinates cell
    grid = add_filled_boxes_to_edges(grid, coordinates_cell)

    # Add the coordinates cell to the top layer
    coordinates_ref = top_layer.add_ref(coordinates_cell)

    # Add the grid to the top layer
    grid_ref = top_layer.add_ref(grid)

    # Create the boundary
    boundary = create_6mm_box("boundary_box")

    # Add the boundary to the top layer
    boundary_ref = top_layer.add_ref(boundary)

    # Create the corner
    corner = create_corner()

    # Rotate the first corner by -90 degrees and place it at (-3000, 3000)
    corner_ref1 = top_layer.add_ref(corner)
    corner_ref1.rotate(-90)
    corner_ref1.move((-2450, 2450))

    # Duplicate the corner and place it at (-3000, -3000) without rotation
    corner_ref2 = top_layer.add_ref(corner)
    corner_ref2.move((-2450, -2450))

    # Duplicate the corner again, rotate it by 90 degrees, and place it at (3000, -3000)
    corner_ref3 = top_layer.add_ref(corner)
    corner_ref3.rotate(90)
    corner_ref3.move((2450, -2450))

    # Load placement data from Die.json
    json_path = os.path.join(os.path.dirname(__file__), "..", "Json", "Die.json")
    with open(json_path, "r") as json_file:
        die_data = json.load(json_file)

    # Place the top-level components using data from Die.json
    for component in die_data["coordinates"]:
        place_cell_component(component["identifier"], component["number"], component["x"], component["y"])

    # Display the top layer with grid, boundary, corners, filled boxes, and text
    top_layer.show()