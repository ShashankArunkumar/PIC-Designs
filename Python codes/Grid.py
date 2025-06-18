import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Prevent .pyc file creation

import gdsfactory as gf
import numpy as np
import json

def load_config_from_json(config_path: str) -> dict:
    """Load grid configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            print("\nLoaded configuration from JSON:")
            print(f"Chip size: {config.get('chip_size')}")
            print(f"Grid settings: {config.get('grid_settings')}")
            print(f"Coordinate markers: {config.get('coordinate_markers')}")
            print(f"E-beam field: {config.get('ebeam_field')}")
            print(f"Layers: {config.get('layers')}\n")
            return config
    except Exception as e:
        print(f"Error loading grid configuration: {e}")
        return None

def create_chip_boundary_component(chip_size, boundary_line_width, layer_chip_boundary) -> gf.Component:
    """Creates the chip boundary component."""
    c = gf.Component("chip_boundary")
    print(f"Creating chip boundary outline (Layer {layer_chip_boundary})...")
    
    half_width = chip_size[0] / 2
    half_height = chip_size[1] / 2
    
    # Create four rectangles for the boundary, ensuring they are centered before moving
    # Top
    top_rect = gf.components.rectangle(size=(chip_size[0], boundary_line_width), layer=layer_chip_boundary, centered=True)
    top_rect_ref = c << top_rect
    # Move so its center is at (0, half_height - boundary_line_width/2), effectively placing its top edge at half_height
    top_rect_ref.movey(half_height - boundary_line_width / 2)

    # Bottom
    bottom_rect = gf.components.rectangle(size=(chip_size[0], boundary_line_width), layer=layer_chip_boundary, centered=True)
    bottom_rect_ref = c << bottom_rect
    # Move so its center is at (0, -half_height + boundary_line_width/2), effectively placing its bottom edge at -half_height
    bottom_rect_ref.movey(-half_height + boundary_line_width / 2)

    # Left
    # The length of the vertical lines should be the full chip height to meet the horizontal lines
    left_rect = gf.components.rectangle(size=(boundary_line_width, chip_size[1]), layer=layer_chip_boundary, centered=True) 
    left_rect_ref = c << left_rect
    # Move so its center is at (-half_width + boundary_line_width/2, 0), effectively placing its left edge at -half_width
    left_rect_ref.movex(-half_width + boundary_line_width / 2)
    
    # Right
    # The length of the vertical lines should be the full chip height
    right_rect = gf.components.rectangle(size=(boundary_line_width, chip_size[1]), layer=layer_chip_boundary, centered=True)
    right_rect_ref = c << right_rect
    # Move so its center is at (half_width - boundary_line_width/2, 0), effectively placing its right edge at half_width
    right_rect_ref.movex(half_width - boundary_line_width / 2)
    
    return c

def create_grid_lines_component(chip_size, boundary_line_width, grid_box_size, grid_line_width, layer_grid) -> gf.Component:
    """Creates the grid lines component."""
    c = gf.Component("grid_lines")
    print(f"Creating grid (Layer {layer_grid})...")
    
    # Usable area for grid lines (inside the boundary)
    usable_width = chip_size[0] - boundary_line_width
    usable_height = chip_size[1] - boundary_line_width
    
    # Use full chip size for grid lines, so grid is measured from chip edge to edge
    num_x_lines = int(chip_size[0] // grid_box_size)
    num_y_lines = int(chip_size[1] // grid_box_size)

    # Vertical lines
    for i in range(num_x_lines + 1):
        x_coord_val = -chip_size[0]/2 + i * grid_box_size
        line = c << gf.components.rectangle(size=(grid_line_width, chip_size[1]), layer=layer_grid, centered=True)
        line.movex(x_coord_val)
    # Horizontal lines
    for i in range(num_y_lines + 1):
        y_coord_val = -chip_size[1]/2 + i * grid_box_size
        line = c << gf.components.rectangle(size=(chip_size[0], grid_line_width), layer=layer_grid, centered=True)
        line.movey(y_coord_val)
    return c

def create_coordinate_markers_component(chip_size, marker_config, grid_box_size, layer_marker_boxes, layer_marker_text) -> gf.Component:
    """Creates the box-style coordinate markers component."""
    c = gf.Component("coordinate_markers")
    print(f"Adding box-style coordinate markers (Layers {layer_marker_boxes}, {layer_marker_text})...")

    marker_size = marker_config.get("marker_size", 20)
    text_size = marker_config.get("text_size", 10)
    marker_offsets = marker_config.get("offsets", {})
    vertical_offset = marker_offsets.get("vertical", 0) # Offset for left/right markers from boundary
    horizontal_offset = marker_offsets.get("horizontal", 0) # Offset for top/bottom markers from boundary
    text_y_offset = marker_config.get("text_y_offset", -15)
    
    edge_spacing = grid_box_size # Align markers with grid boxes

    # Top markers
    num_markers_top = int(chip_size[0] // edge_spacing)
    for i in range(num_markers_top):
        x_b = -chip_size[0]/2 + i*edge_spacing + edge_spacing/2
        y_b = chip_size[1]/2
        x_m = x_b
        y_m = y_b - horizontal_offset # Marker center y
        marker = c << gf.components.rectangle(size=(marker_size, marker_size), layer=layer_marker_boxes, centered=True)
        marker.move((x_m, y_m))
        ct = f"({int(x_m)},{int(y_m)})"
        txt = c << gf.components.text(text=ct, size=text_size, layer=layer_marker_text, justify='center')
        txt.move((x_m, y_m + text_y_offset))

    # Left markers
    num_markers_left = int(chip_size[1] // edge_spacing)
    for i in range(num_markers_left):
        x_b = -chip_size[0]/2
        y_b = -chip_size[1]/2 + i*edge_spacing + edge_spacing/2
        x_m = x_b + vertical_offset # Marker center x
        y_m = y_b
        marker = c << gf.components.rectangle(size=(marker_size, marker_size), layer=layer_marker_boxes, centered=True)
        marker.move((x_m, y_m))
        ct = f"({int(x_m)},{int(y_m)})"
        txt = c << gf.components.text(text=ct, size=text_size, layer=layer_marker_text, justify='center')
        txt.move((x_m, y_m + text_y_offset))

    # Bottom markers
    num_markers_bottom = int(chip_size[0] // edge_spacing)
    for i in range(num_markers_bottom):
        x_b = -chip_size[0]/2 + i*edge_spacing + edge_spacing/2
        y_b = -chip_size[1]/2
        x_m = x_b
        y_m = y_b + horizontal_offset # Marker center y
        marker = c << gf.components.rectangle(size=(marker_size, marker_size), layer=layer_marker_boxes, centered=True)
        marker.move((x_m, y_m))
        ct = f"({int(x_m)},{int(y_m)})"
        txt = c << gf.components.text(text=ct, size=text_size, layer=layer_marker_text, justify='center')
        txt.move((x_m, y_m + text_y_offset))

    # Right markers
    num_markers_right = int(chip_size[1] // edge_spacing)
    for i in range(num_markers_right):
        x_b = chip_size[0]/2
        y_b = -chip_size[1]/2 + i*edge_spacing + edge_spacing/2
        x_m = x_b - vertical_offset # Marker center x
        y_m = y_b
        marker = c << gf.components.rectangle(size=(marker_size, marker_size), layer=layer_marker_boxes, centered=True)
        marker.move((x_m, y_m))
        ct = f"({int(x_m)},{int(y_m)})"
        txt = c << gf.components.text(text=ct, size=text_size, layer=layer_marker_text, justify='center')
        txt.move((x_m, y_m + text_y_offset))
        
    return c

def create_ebeam_field_markers_component(chip_size, ebeam_config, layer_ebeam_field_markers) -> gf.Component:
    """Creates the E-beam field markers component."""
    c = gf.Component("ebeam_field_markers")
    print(f"Adding E-beam field markers (Layer {layer_ebeam_field_markers})...")

    field_size = ebeam_config.get("field_size", 500)
    ebeam_marker_settings = ebeam_config.get("marker_settings", {})
    ebeam_marker_size = ebeam_marker_settings.get("marker_size", 8.0)
    ebeam_marker_offset = ebeam_marker_settings.get("marker_offset", 16.0) # Offset from field corner

    fields_x = int(chip_size[0] // field_size)
    fields_y = int(chip_size[1] // field_size)

    if fields_x <= 0 or fields_y <= 0:
        print("Warning: Chip size too small or field size too large for any e-beam fields.")
    else:
        # Calculate the total extent of the e-beam field array
        total_ebeam_width = fields_x * field_size
        total_ebeam_height = fields_y * field_size

        # Calculate the starting position to center the e-beam field array on the chip
        start_x_ebeam_array = -total_ebeam_width / 2
        start_y_ebeam_array = -total_ebeam_height / 2
        
        for ix in range(fields_x):
            for iy in range(fields_y):
                # Calculate corners of the current field relative to the array's bottom-left
                field_left_rel = ix * field_size
                field_bottom_rel = iy * field_size
                
                # Absolute coordinates of the field corners
                field_left_abs = start_x_ebeam_array + field_left_rel
                field_right_abs = field_left_abs + field_size
                field_bottom_abs = start_y_ebeam_array + field_bottom_rel
                field_top_abs = field_bottom_abs + field_size

                corners_coords = [
                    (field_left_abs + ebeam_marker_offset, field_top_abs - ebeam_marker_offset),    # Top-left of field
                    (field_right_abs - ebeam_marker_offset, field_top_abs - ebeam_marker_offset),   # Top-right of field
                    (field_left_abs + ebeam_marker_offset, field_bottom_abs + ebeam_marker_offset), # Bottom-left of field
                    (field_right_abs - ebeam_marker_offset, field_bottom_abs + ebeam_marker_offset) # Bottom-right of field
                ]

                for cx, cy in corners_coords:
                    # Check if marker is within chip boundaries before adding
                    if -chip_size[0]/2 < cx < chip_size[0]/2 and \
                       -chip_size[1]/2 < cy < chip_size[1]/2:
                        box = c << gf.components.rectangle(size=(ebeam_marker_size, ebeam_marker_size), layer=layer_ebeam_field_markers, centered=True)
                        box.move((cx, cy))
    return c

def create_origin_marker_component(origin_marker_config, layer_origin_marker) -> gf.Component:
    """Creates the origin marker component."""
    c = gf.Component("origin_marker")
    print("Adding origin marker...")
    origin_marker_size = tuple(origin_marker_config.get("size", (8,8)))
    marker = c << gf.components.rectangle(size=origin_marker_size, layer=layer_origin_marker, centered=True)
    marker.move((0,0)) # Centered at component's origin, which will be (0,0) in parent
    return c

def create_corner_labels_component(chip_size, config, layer_corner_labels) -> gf.Component:
    """Creates the corner labels component."""
    c = gf.Component("corner_labels")
    print(f"Adding corner labels (Layer {layer_corner_labels})...")
    # Remove all corner label text (1,2,3,4)
    return c

def create_grid_component(config: dict) -> gf.Component:
        
    # Extract parameters from config
    chip_size = tuple(config.get("chip_size", (10000, 10000)))
    
    grid_settings = config.get("grid_settings", {})
    grid_box_size = grid_settings.get("grid_box_size", 500)
    grid_line_width = grid_settings.get("grid_line_width", 0.2)
    boundary_line_width = grid_settings.get("boundary_line_width", 2)
    
    print("\nUsing grid parameters:")
    print(f"Chip size: {chip_size}")
    print(f"Grid box size: {grid_box_size}")
    print(f"Grid line width: {grid_line_width}")
    print(f"Boundary line width: {boundary_line_width}\n")
    
    marker_config = config.get("coordinate_markers", {})
    # ebeam_config is extracted within its own component creation function
    ebeam_config = config.get("ebeam_field", {})
    origin_marker_settings_config = config.get("origin_marker_settings", {}) # Renamed to avoid conflict

    layers = config.get("layers", {})
    layer_chip_boundary = tuple(layers.get("chip_boundary", (99, 0)))
    layer_grid = tuple(layers.get("grid", (98, 0)))
    layer_marker_boxes = tuple(layers.get("marker_boxes", (97, 0)))
    layer_marker_text = tuple(layers.get("marker_text", (97, 0)))
    layer_ebeam_field_markers = tuple(layers.get("ebeam_field_markers", (95, 0)))
    layer_origin_marker = tuple(layers.get("origin_(2,0)", layer_marker_boxes)) # Default to marker_boxes if not specified
    layer_corner_labels = tuple(layers.get("corner_labels_layer", layers.get("corner_labels", layer_marker_text))) # Fallback for corner labels layer

    # Create main component that will hold all other sub-components
    top_level_cell = gf.Component("Grid")
    
    # Create and add sub-components
    boundary_comp = create_chip_boundary_component(chip_size, boundary_line_width, layer_chip_boundary)
    top_level_cell << boundary_comp
    
    grid_lines_comp = create_grid_lines_component(chip_size, boundary_line_width, grid_box_size, grid_line_width, layer_grid)
    top_level_cell << grid_lines_comp
    
    coord_markers_comp = create_coordinate_markers_component(chip_size, marker_config, grid_box_size, layer_marker_boxes, layer_marker_text)
    top_level_cell << coord_markers_comp
    
    ebeam_markers_comp = create_ebeam_field_markers_component(chip_size, ebeam_config, layer_ebeam_field_markers)
    top_level_cell << ebeam_markers_comp
    
    origin_marker_comp = create_origin_marker_component(origin_marker_settings_config, layer_origin_marker)
    top_level_cell << origin_marker_comp
    
    # Remove corner labels from the grid hierarchy by not adding the component
    # corner_labels_comp = create_corner_labels_component(chip_size, config, layer_corner_labels)
    # top_level_cell << corner_labels_comp
    return top_level_cell

if __name__ == "__main__":
    # Test the grid generation directly
    config_path = "Json/Grid.json"
    config = load_config_from_json(config_path)
    
    if config:
        grid = create_grid_component(config)
        grid.show()
        # Save as GDS file
        grid.write_gds("build/gds/grid_layout.gds")
        print("GDS file saved as build/gds/grid_layout.gds")
    else:
        print("Failed to load grid configuration")