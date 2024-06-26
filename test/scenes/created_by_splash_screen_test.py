from unittest.mock import MagicMock

import pygame as pg
import pytest
from nodes.game import Game
from scenes.created_by_splash_screen import CreatedBySplashScreen


@pytest.fixture
def game_instance():
    game = MagicMock(spec=Game)
    game.key_bindings = {"enter": pg.K_RETURN}
    game.is_enter_just_pressed = False
    game.debug_draw = MagicMock()
    return game


@pytest.fixture
def created_by_splash_screen_instance(game_instance):
    return CreatedBySplashScreen(game_instance)


def test_on_curtain_invisible_listener_registered(created_by_splash_screen_instance):
    curtain = created_by_splash_screen_instance.curtain
    assert any(
        listener == created_by_splash_screen_instance.on_curtain_invisible
        for listener in curtain.listener_invisible_ends
    )


def test_on_curtain_opaque_listener_registered(created_by_splash_screen_instance):
    curtain = created_by_splash_screen_instance.curtain
    assert any(
        listener == created_by_splash_screen_instance.on_curtain_opaque
        for listener in curtain.listener_opaque_ends
    )


def test_on_entry_delay_timer_end_listener_registered(
    created_by_splash_screen_instance,
):
    entry_delay_timer = created_by_splash_screen_instance.entry_delay_timer
    assert any(
        listener == created_by_splash_screen_instance.on_entry_delay_timer_end
        for listener in entry_delay_timer.listener_end
    )


def test_on_exit_delay_timer_end_listener_registered(created_by_splash_screen_instance):
    exit_delay_timer = created_by_splash_screen_instance.exit_delay_timer
    assert any(
        listener == created_by_splash_screen_instance.on_exit_delay_timer_end
        for listener in exit_delay_timer.listener_end
    )


def test_on_screen_time_timer_end_listener_registered(
    created_by_splash_screen_instance,
):
    screen_time_timer = created_by_splash_screen_instance.screen_time_timer
    assert any(
        listener == created_by_splash_screen_instance.on_screen_time_timer_end
        for listener in screen_time_timer.listener_end
    )


def test_on_curtain_invisible_sets_state_to_reached_invisible(
    created_by_splash_screen_instance,
):
    created_by_splash_screen_instance.set_state = MagicMock()
    created_by_splash_screen_instance.on_curtain_invisible()
    created_by_splash_screen_instance.set_state.assert_called_once_with(
        CreatedBySplashScreen.REACHED_INVISIBLE
    )


def test_on_curtain_opaque_sets_state_to_reached_opaque(
    created_by_splash_screen_instance,
):
    created_by_splash_screen_instance.set_state = MagicMock()
    created_by_splash_screen_instance.on_curtain_opaque()
    created_by_splash_screen_instance.set_state.assert_called_once_with(
        CreatedBySplashScreen.REACHED_OPAQUE
    )


def test_initial_state_is_just_entered(created_by_splash_screen_instance):
    assert created_by_splash_screen_instance.state == CreatedBySplashScreen.JUST_ENTERED


def test_update_just_entered_state_updates_entry_delay_timer(
    created_by_splash_screen_instance,
):
    created_by_splash_screen_instance.state = CreatedBySplashScreen.JUST_ENTERED
    created_by_splash_screen_instance.entry_delay_timer.update = MagicMock()
    created_by_splash_screen_instance.update(100)
    created_by_splash_screen_instance.entry_delay_timer.update.assert_called_once_with(
        100
    )


def test_update_going_to_invisible_state_updates_curtain(
    created_by_splash_screen_instance,
):
    created_by_splash_screen_instance.state = CreatedBySplashScreen.GOING_TO_INVISIBLE
    created_by_splash_screen_instance.curtain.update = MagicMock()
    created_by_splash_screen_instance.update(100)
    created_by_splash_screen_instance.curtain.update.assert_called_once_with(100)


def test_update_reached_invisible_state_updates_screen_time_timer(
    created_by_splash_screen_instance,
):
    created_by_splash_screen_instance.state = CreatedBySplashScreen.REACHED_INVISIBLE
    created_by_splash_screen_instance.screen_time_timer.update = MagicMock()
    created_by_splash_screen_instance.update(100)
    created_by_splash_screen_instance.screen_time_timer.update.assert_called_once_with(
        100
    )


def test_update_going_to_opaque_state_updates_curtain(
    created_by_splash_screen_instance,
):
    created_by_splash_screen_instance.state = CreatedBySplashScreen.GOING_TO_OPAQUE
    created_by_splash_screen_instance.curtain.update = MagicMock()
    created_by_splash_screen_instance.update(100)
    created_by_splash_screen_instance.curtain.update.assert_called_once_with(100)


def test_update_reached_opaque_state_updates_exit_delay_timer(
    created_by_splash_screen_instance,
):
    created_by_splash_screen_instance.state = CreatedBySplashScreen.REACHED_OPAQUE
    created_by_splash_screen_instance.exit_delay_timer.update = MagicMock()
    created_by_splash_screen_instance.update(100)
    created_by_splash_screen_instance.exit_delay_timer.update.assert_called_once_with(
        100
    )


def test_set_state_transitions_from_just_entered_to_going_to_invisible(
    created_by_splash_screen_instance,
):
    created_by_splash_screen_instance.state = CreatedBySplashScreen.JUST_ENTERED
    created_by_splash_screen_instance.curtain.go_to_invisible = MagicMock()
    created_by_splash_screen_instance.set_state(
        CreatedBySplashScreen.GOING_TO_INVISIBLE
    )
    created_by_splash_screen_instance.curtain.go_to_invisible.assert_called_once()


def test_set_state_transitions_from_going_to_invisible_to_going_to_opaque(
    created_by_splash_screen_instance,
):
    created_by_splash_screen_instance.state = CreatedBySplashScreen.GOING_TO_INVISIBLE
    created_by_splash_screen_instance.curtain.go_to_opaque = MagicMock()
    created_by_splash_screen_instance.set_state(CreatedBySplashScreen.GOING_TO_OPAQUE)
    created_by_splash_screen_instance.curtain.go_to_opaque.assert_called_once()


def test_set_state_transitions_from_reached_invisible_to_going_to_opaque(
    created_by_splash_screen_instance,
):
    created_by_splash_screen_instance.state = CreatedBySplashScreen.REACHED_INVISIBLE
    created_by_splash_screen_instance.curtain.go_to_opaque = MagicMock()
    created_by_splash_screen_instance.set_state(CreatedBySplashScreen.GOING_TO_OPAQUE)
    created_by_splash_screen_instance.curtain.go_to_opaque.assert_called_once()
