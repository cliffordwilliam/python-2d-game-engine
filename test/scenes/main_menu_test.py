from unittest.mock import MagicMock

import pytest
from constants import NATIVE_HEIGHT, NATIVE_SURF, NATIVE_WIDTH, pg
from scenes.main_menu import MainMenu


@pytest.fixture
def game_instance():
    game = MagicMock()
    game.quit = MagicMock()
    game.set_is_options_menu_active = MagicMock()
    return game


@pytest.fixture
def main_menu_instance(game_instance):
    return MainMenu(game_instance)


def test_on_entry_delay_timer_end_transitions_state(main_menu_instance):
    main_menu_instance.state = main_menu_instance.JUST_ENTERED
    main_menu_instance.on_entry_delay_timer_end()
    assert main_menu_instance.state == main_menu_instance.GOING_TO_INVISIBLE


def test_on_exit_delay_timer_end_calls_game_quit(main_menu_instance):
    main_menu_instance.selected_button = main_menu_instance.exit_button
    main_menu_instance.on_exit_delay_timer_end()
    main_menu_instance.game.quit.assert_called_once()


def test_on_button_selected_updates_selected_button(main_menu_instance):
    main_menu_instance.on_button_selected(main_menu_instance.new_game_button)
    assert main_menu_instance.selected_button == main_menu_instance.new_game_button


def test_on_button_selected_does_not_change_state(main_menu_instance):
    initial_state = main_menu_instance.state
    main_menu_instance.on_button_selected(main_menu_instance.new_game_button)
    assert main_menu_instance.state == initial_state


def test_init_state_draws_curtain(main_menu_instance):
    main_menu_instance.curtain.draw = MagicMock()
    main_menu_instance.init_state()
    main_menu_instance.curtain.draw.assert_called_once_with(NATIVE_SURF, 0)


def test_set_state_transitions_correctly(main_menu_instance):
    main_menu_instance.state = main_menu_instance.JUST_ENTERED
    main_menu_instance.set_state(main_menu_instance.GOING_TO_INVISIBLE)
    assert main_menu_instance.state == main_menu_instance.GOING_TO_INVISIBLE


def test_update_calls_correct_methods(main_menu_instance):
    main_menu_instance.state = main_menu_instance.JUST_ENTERED
    main_menu_instance.entry_delay_timer.update = MagicMock()
    main_menu_instance.update(100)
    main_menu_instance.entry_delay_timer.update.assert_called_once_with(100)


def test_draw_calls_correct_methods(main_menu_instance):
    # Create a real surface for the background
    main_menu_instance.background_surf = pg.Surface((NATIVE_WIDTH, NATIVE_HEIGHT))

    # Mock the button container and curtain draw methods
    main_menu_instance.button_container.draw = MagicMock()
    main_menu_instance.curtain.draw = MagicMock()

    # Call the draw method
    main_menu_instance.draw()

    # Verify the calls
    main_menu_instance.button_container.draw.assert_called_once_with(NATIVE_SURF)
    main_menu_instance.curtain.draw.assert_called_once_with(NATIVE_SURF, 0)
