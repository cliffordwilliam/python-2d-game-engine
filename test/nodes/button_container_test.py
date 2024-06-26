from unittest.mock import MagicMock

import pygame as pg
import pytest
from nodes.button import Button
from nodes.button_container import ButtonContainer


@pytest.fixture
def button_instance():
    button = MagicMock(spec=Button)
    button.rect = pg.Rect(0, 0, 100, 30)
    button.active_curtain = MagicMock()
    button.active_curtain.rect = pg.Rect(0, 0, 100, 30)
    return button


@pytest.fixture
def button_list(button_instance):
    return [button_instance for _ in range(5)]


@pytest.fixture
def button_container(button_list):
    return ButtonContainer(buttons=button_list, offset=0, limit=3, is_pagination=True)


def test_initialization_with_buttons(button_container, button_list):
    assert button_container.buttons == button_list
    assert button_container.offset == 0
    assert button_container.limit == 3
    assert button_container.is_pagination is True
    assert button_container.buttons_len == len(button_list)
    assert button_container.index == 0


def test_initialization_with_empty_buttons():
    button_container = ButtonContainer(
        buttons=[], offset=0, limit=3, is_pagination=True
    )
    assert button_container.buttons == []
    assert button_container.buttons_len == 0


def test_add_event_listener_index_changed(button_container):
    callback = MagicMock()
    button_container.add_event_listener(callback, ButtonContainer.INDEX_CHANGED)
    assert callback in button_container.listener_index_changed


def test_add_event_listener_button_selected(button_container):
    callback = MagicMock()
    button_container.add_event_listener(callback, ButtonContainer.BUTTON_SELECTED)
    assert callback in button_container.listener_button_selected


def test_set_is_input_allowed_true(button_container):
    button_container.set_is_input_allowed(True)
    assert button_container.is_input_allowed is True
    button_container.buttons[0].set_state.assert_called_with(Button.ACTIVE)


def test_set_is_input_allowed_false(button_container):
    button_container.set_is_input_allowed(False)
    assert button_container.is_input_allowed is False
    button_container.buttons[0].set_state.assert_called_with(Button.INACTIVE)


def test_update_scrollbar_step_and_height(button_container):
    button_container.update_scrollbar_step_and_height()
    assert button_container.scrollbar_height > 0
    assert button_container.scrollbar_step >= 0


def test_event_up_down_input(button_container):
    game = MagicMock()
    game.is_up_just_pressed = True
    game.is_down_just_pressed = False
    old_index = button_container.index
    button_container.set_is_input_allowed(True)
    button_container.event(game)
    assert button_container.index == (old_index - 1) % button_container.buttons_len


def test_event_enter_input(button_container):
    game = MagicMock()
    game.is_up_just_pressed = False
    game.is_down_just_pressed = False
    game.is_enter_just_pressed = True
    callback = MagicMock()
    button_container.add_event_listener(callback, ButtonContainer.BUTTON_SELECTED)
    button_container.set_is_input_allowed(True)
    button_container.event(game)
    callback.assert_called_once_with(button_container.buttons[button_container.index])


def test_draw(button_container):
    surf = pg.Surface((640, 480))
    button_container.draw(surf)
    assert surf.get_at(
        (button_container.description_rect.x, button_container.description_rect.y)
    ) == pg.Color(button_container.DESCRIPTION_SURF_COLOR)


def test_update(button_container):
    dt = 16
    button_container.update(dt)
    for button in button_container.buttons:
        button.update.assert_called_with(dt)
