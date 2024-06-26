from unittest.mock import MagicMock

import pytest
from nodes.debug_draw import DebugDraw


@pytest.fixture
def debug_draw_instance():
    return DebugDraw()


def test_add_object_to_correct_layer(debug_draw_instance):
    obj = {"layer": 0, "type": "text", "x": 10, "y": 20, "text": "Hello"}
    debug_draw_instance.add(obj)
    assert debug_draw_instance.layers[0] == [obj]


def test_add_text_object(debug_draw_instance):
    obj = {"layer": 1, "type": "text", "x": 10, "y": 20, "text": "Hello"}
    debug_draw_instance.add(obj)
    assert debug_draw_instance.layers[1] == [obj]


def test_add_rectangle_object(debug_draw_instance):
    obj = {
        "layer": 1,
        "type": "rect",
        "color": (255, 0, 0),
        "rect": (10, 10, 50, 50),
        "width": 2,
    }
    debug_draw_instance.add(obj)
    assert debug_draw_instance.layers[1] == [obj]


def test_add_line_object(debug_draw_instance):
    obj = {
        "layer": 2,
        "type": "line",
        "color": (0, 255, 0),
        "start": (10, 10),
        "end": (50, 50),
        "width": 2,
    }
    debug_draw_instance.add(obj)
    assert debug_draw_instance.layers[2] == [obj]


def test_add_circle_object(debug_draw_instance):
    obj = {
        "layer": 3,
        "type": "circle",
        "color": (0, 0, 255),
        "center": (30, 30),
        "radius": 15,
    }
    debug_draw_instance.add(obj)
    assert debug_draw_instance.layers[3] == [obj]


def test_add_surface_object(debug_draw_instance):
    mock_surface = MagicMock()
    obj = {"layer": 4, "type": "surf", "surf": mock_surface, "x": 30, "y": 40}
    debug_draw_instance.add(obj)
    assert debug_draw_instance.layers[4] == [obj]
