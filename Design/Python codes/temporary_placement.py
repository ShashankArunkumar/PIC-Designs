import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import gdsfactory as gf
from pathlib import Path
import kfactory.conf as kf_conf

# Route gdsfactory build artifacts to Setup/build.
for _parent in Path(__file__).resolve().parents:
    _setup_dir = _parent / "Setup"
    if _setup_dir.exists():
        kf_conf.config.__dict__["project_dir"] = _setup_dir
        breakimport json
import importlib
import importlib.util
import sys
from pathlib import Path

# gdsfactory 9.x requires an active PDK before geometry/layer creation.
try:
    gf.get_active_pdk()
except Exception:
    try:
        gf.gpdk.PDK.activate()
    except Exception:
        from gdsfactory.generic_tech import get_generic_pdk
        get_generic_pdk().activate()

def load_component_from_py(py_path, func_name, **kwargs):
    """Dynamically load and call a component factory function from a Python file."""
    module_name = Path(py_path).stem
    if module_name in sys.modules:
        mod = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, py_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

    if not hasattr(mod, func_name):
        raise ValueError(f"Function {func_name} not found in {py_path}")

    factory = getattr(mod, func_name)
    if not callable(factory):
        raise ValueError(f"{func_name} in {py_path} is not callable")

    return factory(**kwargs)

def create_bend_3x3_matrix(bend_array_comp, x_step=2500, y_step=-2500) -> gf.Component:
    """
    Create a 3x3 matrix of bend arrays.
    The top-left corner of the matrix is defined as the origin (0, 0).
    X step: +2500 (columns go right), Y step: -2500 (rows go down).
    """
    matrix = gf.Component()

    for row in range(3):
        for col in range(3):
            x_pos = col * x_step
            y_pos = row * y_step
            ref = matrix << bend_array_comp
            ref.move((x_pos, y_pos))

    return matrix


def create_temporary_placement():
    """
    Build the grid from Grid.py and place 4 copies of the 3x3 bend-array matrix on it
    at positions (-8500, 8500), (1000, 8500), (1000, -1000), (-8500, -1000).
    """
    script_dir = Path(__file__).parent
    json_dir = script_dir.parent / "Json"

    # --- Load Grid ---
    sys.path.insert(0, str(script_dir))
    from Grid import load_config_from_json, create_grid_component
    grid_config = load_config_from_json(str(json_dir / "Grid.json"))
    grid_comp = create_grid_component(grid_config)

    # --- Load bend array component ---
    bend_json_path = json_dir / "bend.json"
    bend_array_json_path = json_dir / "bend_array.json"
    with open(bend_json_path, "r") as f:
        bend_params = json.load(f)
    with open(bend_array_json_path, "r") as f:
        bend_array_params = json.load(f)
    bend_array_comp = load_component_from_py(
        str(script_dir / "bend_array.py"),
        "create_bend_array",
        base_params=bend_params,
        array_params=bend_array_params,
    )

    # --- Build the reusable 3x3 matrix (top-left = origin) ---
    matrix_comp = create_bend_3x3_matrix(bend_array_comp, x_step=2500, y_step=-2500)
    print("Created 3x3 bend-array matrix (top-left = origin)")

    # --- Assemble top-level component ---
    c = gf.Component("temporary_placement")
    c << grid_comp  # background grid

    # Four placement positions on the grid
    positions = [
        (-8500,  8500),
        ( 1000,  8500),
        ( 1000, -1000),
        (-8500, -1000),
    ]

    for idx, (x, y) in enumerate(positions):
        ref = c << matrix_comp
        ref.move((x, y))
        print(f"Placed 3x3 matrix #{idx+1} at ({x}, {y})")

    print("\nTotal: 4 × 3×3 = 36 bend arrays on grid")
    return c


if __name__ == "__main__":
    comp = create_temporary_placement()

    comp.show()

