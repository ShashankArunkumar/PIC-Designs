import json
import os

import gdsfactory as gf
from pathlib import Path
import kfactory.conf as kf_conf

# Route gdsfactory build artifacts to Setup/build.
for _parent in Path(__file__).resolve().parents:
    _setup_dir = _parent / "Setup"
    if _setup_dir.exists():
        kf_conf.config.__dict__["project_dir"] = _setup_dir
        break
# gdsfactory 9.x requires an active PDK before geometry/layer creation.
try:
    gf.get_active_pdk()
except Exception:
    try:
        gf.gpdk.PDK.activate()
    except Exception:
        from gdsfactory.generic_tech import get_generic_pdk

        get_generic_pdk().activate()

_UNIFORM_FIELDS = (
    "n_periods",
    "period",
    "fill_factor",
    "taper_length",
    "taper_angle",
    "wavelength",
    "fiber_angle",
    "polarization",
    "width",
)

_TRENCH_FIELDS = (
    "polarization",
    "taper_length",
    "taper_angle",
    "trenches_extra_angle",
    "wavelength",
    "fiber_angle",
    "grating_line_width",
    "neff",
    "ncladding",
    "layer_trench",
    "p_start",
    "n_periods",
    "end_straight_length",
    "taper",
    "cross_section",
)


def _json_path() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "Json", "grating_couplers.json")


def _load_gc_library() -> dict:
    with open(_json_path(), "r") as f:
        data = json.load(f)

    if "models" not in data or not isinstance(data["models"], dict):
        raise ValueError("grating_couplers.json must contain a 'models' dictionary.")

    return data


def list_available_gcs() -> list[str]:
    data = _load_gc_library()
    return sorted(data["models"].keys())


def get_gc_params(name: str | None = None) -> dict:
    data = _load_gc_library()
    selected = name or data.get("default_model")
    if not selected:
        raise ValueError("No grating coupler model name provided and no default_model set.")

    model = data["models"].get(selected)
    if model is None:
        available = ", ".join(list_available_gcs())
        raise ValueError(f"Unknown grating coupler model '{selected}'. Available: {available}")

    component_type = model.get("component_type")
    if component_type == "grating_coupler_elliptical_uniform":
        required_fields = _UNIFORM_FIELDS
    elif component_type == "grating_coupler_elliptical_trenches":
        required_fields = _TRENCH_FIELDS
    else:
        raise ValueError(
            f"Model '{selected}' has unsupported component_type '{component_type}'."
        )

    missing = [field for field in required_fields if field not in model]
    if missing:
        raise ValueError(
            f"Model '{selected}' is missing required fields: {', '.join(missing)}"
        )

    return dict(model)


def get_gc_width(name: str | None = None) -> float:
    return float(get_gc_params(name).get("width", 0.5))


def create_grating_coupler(
    name: str | None = None,
    layer: tuple[int, int] | None = None,
    port_width: float | None = None,
) -> gf.Component:
    params = get_gc_params(name)

    component_type = params["component_type"]
    if component_type not in (
        "grating_coupler_elliptical_uniform",
        "grating_coupler_elliptical_trenches",
    ):
        raise ValueError(
            "Only 'grating_coupler_elliptical_uniform' and "
            "'grating_coupler_elliptical_trenches' are currently supported. "
            f"Got '{component_type}'."
        )

    gc_layer = tuple(params.get("layer", [1, 0])) if layer is None else tuple(layer)

    if component_type == "grating_coupler_elliptical_trenches":
        from gdsfactory.components.grating_couplers import grating_coupler_elliptical_trenches

        return grating_coupler_elliptical_trenches(
            polarization=str(params["polarization"]),
            taper_length=float(params["taper_length"]),
            taper_angle=float(params["taper_angle"]),
            trenches_extra_angle=float(params["trenches_extra_angle"]),
            wavelength=float(params["wavelength"]),
            fiber_angle=float(params["fiber_angle"]),
            grating_line_width=float(params["grating_line_width"]),
            neff=float(params["neff"]),
            ncladding=float(params["ncladding"]),
            layer_trench=params["layer_trench"],
            p_start=int(params["p_start"]),
            n_periods=int(params["n_periods"]),
            end_straight_length=float(params["end_straight_length"]),
            taper=params["taper"],
            cross_section=params["cross_section"],
        )

    width_value = float(params["width"]) if port_width is None else float(port_width)
    gc_xs = gf.cross_section.strip(width=width_value, layer=gc_layer)

    return gf.components.grating_coupler_elliptical_uniform(
        n_periods=int(params["n_periods"]),
        period=float(params["period"]),
        fill_factor=float(params["fill_factor"]),
        taper_length=float(params["taper_length"]),
        taper_angle=float(params["taper_angle"]),
        wavelength=float(params["wavelength"]),
        fiber_angle=float(params["fiber_angle"]),
        polarization=str(params["polarization"]),
        cross_section=gc_xs,
    )

