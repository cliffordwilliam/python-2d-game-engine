from unittest.mock import MagicMock, patch

import pytest
from nodes.game import Game
from scenes.made_with_splash_screen import MadeWithSplashScreen


@pytest.fixture
def game_instance():
    return Game(initial_scene="MainMenu")


@pytest.fixture
def splash_screen_instance(game_instance):
    return MadeWithSplashScreen(game_instance)


def test_on_curtain_invisible_sets_state_to_reached_invisible(splash_screen_instance):
    splash_screen_instance.on_curtain_invisible()
    assert splash_screen_instance.state == MadeWithSplashScreen.REACHED_INVISIBLE


def test_on_curtain_opaque_sets_state_to_reached_opaque(splash_screen_instance):
    splash_screen_instance.on_curtain_opaque()
    assert splash_screen_instance.state == MadeWithSplashScreen.REACHED_OPAQUE


def test_set_state_to_going_to_opaque_triggers_curtain(splash_screen_instance):
    with patch.object(
        splash_screen_instance.curtain, "go_to_opaque"
    ) as mock_go_to_opaque:
        print("Current state before setting:", splash_screen_instance.state)
        # Set state to REACHED_INVISIBLE first to simulate the correct transition
        splash_screen_instance.set_state(MadeWithSplashScreen.REACHED_INVISIBLE)
        print(
            "Current state after setting to REACHED_INVISIBLE:",
            splash_screen_instance.state,
        )
        # Now set state to GOING_TO_OPAQUE
        splash_screen_instance.set_state(MadeWithSplashScreen.GOING_TO_OPAQUE)
        print(
            "Current state after setting to GOING_TO_OPAQUE:",
            splash_screen_instance.state,
        )
        assert splash_screen_instance.state == MadeWithSplashScreen.GOING_TO_OPAQUE
        mock_go_to_opaque.assert_called_once()


def test_on_entry_delay_timer_end_sets_state_to_going_to_invisible(
    splash_screen_instance,
):
    splash_screen_instance.on_entry_delay_timer_end()
    assert splash_screen_instance.state == MadeWithSplashScreen.GOING_TO_INVISIBLE


def test_on_exit_delay_timer_end_sets_scene_to_title_screen(splash_screen_instance):
    with patch.object(splash_screen_instance.game, "set_scene") as mock_set_scene:
        splash_screen_instance.on_exit_delay_timer_end()
        mock_set_scene.assert_called_once_with("TitleScreen")


def test_on_screen_time_timer_end_sets_state_to_going_to_opaque(splash_screen_instance):
    splash_screen_instance.on_screen_time_timer_end()
    assert splash_screen_instance.state == MadeWithSplashScreen.GOING_TO_OPAQUE


def test_draw_calls_fill_and_render_to(splash_screen_instance):
    mock_surface = MagicMock()
    mock_font = MagicMock()

    with patch("pygame.Surface", return_value=mock_surface), patch(
        "constants.FONT", mock_font
    ), patch.object(
        splash_screen_instance.curtain, "draw", new_callable=MagicMock
    ) as mock_curtain_draw, patch(
        "scenes.made_with_splash_screen.NATIVE_SURF", mock_surface
    ), patch(
        "scenes.made_with_splash_screen.FONT", mock_font
    ):

        # Add print statements to trace execution
        print(
            f"Before calling draw: NATIVE_SURF.fill call count: {mock_surface.fill.call_count}"
        )

        splash_screen_instance.draw()

        print(
            f"After calling draw: NATIVE_SURF.fill call count: {mock_surface.fill.call_count}"
        )

        mock_surface.fill.assert_called_once_with(
            splash_screen_instance.native_clear_color
        )
        assert mock_font.render_to.call_count == 2
        mock_curtain_draw.assert_called_once_with(mock_surface, 0)


def test_update_just_entered_updates_entry_delay_timer(splash_screen_instance):
    with patch.object(
        splash_screen_instance.entry_delay_timer, "update"
    ) as mock_update:
        splash_screen_instance.state = MadeWithSplashScreen.JUST_ENTERED
        splash_screen_instance.update(100)
        mock_update.assert_called_once_with(100)


def test_update_going_to_invisible_updates_curtain(splash_screen_instance):
    with patch.object(splash_screen_instance.curtain, "update") as mock_update:
        splash_screen_instance.state = MadeWithSplashScreen.GOING_TO_INVISIBLE
        splash_screen_instance.update(100)
        mock_update.assert_called_once_with(100)


def test_update_reached_invisible_updates_screen_time_timer(splash_screen_instance):
    with patch.object(
        splash_screen_instance.screen_time_timer, "update"
    ) as mock_update:
        splash_screen_instance.state = MadeWithSplashScreen.REACHED_INVISIBLE
        splash_screen_instance.update(100)
        mock_update.assert_called_once_with(100)


def test_update_going_to_opaque_updates_curtain(splash_screen_instance):
    with patch.object(splash_screen_instance.curtain, "update") as mock_update:
        splash_screen_instance.state = MadeWithSplashScreen.GOING_TO_OPAQUE
        splash_screen_instance.update(100)
        mock_update.assert_called_once_with(100)


def test_update_reached_opaque_updates_exit_delay_timer(splash_screen_instance):
    with patch.object(splash_screen_instance.exit_delay_timer, "update") as mock_update:
        splash_screen_instance.state = MadeWithSplashScreen.REACHED_OPAQUE
        splash_screen_instance.update(100)
        mock_update.assert_called_once_with(100)
