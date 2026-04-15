import gdsfactory as gf
from pathlib import Path
import json
import random
import kfactory.conf as kf_conf


for _parent in Path(__file__).resolve().parents:
    _setup_dir = _parent / "Setup"
    if _setup_dir.exists():
        kf_conf.config.__dict__["project_dir"] = _setup_dir
        break


try:
    gf.get_active_pdk()
except Exception:
    try:
        gf.gpdk.PDK.activate()
    except Exception:
        from gdsfactory.generic_tech import get_generic_pdk
        get_generic_pdk().activate()


DEVICE_ORIGIN = (250.0, -250.0)


def _add_outline(top_level: gf.Component, width: float = 500.0, height: float = 500.0, border: float = 0.005) -> None:
    top_level.add_polygon(
        [(0, border / 2), (width, border / 2), (width, -border / 2), (0, -border / 2)],
        layer=(10, 0),
    )
    top_level.add_polygon(
        [
            (0, -height + border / 2),
            (width, -height + border / 2),
            (width, -height - border / 2),
            (0, -height - border / 2),
        ],
        layer=(10, 0),
    )
    top_level.add_polygon(
        [(border / 2, 0), (-border / 2, 0), (-border / 2, -height), (border / 2, -height)],
        layer=(10, 0),
    )
    top_level.add_polygon(
        [
            (width - border / 2, 0),
            (width + border / 2, 0),
            (width + border / 2, -height),
            (width - border / 2, -height),
        ],
        layer=(10, 0),
    )


def _add_markers(top_level: gf.Component) -> None:
    marker = gf.Component(f"marker_8x8_{random.randint(10000, 99999)}")
    marker_size = 8.0
    marker.add_polygon(
        [
            (-marker_size / 2, marker_size / 2),
            (marker_size / 2, marker_size / 2),
            (marker_size / 2, -marker_size / 2),
            (-marker_size / 2, -marker_size / 2),
        ],
        layer=(97, 0),
    )

    marker_positions = [
        (20, -20), (130, -20), (20, -130),
        (480, -20), (370, -20), (480, -130),
        (20, -480), (20, -370), (130, -480),
        (480, -480), (370, -480), (480, -370),
    ]

    for position in marker_positions:
        top_level.add_ref(marker).move(position)


def _add_nw_filled_boxes(top_level: gf.Component) -> None:
    filled_box = gf.Component(f"nw_marker_0p5_{random.randint(10000, 99999)}")
    filled_box.add_polygon([(0, 0), (0.5, 0), (0.5, 0.5), (0, 0.5)], layer=(3, 0))

    filled_box_positions = [
        (DEVICE_ORIGIN[0] - 4.5, DEVICE_ORIGIN[1] - 4.5),
        (DEVICE_ORIGIN[0] - 4.5, DEVICE_ORIGIN[1] + 4.5),
        (DEVICE_ORIGIN[0] + 4.5, DEVICE_ORIGIN[1] - 4.5),
        (DEVICE_ORIGIN[0] - 4.5, DEVICE_ORIGIN[1] - 8.0),
        (DEVICE_ORIGIN[0] - 8.0, DEVICE_ORIGIN[1] - 4.5),
    ]

    for position in filled_box_positions:
        top_level.add_ref(filled_box).move(position)


def _add_text(top_level: gf.Component, letter: str, number: int) -> None:
    text_component = gf.components.text(
        text=f"{letter}{number}", size=50, position=(0, 0), justify="left", layer=(5, 0)
    )
    top_level.add_ref(text_component).move((40, -100))


def _add_grid(top_level: gf.Component, num_rows: int, num_cols: int, grid_box_size: float = 200.0, border: float = 0.005) -> None:
    grid_box = gf.Component(f"grid_box_{random.randint(10000, 99999)}")

    grid_box.add_polygon(
        [
            (-grid_box_size / 2, grid_box_size / 2 - border / 2),
            (grid_box_size / 2, grid_box_size / 2 - border / 2),
            (grid_box_size / 2, grid_box_size / 2 + border / 2),
            (-grid_box_size / 2, grid_box_size / 2 + border / 2),
        ],
        layer=(4, 0),
    )
    grid_box.add_polygon(
        [
            (-grid_box_size / 2, -grid_box_size / 2 + border / 2),
            (grid_box_size / 2, -grid_box_size / 2 + border / 2),
            (grid_box_size / 2, -grid_box_size / 2 - border / 2),
            (-grid_box_size / 2, -grid_box_size / 2 - border / 2),
        ],
        layer=(4, 0),
    )
    grid_box.add_polygon(
        [
            (-grid_box_size / 2 + border / 2, grid_box_size / 2),
            (-grid_box_size / 2 - border / 2, grid_box_size / 2),
            (-grid_box_size / 2 - border / 2, -grid_box_size / 2),
            (-grid_box_size / 2 + border / 2, -grid_box_size / 2),
        ],
        layer=(4, 0),
    )
    grid_box.add_polygon(
        [
            (grid_box_size / 2 - border / 2, grid_box_size / 2),
            (grid_box_size / 2 + border / 2, grid_box_size / 2),
            (grid_box_size / 2 + border / 2, -grid_box_size / 2),
            (grid_box_size / 2 - border / 2, -grid_box_size / 2),
        ],
        layer=(4, 0),
    )

    x_offset = (num_cols - 1) / 2.0
    y_offset = (num_rows - 1) / 2.0

    for row in range(num_rows):
        for col in range(num_cols):
            x = DEVICE_ORIGIN[0] + (col - x_offset) * grid_box_size
            y = DEVICE_ORIGIN[1] + (row - y_offset) * grid_box_size
            top_level.add_ref(grid_box).move((x, y))


# Global variables for create_outline() compatibility with Die.py
letter = "A"
number = 1
num_rows = 3
num_cols = 3


def create_outline() -> gf.Component:
    """Legacy interface for Die.py compatibility. Uses global variables: letter, number, num_rows, num_cols.
    No triangle support (original Die.py behavior)."""
    top_level = gf.Component(f"{letter}{number}")

    _add_outline(top_level)
    _add_markers(top_level)
    _add_nw_filled_boxes(top_level)
    _add_grid(top_level, num_rows=num_rows, num_cols=num_cols)
    _add_text(top_level, letter=letter, number=number)

    return top_level


if __name__ == "__main__":
    config_path = Path(__file__).resolve().parents[1] / "Json" / "cell.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing configuration file: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    # Use globals for legacy behavior
    letter = str(config["letter"])
    number = int(config["number"])
    num_rows = int(config["num_rows"])
    num_cols = int(config["num_cols"])

    component = create_outline()
    component.show()
