import json
import os

import gdsfactory as gf

# gdsfactory 9.x requires an active PDK before geometry/layer creation.
try:
    gf.get_active_pdk()
except Exception:
    try:
        gf.gpdk.PDK.activate()
    except Exception:
        from gdsfactory.generic_tech import get_generic_pdk

        get_generic_pdk().activate()

_REQUIRED_FIELDS = (
    "component_type",
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

    missing = [field for field in _REQUIRED_FIELDS if field not in model]
    if missing:
        raise ValueError(
            f"Model '{selected}' is missing required fields: {', '.join(missing)}"
        )

    return dict(model)


def get_gc_width(name: str | None = None) -> float:
    return float(get_gc_params(name).get("width", 0.5))


def create_grating_coupler(name: str | None = None, layer: tuple[int, int] | None = None) -> gf.Component:
    params = get_gc_params(name)

    if params["component_type"] != "grating_coupler_elliptical_uniform":
        raise ValueError(
            "Only 'grating_coupler_elliptical_uniform' is currently supported. "
            f"Got '{params['component_type']}'."
        )

    gc_layer = tuple(params.get("layer", [1, 0])) if layer is None else tuple(layer)
    gc_xs = gf.cross_section.strip(width=float(params["width"]), layer=gc_layer)

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
