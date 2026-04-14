import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import gdsfactory as gf
from pathlib import Path
import kfactory.conf as kf_conf
import copy

# Route gdsfactory build artifacts to Setup/build.
for _parent in Path(__file__).resolve().parents:
    _setup_dir = _parent / "Setup"
    if _setup_dir.exists():
        kf_conf.config.__dict__["project_dir"] = _setup_dir
        break
import json
import importlib
import importlib.util
import re
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


def create_width_dependent_component(
    component_file: str,
    width: float,
    script_dir: Path,
    json_dir: Path,
    grating_coupler_model: str | None = None,
) -> gf.Component:
    """
    Create a width-dependent component (bend or length array).
    
    Args:
        component_file: "bend.py" or "length.py" or "bend_array.py" or "length_array.py"
        width: Width in micrometers (e.g., 0.5 for 500nm)
        script_dir: Path to Python codes directory
        json_dir: Path to Json directory
        grating_coupler_model: Optional model override per placement.
    
    Returns:
        gf.Component with the specified width
    """
    if component_file.startswith("bend"):
        # Load bend_array with specified width
        bend_json_path = json_dir / "bend.json"
        bend_array_json_path = json_dir / "bend_array.json"
        
        with open(bend_json_path, "r") as f:
            bend_params = json.load(f)
        with open(bend_array_json_path, "r") as f:
            bend_array_params = json.load(f)
        
        # Set the width in both base and array override sections.
        # bend_array.py merges array_params["bend_element"] over base_params.
        bend_params["wg_width"] = width
        if "bend_element" not in bend_array_params:
            bend_array_params["bend_element"] = {}
        bend_array_params["bend_element"]["wg_width"] = width
        if grating_coupler_model:
            bend_params["grating_coupler_model"] = grating_coupler_model
            bend_array_params["bend_element"]["grating_coupler_model"] = grating_coupler_model

        # Ensure unique top-level/child cell names for each width+GC-model variant.
        if "array" not in bend_array_params:
            bend_array_params["array"] = {}
        width_nm = int(round(float(width) * 1000))
        model_tag = re.sub(r"[^0-9A-Za-z]+", "", str(grating_coupler_model or "default"))
        bend_array_params["array"]["array_name"] = f"BW{width_nm}_{model_tag}"
        bend_array_params["array"]["top_cell_prefix"] = f"BW{width_nm}_{model_tag}_L"
        
        component = load_component_from_py(
            str(script_dir / "bend_array.py"),
            "create_bend_array",
            base_params=bend_params,
            array_params=bend_array_params,
        )
        return component
    
    elif component_file.startswith("length"):
        # Load length_array with specified width.
        # D comes from length_array.json defaults (or whatever that file defines).
        length_array_json_path = json_dir / "length_array.json"
        
        with open(length_array_json_path, "r") as f:
            length_array_params = json.load(f)
        
        # Set width in the length_element section.
        if "length_element" not in length_array_params:
            length_array_params["length_element"] = {}

        length_array_params["length_element"]["width"] = width
        if grating_coupler_model:
            length_array_params["length_element"]["grating_coupler_model"] = grating_coupler_model

        # Prevent collisions for multiple width variants in one layout.
        if "array" not in length_array_params:
            length_array_params["array"] = {}
        width_nm = int(round(float(width) * 1000))
        model_tag = re.sub(r"[^0-9A-Za-z]+", "", str(grating_coupler_model or "default"))
        length_array_params["array"]["array_name"] = f"SW{width_nm}_{model_tag}"
        length_array_params["array"]["top_cell_prefix"] = f"SW{width_nm}_{model_tag}_L"
        
        component = load_component_from_py(
            str(script_dir / "length_array.py"),
            "create_length_array",
            array_params=length_array_params,
        )
        return component
    
    else:
        raise ValueError(f"Unknown component file: {component_file}")


def create_temporary_placement():
    """
    Build the grid from Grid.py and place width-dependent components on it
    according to temporary_placement.json configuration.
    """
    script_dir = Path(__file__).parent
    json_dir = script_dir.parent / "Json"

    # --- Load Grid ---
    sys.path.insert(0, str(script_dir))
    from Grid import load_config_from_json, create_grid_component
    grid_config = load_config_from_json(str(json_dir / "Grid.json"))
    grid_comp = create_grid_component(grid_config)
    print("Created grid component\n")

    # --- Load placement configuration ---
    placement_config_path = json_dir / "temporary_placement.json"
    with open(placement_config_path, "r") as f:
        placement_config = json.load(f)

    # --- Assemble top-level component ---
    c = gf.Component("temporary_placement")
    c << grid_comp  # background grid

    # --- Place components according to configuration ---
    # Reuse already-created parameterized cells to avoid duplicate names in KCLayout.
    component_cache = {}

    for idx, placement in enumerate(placement_config["placements"]):
        component_file = placement["component_file"]
        width = placement["width"]
        x = placement["x"]
        y = placement["y"]
        grating_coupler_model = placement.get("grating_coupler_model", None)
        cache_key = (component_file, width, grating_coupler_model)
        if cache_key not in component_cache:
            model_msg = (
                f", gc_model={grating_coupler_model}"
                if grating_coupler_model
                else ""
            )
            print(f"Creating {component_file} with width={width}µm{model_msg}...")
            component_cache[cache_key] = create_width_dependent_component(
                component_file,
                width,
                script_dir,
                json_dir,
                grating_coupler_model,
            )
        else:
            model_msg = (
                f", gc_model={grating_coupler_model}"
                if grating_coupler_model
                else ""
            )
            print(f"Reusing {component_file} with width={width}µm{model_msg}...")

        component = component_cache[cache_key]
        
        ref = c << component
        ref.move((x, y))
        print(f"Placed '{component.name}' at ({x}, {y})")
    
    print(f"\nTotal placements: {len(placement_config['placements'])}")
    return c


if __name__ == "__main__":
    comp = create_temporary_placement()

    comp.show()


