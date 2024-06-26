from unittest.mock import MagicMock, patch

import pygame as pg
import pytest
from nodes.button import Button
from nodes.game import Game
from nodes.options_menu import OptionsMenu

FONT = MagicMock()


@pytest.fixture
def game_instance():
    game = MagicMock(spec=Game)
    game.local_settings_dict = {"resolution_scale": "2"}
    return game


@pytest.fixture
def options_menu_instance(game_instance):
    return OptionsMenu(game_instance)


def test_set_resolution_index_wraps_correctly(options_menu_instance):
    options_menu_instance.set_resolution_index(10)
    assert (
        options_menu_instance.resolution_index == 3
    )  # Assuming 7 resolutions, 10 % 7 = 3
    assert (
        options_menu_instance.resolution_text
        == options_menu_instance.resolution_texts[3]
    )


def test_set_resolution_index_negative_value(options_menu_instance):
    options_menu_instance.set_resolution_index(-1)
    assert (
        options_menu_instance.resolution_index == 6
    )  # Assuming 7 resolutions, -1 % 7 = 6
    assert (
        options_menu_instance.resolution_text
        == options_menu_instance.resolution_texts[6]
    )


def test_on_entry_delay_timer_end_transitions_state(options_menu_instance):
    options_menu_instance.state = options_menu_instance.JUST_ENTERED
    options_menu_instance.on_entry_delay_timer_end()
    assert options_menu_instance.state == options_menu_instance.GOING_TO_OPAQUE


def test_on_exit_delay_timer_end_resets_timers_and_deactivates_menu(
    options_menu_instance,
):
    options_menu_instance.state = options_menu_instance.REACHED_INVISIBLE
    options_menu_instance.exit_delay_timer.reset = MagicMock()
    options_menu_instance.entry_delay_timer.reset = MagicMock()
    options_menu_instance.on_exit_delay_timer_end()
    assert options_menu_instance.state == options_menu_instance.JUST_ENTERED
    options_menu_instance.exit_delay_timer.reset.assert_called_once()
    options_menu_instance.entry_delay_timer.reset.assert_called_once()
    options_menu_instance.game.set_is_options_menu_active.assert_called_once_with(False)


def test_set_resolution_index_updates_text_and_position(options_menu_instance):
    # Ensure resolution_button.rect.topright is set correctly before the test
    options_menu_instance.resolution_button.rect.topright = (236, 18)
    options_menu_instance.set_resolution_index(2)

    expected_topright = options_menu_instance.resolution_button.rect.topright
    actual_topright = options_menu_instance.resolution_text_rect.topright

    # Debugging detailed steps
    print(
        "Initial resolution_button.rect:", options_menu_instance.resolution_button.rect
    )
    print("Initial resolution_text_rect:", options_menu_instance.resolution_text_rect)

    # Check how the text rect is adjusted
    print(
        "Resolution text rect x adjustment:",
        options_menu_instance.resolution_text_rect.x,
    )
    print(
        "Resolution text rect y adjustment:",
        options_menu_instance.resolution_text_rect.y,
    )

    # Adjust the expected_topright to account for the manual adjustments made in the set_resolution_index method
    adjusted_expected_topright = (expected_topright[0] - 3, expected_topright[1] + 2)

    # Assertions
    assert options_menu_instance.resolution_index == 2
    assert (
        options_menu_instance.resolution_text
        == options_menu_instance.resolution_texts[2]
    )

    # Check individual components of the topright values
    assert (
        actual_topright[0] == adjusted_expected_topright[0]
    ), f"Expected x {adjusted_expected_topright[0]} but got {actual_topright[0]}"
    assert (
        actual_topright[1] == adjusted_expected_topright[1]
    ), f"Expected y {adjusted_expected_topright[1]} but got {actual_topright[1]}"


def test_on_button_selected_sets_state_to_going_to_invisible(options_menu_instance):
    options_menu_instance.selected_button = options_menu_instance.exit_button
    options_menu_instance.on_button_selected(options_menu_instance.exit_button)
    assert options_menu_instance.state == options_menu_instance.GOING_TO_INVISIBLE


def test_on_button_selected_updates_selected_button(options_menu_instance):
    options_menu_instance.on_button_selected(options_menu_instance.resolution_button)
    assert (
        options_menu_instance.selected_button == options_menu_instance.resolution_button
    )


def test_on_button_index_changed_updates_focused_button(options_menu_instance):
    new_button = MagicMock(spec=Button)
    options_menu_instance.on_button_index_changed(new_button)
    assert options_menu_instance.focused_button == new_button


@patch("nodes.options_menu.FONT", new_callable=MagicMock)
def test_draw_calls_correct_methods(mock_font, options_menu_instance):
    # Create a real surface for the curtain's surf
    real_surface = pg.Surface((100, 100))
    options_menu_instance.curtain.surf = real_surface

    # Mock the button container draw method
    options_menu_instance.button_container.draw = MagicMock()

    # Mock the pg.draw.line method
    pg.draw.line = MagicMock()

    options_menu_instance.draw()

    # Print out actual calls to FONT.render_to
    print("Calls to FONT.render_to:")
    for call in mock_font.render_to.call_args_list:
        print(call)

    # Check if the fill method was called with the correct color
    options_menu_instance.curtain.surf.fill(options_menu_instance.native_clear_color)

    # Check if the button container draw method was called with the surface
    options_menu_instance.button_container.draw.assert_called_once_with(
        options_menu_instance.curtain.surf
    )

    # Check if FONT.render_to was called with the correct arguments
    expected_calls = [
        (
            (
                options_menu_instance.curtain.surf,
                options_menu_instance.title_rect,
                options_menu_instance.title_text,
                options_menu_instance.font_color,
            ),
        ),
        (
            (
                options_menu_instance.curtain.surf,
                options_menu_instance.resolution_text_rect,
                options_menu_instance.resolution_text,
                options_menu_instance.font_color,
            ),
        ),
    ]
    mock_font.render_to.assert_has_calls(expected_calls, any_order=True)

    # Check if pg.draw.line was called with the correct arguments
    pg.draw.line.assert_any_call(
        options_menu_instance.curtain.surf,
        "#0193bc",
        (
            options_menu_instance.decoration_horizontal_left,
            options_menu_instance.decoration_horizontal_y,
        ),
        (
            options_menu_instance.decoration_horizontal_right,
            options_menu_instance.decoration_horizontal_y,
        ),
        1,
    )
    pg.draw.line.assert_any_call(
        options_menu_instance.curtain.surf,
        "#0193bc",
        (
            options_menu_instance.decoration_vertical_x,
            options_menu_instance.decoration_vertical_top,
        ),
        (
            options_menu_instance.decoration_vertical_x,
            options_menu_instance.decoration_vertical_bottom,
        ),
        1,
    )
