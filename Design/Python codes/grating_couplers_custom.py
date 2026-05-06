from __future__ import annotations

__all__ = [
    "grating_coupler_elliptical_trenches",
    "grating_coupler_te",
    "grating_coupler_tm",
]

from functools import partial

import numpy as np

import gdsfactory as gf
from gdsfactory.component import Component
from gdsfactory.functions import DEG2RAD
from gdsfactory.typings import LayerSpec

try:
    from ..grating_couplers.functions import grating_tooth_points
except ImportError:
    from gdsfactory.components.grating_couplers.functions import grating_tooth_points

try:
    gf.get_active_pdk()
except Exception:
    try:
        gf.gpdk.PDK.activate()
    except Exception:
        from gdsfactory.generic_tech import get_generic_pdk

        get_generic_pdk().activate()


def _as_layer(layer: LayerSpec) -> tuple[int, int]:
    if isinstance(layer, tuple):
        return layer
    return tuple(gf.get_layer(layer))


@gf.cell
def grating_coupler_elliptical_trenches(
    wg_width: float = 0.5,
    taper_length: float = 16.6,
    period: float = 0.4,
    fill_factor: float = 0.5,
    n_periods: int = 30,
    extra_length: float = 0.0,
    taper_angle: float = 30.0,
    trenches_extra_angle: float = 1.0,
    a1: float = 0.625,
    b1: float = 0.405,
    layer_wg: LayerSpec = (1, 0),
    layer_trench: LayerSpec = (2, 6),
    polarization: str = "te",
) -> Component:
    r"""Custom grating coupler PCell.

    Geometry rules:
    - Waveguide taper lives on `layer_wg`.
    - Grating trenches live on `layer_trench`.
    - Taper and grating overlap in x, but are drawn on different layers.
    - `o1` is the waveguide input port and must match `wg_width`.
    - `o2` is a vertical optical port.
    - Ellipse parameters `a1` and `b1` are direct input parameters.
    - Fill factor is defined as `gap_width / period`.
    """

    layer_wg = _as_layer(layer_wg)
    layer_trench = _as_layer(layer_trench)

    if not 0 < fill_factor < 1:
        raise ValueError("fill_factor must be between 0 and 1.")
    if n_periods <= 0:
        raise ValueError("n_periods must be positive.")
    if period <= 0:
        raise ValueError("period must be positive.")

    gap_width = period * fill_factor
    trench_width = period - gap_width
    total_length = taper_length + period * n_periods + extra_length

    taper_half_end = wg_width / 2 + np.tan(taper_angle * DEG2RAD / 2) * total_length

    c = gf.Component()

    taper_poly = [
        (0.0, -wg_width / 2),
        (total_length, -taper_half_end),
        (total_length, taper_half_end),
        (0.0, wg_width / 2),
    ]
    c.add_polygon(taper_poly, layer_wg)

    # Keep the grating start aligned to the taper start so the two layers overlap.
    # `period` sets the actual pitch.
    p_start = 30
    for p in range(p_start, p_start + n_periods):
        pts = grating_tooth_points(
            (p + 1) * a1,
            (p + 1) * b1,
            0.0,
            width=trench_width,
            taper_angle=taper_angle + trenches_extra_angle,
        )
        pts[:, 0] += p * period
        c.add_polygon(pts, layer_trench)

    c.add_port(
        name="o1",
        center=(0.0, 0.0),
        width=wg_width,
        orientation=180,
        layer=layer_wg,
        port_type="optical",
    )

    c.add_port(
        name="o2",
        center=(total_length, 0.0),
        width=10.0,
        orientation=90,
        layer=layer_trench,
        port_type=f"vertical_{polarization}",
    )

    c.info["a1"] = float(a1)
    c.info["b1"] = float(b1)
    c.info["period"] = float(period)
    c.info["fill_factor"] = float(fill_factor)
    c.info["gap_width"] = float(gap_width)
    c.info["trench_width"] = float(trench_width)
    c.info["n_periods"] = int(n_periods)
    c.info["taper_length"] = float(taper_length)
    c.info["extra_length"] = float(extra_length)
    c.info["total_length"] = float(total_length)
    c.info["taper_angle"] = float(taper_angle)
    c.info["trenches_extra_angle"] = float(trenches_extra_angle)
    c.info["polarization"] = polarization

    return c


grating_coupler_te = partial(
    grating_coupler_elliptical_trenches,
    polarization="te",
    taper_angle=35.0,
)

grating_coupler_tm = partial(
    grating_coupler_elliptical_trenches,
    polarization="tm",
    taper_angle=35.0,
)


if __name__ == "__main__":
    c = grating_coupler_elliptical_trenches()
    c.show()