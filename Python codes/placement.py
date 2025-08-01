import gdsfactory as gf
import importlib
import importlib.util
import sys
from pathlib import Path

# Import the grid creation function from Grid.py
from Grid import load_config_from_json, create_grid_component

def load_component_from_py(py_path, func_name, **kwargs):
    """Dynamically load a component from a Python file given the function name and kwargs."""
    module_name = Path(py_path).stem
    if module_name in sys.modules:
        mod = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, py_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    func = getattr(mod, func_name)
    return func(**kwargs)

def load_width_pitch_component(py_path):
    """Load the main width_pitch component using p_cascades and add_die_box_with_grid."""
    module_name = Path(py_path).stem
    if module_name in sys.modules:
        mod = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, py_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    c, _ = mod.p_cascades()
    c = mod.add_die_box_with_grid(c)
    return c

def load_width_pitch_component_with_name(py_path, die_number=None):
    """Load the main width_pitch component and return (component, die_name). Optionally override die_name."""
    import uuid
    module_name = Path(py_path).stem
    if module_name in sys.modules:
        mod = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, py_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    # Generate a unique cell name for each instance to avoid cell name collision
    unique_id = uuid.uuid4().hex[:8]
    orig_gf_Component = gf.Component
    def UniqueNameComponent(*args, **kwargs):
        if args:
            args = (f"{args[0]}_{unique_id}",) + args[1:]
        elif 'name' in kwargs:
            kwargs['name'] = f"{kwargs['name']}_{unique_id}"
        return orig_gf_Component(*args, **kwargs)
    gf.Component = UniqueNameComponent
    try:
        c, die_name = mod.p_cascades()
        # Pass die_number directly to add_die_box_with_grid for correct label
        c = mod.add_die_box_with_grid(c, die_name=die_number)
    finally:
        gf.Component = orig_gf_Component
    # die_name will be 'Die (x)' if die_number is int, or as passed
    return c, f"Die {die_number}" if die_number is not None else die_name

def load_component_with_die(py_path, die_number=None, width=None):
    """Load a component from a Python file, add a die box with the correct die label, and return (component, die_name)."""
    import uuid
    import importlib.util
    import os
    
    # Handle both relative and absolute paths, and ensure proper path construction
    if not py_path.endswith('.py'):
        py_path = py_path + '.py'
    
    # Convert to Path object for easier manipulation
    path_obj = Path(py_path)
    
    # If it's already an absolute path, use it as is
    if path_obj.is_absolute():
        resolved_path = path_obj
    else:
        # For relative paths, we need to resolve them properly
        # Get the directory where this script is located (should be "Python codes")
        script_dir = Path(__file__).parent
        
        # If the path starts with "Python codes/", we need to go up one level
        if py_path.startswith('Python codes/') or py_path.startswith('Python codes\\'):
            # Remove the "Python codes/" prefix and resolve from parent directory
            relative_part = py_path[len('Python codes/'):].replace('\\', '/')
            resolved_path = script_dir.parent / 'Python codes' / relative_part
        else:
            # Path is relative to current script directory
            resolved_path = script_dir / py_path
    
    # Convert back to string for the rest of the function
    py_path_str = str(resolved_path)
    
    print(f"Debug: Original py_path: {py_path}")
    print(f"Debug: Resolved py_path: {py_path_str}")
    print(f"Debug: File exists: {resolved_path.exists()}")
    
    module_name = resolved_path.stem
    if module_name in sys.modules:
        mod = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, py_path_str)
        if spec is None:
            raise FileNotFoundError(f"Cannot find module file: {py_path_str}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    # Instead of a random uuid, use the die_number for subcell uniqueness
    orig_gf_Component = gf.Component
    def UniqueNameComponent(*args, **kwargs):
        # Always append _{die_number} to the cell name for all subcells
        if args:
            args = (f"{args[0]}_{die_number}",) + args[1:]
        elif 'name' in kwargs:
            kwargs['name'] = f"{kwargs['name']}_{die_number}"
        return orig_gf_Component(*args, **kwargs)
    gf.Component = UniqueNameComponent
    try:        
        # Check if this is width_pitch.py - it doesn't need width parameter since it does internal width sweeping
        if module_name == 'width_pitch':
            if hasattr(mod, 'p_cascades'):
                c, die_name = mod.p_cascades()
            else:
                raise AttributeError(f"width_pitch.py must have a p_cascades function")
        # For other components, try to call p_cascades() or get_component() with width if available
        elif hasattr(mod, 'p_cascades'):
            # Pass width parameter if available
            if width is not None:
                c, die_name = mod.p_cascades(width=width)
            else:
                c, die_name = mod.p_cascades()
        elif hasattr(mod, 'get_component'):
            # Pass width parameter if available
            if width is not None:
                c, die_name = mod.get_component(width=width)
            else:
                c, die_name = mod.get_component()
        else:
            raise AttributeError(f"No suitable component factory found in {py_path}")
        # Try to call add_die_box_with_grid with die_name=die_number if available
        if hasattr(mod, 'add_die_box_with_grid'):
            c = mod.add_die_box_with_grid(c, die_name=die_number)
    finally:
        gf.Component = orig_gf_Component
    return c, f"Die {die_number}" if die_number is not None else die_name

def place_component_on_grid(grid_component, component, position, name=None):
    """Place a component at a specified (x, y) position relative to the grid origin."""
    ref = grid_component.add_ref(component)
    ref.move(position)
    if name:
        ref.name = name
    return ref

def calculate_dynamic_chip_size(placements, margin=2000):
    """Calculate chip size based on die placements with margin"""
    if not placements:
        return [10000, 10000]  # Default fallback
    
    # Get all x and y positions
    x_positions = [p["position"][0] for p in placements]
    y_positions = [p["position"][1] for p in placements]
    
    # Calculate bounds (assuming each die is roughly 3000x3000 microns)
    die_size_estimate = 3000  # This could be made more precise by loading actual die sizes
    
    min_x = min(x_positions) - die_size_estimate/2
    max_x = max(x_positions) + die_size_estimate/2
    min_y = min(y_positions) - die_size_estimate/2
    max_y = max(y_positions) + die_size_estimate/2
    
    # Add margin
    total_width = (max_x - min_x) + 2 * margin
    total_height = (max_y - min_y) + 2 * margin
    
    # Round up to nearest 1000 for clean boundaries
    chip_width = int((total_width + 999) // 1000) * 1000
    chip_height = int((total_height + 999) // 1000) * 1000
    
    print(f"Calculated dynamic chip size: {chip_width} x {chip_height} microns")
    return [chip_width, chip_height]

def main():
    import json
    # Load grid config and create grid using chip size from Grid.json
    config_path = "Json/Grid.json"
    config = load_config_from_json(config_path)
    if not config:
        print("Failed to load grid configuration.")
        return
    
    print(f"Using chip size from Grid.json: {config['chip_size']}")
    
    # Load placements from placement.json
    with open("Json/placement.json", "r") as f:
        placement_data = json.load(f)
    placements = placement_data["placements"]
    
    # Create the grid as a separate component named 'Grid'
    grid = create_grid_component(config)
    grid.name = "Grid"
    
    # Create Dies component to hold all dies
    dies_component = gf.Component("Dies")
    die_refs = []
    for placement in placements:
        # Extract width parameter if it exists, otherwise use None
        width = placement.get("width", None)
        component, die_name = load_component_with_die(
            placement["py_path"], 
            die_number=placement["die_number"],
            width=width
        )
        # Rename the die cell to Die1, Die2, ...
        component.name = die_name.replace(" ", "")  # e.g., Die1, Die2
        die_ref = dies_component.add_ref(component)
        die_ref.move(tuple(placement["position"]))
        die_ref.name = die_name
        die_refs.append(die_ref)

    # Create the top-level chip component
    top_chip = gf.Component("Placed Chip")
    # Add grid and dies as children
    grid_ref = top_chip.add_ref(grid)
    grid_ref.name = "Grid"
    dies_ref = top_chip.add_ref(dies_component)
    dies_ref.name = "Dies"

    # Save the result
    top_chip.write_gds("build/gds/17_07_2025.gds")
    print("GDS with placed component saved as build/gds/grid_with_placement.gds")

    # Show the layout in the viewer
    top_chip.show()

if __name__ == "__main__":
    main()