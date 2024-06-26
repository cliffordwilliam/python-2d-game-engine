from unittest.mock import MagicMock

import pygame as pg
import pytest
from nodes.curtain import Curtain


@pytest.fixture
def curtain_instance():
    return Curtain(
        duration=1.0,
        start_state=Curtain.INVISIBLE,
        max_alpha=255,
        surf_size_tuple=(100, 100),
        is_invisible=True,
        color="black",
    )


def test_go_to_opaque(curtain_instance):
    curtain_instance.go_to_opaque()
    assert curtain_instance.direction == 1
    assert not curtain_instance.is_done


def test_go_to_invisible(curtain_instance):
    curtain_instance.go_to_invisible()
    assert curtain_instance.direction == -1
    assert not curtain_instance.is_done


def test_add_event_listener_invisible_end(curtain_instance):
    callback = MagicMock()
    curtain_instance.add_event_listener(callback, Curtain.INVISIBLE_END)
    assert callback in curtain_instance.listener_invisible_ends


def test_add_event_listener_opaque_end(curtain_instance):
    callback = MagicMock()
    curtain_instance.add_event_listener(callback, Curtain.OPAQUE_END)
    assert callback in curtain_instance.listener_opaque_ends


def test_jump_to_opaque(curtain_instance):
    curtain_instance.jump_to_opaque()
    assert curtain_instance.alpha == curtain_instance.max_alpha
    assert curtain_instance.remainder == 0
    assert curtain_instance.fade_counter == curtain_instance.fade_duration


def test_set_max_alpha(curtain_instance):
    new_max_alpha = 128
    curtain_instance.set_max_alpha(new_max_alpha)
    assert curtain_instance.max_alpha == new_max_alpha


def test_draw(curtain_instance):
    screen = pg.Surface((200, 200))
    curtain_instance.alpha = 128
    curtain_instance.draw(screen, 10)
    assert screen.get_at(
        (curtain_instance.rect.x, curtain_instance.rect.y + 10)
    ) == pg.Color("black")


def test_update_to_opaque(curtain_instance):
    curtain_instance.go_to_opaque()
    curtain_instance.update(1)
    assert curtain_instance.fade_counter > 0
    assert curtain_instance.alpha > 0


def test_update_to_invisible(curtain_instance):
    curtain_instance.go_to_opaque()
    curtain_instance.update(1)
    curtain_instance.go_to_invisible()
    curtain_instance.update(1)
    assert curtain_instance.fade_counter < curtain_instance.fade_duration
    assert curtain_instance.alpha < curtain_instance.max_alpha


def test_update_invisible_end_event(curtain_instance):
    callback = MagicMock()
    curtain_instance.add_event_listener(callback, Curtain.INVISIBLE_END)
    curtain_instance.go_to_invisible()
    curtain_instance.update(1000)
    callback.assert_called_once()


def test_update_opaque_end_event(curtain_instance):
    callback = MagicMock()
    curtain_instance.add_event_listener(callback, Curtain.OPAQUE_END)
    curtain_instance.go_to_opaque()
    curtain_instance.update(1000)
    callback.assert_called_once()
