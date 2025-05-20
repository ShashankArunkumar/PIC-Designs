import gdsfactory as gf
import importlib
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

def load_component_with_die(py_path, die_number=None):
    """Load a component from a Python file, add a die box with the correct die label, and return (component, die_name)."""
    import uuid
    module_name = Path(py_path).stem
    if module_name in sys.modules:
        mod = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, py_path)
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
        # Try to call p_cascades() or a similar function, fallback to a generic 'get_component' if present
        if hasattr(mod, 'p_cascades'):
            c, die_name = mod.p_cascades()
        elif hasattr(mod, 'get_component'):
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

def main():
    import json
    # Load grid config and create grid
    config_path = "Json/Grid.json"
    config = load_config_from_json(config_path)
    if not config:
        print("Failed to load grid configuration.")
        return
    # Create the grid as a separate component named 'Grid'
    grid = create_grid_component(config)
    grid.name = "Grid"

    # Load placements from placement.json
    with open("Json/placement.json", "r") as f:
        placement_data = json.load(f)
    placements = placement_data["placements"]

    # Create Dies component to hold all dies
    dies_component = gf.Component("Dies")
    die_refs = []
    for placement in placements:
        component, die_name = load_component_with_die(placement["py_path"], die_number=placement["die_number"])
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
    top_chip.write_gds("build/gds/grid_with_placement.gds")
    print("GDS with placed component saved as build/gds/grid_with_placement.gds")

    # Show the layout in the viewer
    top_chip.show()

if __name__ == "__main__":
    main()
