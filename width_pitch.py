import gdsfactory as gf


def waveguide_with_grating_couplers():
    # Parameters
    wg_length = 3000.0  # microns
    wg_width = 0.5      # microns
    taper_length = 10.0 # microns
    grating_n_periods = 20
    grating_period = 0.75
    grating_fill_factor = 0.5
    grating_taper_length_gc = 16.6
    grating_taper_angle_gc = 30.0
    grating_wavelength_gc = 1.55
    grating_fiber_angle_gc = 15.0
    grating_polarization_gc = 'te'

    # Define a single cross-section for all waveguide elements
    wg_xs = gf.cross_section.strip(width=wg_width, layer=(1, 0))

    # Grating coupler definition (remove slab by omitting with_slab and slab_layer, use default parameters)
    gc = gf.components.grating_coupler_elliptical_uniform(
        n_periods=grating_n_periods,
        period=grating_period,
        fill_factor=grating_fill_factor,
        taper_length=grating_taper_length_gc,
        taper_angle=grating_taper_angle_gc,
        wavelength=grating_wavelength_gc,
        fiber_angle=grating_fiber_angle_gc,
        polarization=grating_polarization_gc,
        cross_section=wg_xs,
    )

    # Taper definition
    taper = gf.components.taper(
        length=taper_length,
        width1=gc.ports['o1'].width,
        width2=wg_width,
        cross_section=wg_xs,
    )

    # Waveguide definition
    wg = gf.components.straight(
        length=wg_length,
        cross_section=wg_xs,
    )

    # Top-level component
    c = gf.Component("waveguide_with_grating_couplers")
    wg_ref = c.add_ref(wg)
    taper1_ref = c.add_ref(taper)
    gc1_ref = c.add_ref(gc)
    taper2_ref = c.add_ref(taper)
    gc2_ref = c.add_ref(gc)

    # Connect left side
    taper1_ref.connect('o2', wg_ref.ports['o1'])
    gc1_ref.connect('o1', taper1_ref.ports['o1'])
    # Connect right side
    taper2_ref.connect('o1', wg_ref.ports['o2'])
    gc2_ref.connect('o1', taper2_ref.ports['o2'])

    # Add ports
    c.add_port('opt1', port=gc1_ref.ports['o2'])
    c.add_port('opt2', port=gc2_ref.ports['o2'])

    # Add 8x8 boxes 150 microns away from outside the grating couplers and text annotations
    marker_size = 8.0
    marker_offset = 50.0
    # Use a dedicated marker layer (e.g., (10, 0)) for both markers and text
    marker_layer = (10, 0)
    # Left marker and text
    left_marker = gf.components.rectangle(size=(marker_size, marker_size), layer=marker_layer)
    left_marker_ref = c.add_ref(left_marker)
    # Place marker between the grating coupler and the text
    left_marker_ref.move((gc1_ref.ports['o2'].center[0] - marker_offset, gc1_ref.ports['o2'].center[1] - marker_size/2))
    left_text = gf.components.text(
        text=f"w{int(wg_width*1000)} p{int(grating_period*1000)}",
        size=10,
        layer=marker_layer
    )
    left_text_ref = c.add_ref(left_text)
    # Place text further from the device than the marker, accounting for text width
    left_text_ref.move((left_marker_ref.xmax - left_text.size_info.width - 18, left_marker_ref.ymin))

    # Right marker and text
    right_marker = gf.components.rectangle(size=(marker_size, marker_size), layer=marker_layer)
    right_marker_ref = c.add_ref(right_marker)
    # Place marker between the grating coupler and the text
    right_marker_ref.move((gc2_ref.ports['o2'].center[0] + marker_offset - marker_size, gc2_ref.ports['o2'].center[1] - marker_size/2))
    right_text = gf.components.text(
        text=f"w{int(wg_width*1000)} p{int(grating_period*1000)}",
        size=10,
        layer=marker_layer
    )
    right_text_ref = c.add_ref(right_text)
    # Place text further from the device than the marker, accounting for text width (symmetric to left)
    right_text_ref.move((right_marker_ref.xmax + 10, right_marker_ref.ymin))

    return c


if __name__ == "__main__":
    c = waveguide_with_grating_couplers()
    c.show()
    c.write_gds("build/gds/waveguide_with_grating_couplers.gds")
