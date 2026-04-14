import gdsfactory as gf
gf.gpdk.PDK.activate()

def gc_uniform_straight20() -> gf.Component:
    c = gf.Component("gc_uniform_straight20")

    # Uniform grating coupler
    gc = c << gf.components.grating_coupler_elliptical_uniform()

    # Straight waveguide: 20 um
    wg = c << gf.components.straight(length=20.0)

    # Connect straight to the coupler waveguide port
    wg.connect("o1", gc.ports["o1"])

    return c


if __name__ == "__main__":
    c = gc_uniform_straight20()
    c.show()