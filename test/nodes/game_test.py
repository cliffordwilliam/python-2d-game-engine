from unittest.mock import call, mock_open, patch

import pygame as pg
import pytest
from constants import (
    DEFAULT_SETTINGS_DICT,
    JSONS_PATHS_DICT,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from nodes.game import Game
from scenes.created_by_splash_screen import CreatedBySplashScreen
from scenes.made_with_splash_screen import MadeWithSplashScreen
from scenes.main_menu import MainMenu
from scenes.title_screen import TitleScreen


@pytest.fixture
def game_instance():
    return Game(initial_scene="MainMenu")


def test_sync_local_saves_with_disk_saves(game_instance):
    game_instance.local_settings_dict = {"resolution_scale": "4"}
    expected_calls = [
        call("{"),
        call('"resolution_scale"'),
        call(": "),
        call('"4"'),
        call("}"),
    ]
    with patch("builtins.open", mock_open()) as mocked_file:
        game_instance.sync_local_saves_with_disk_saves()
        mocked_file.assert_called_once_with(JSONS_PATHS_DICT["settings.json"], "w")
        assert mocked_file().write.call_args_list == expected_calls


def test_set_is_options_menu_active(game_instance):
    game_instance.set_is_options_menu_active(True)
    assert game_instance.is_options_menu_active is True


def test_set_scene_main_menu(game_instance):
    game_instance.set_scene("MainMenu")
    assert isinstance(game_instance.current_scene, MainMenu)


def test_set_scene_title_screen(game_instance):
    game_instance.set_scene("TitleScreen")
    assert isinstance(game_instance.current_scene, TitleScreen)


def test_set_scene_made_with_splash_screen(game_instance):
    game_instance.set_scene("MadeWithSplashScreen")
    assert isinstance(game_instance.current_scene, MadeWithSplashScreen)


def test_set_scene_created_by_splash_screen(game_instance):
    game_instance.set_scene("CreatedBySplashScreen")
    assert isinstance(game_instance.current_scene, CreatedBySplashScreen)


def test_init_window_resolution():
    game = Game(initial_scene="MainMenu")
    assert game.resolution_scale == int(DEFAULT_SETTINGS_DICT["resolution_scale"])
    assert game.window_width == game.resolution_scale * WINDOW_WIDTH
    assert game.window_height == game.resolution_scale * WINDOW_HEIGHT


def test_set_resolution(game_instance):
    game_instance.set_resolution(5)
    assert game_instance.resolution_scale == 5
    assert (
        game_instance.window_width == 5 * WINDOW_WIDTH
    )  # Assuming WINDOW_WIDTH is 800
    assert (
        game_instance.window_height == 5 * WINDOW_HEIGHT
    )  # Assuming WINDOW_HEIGHT is 600
    assert game_instance.local_settings_dict["resolution_scale"] == "5"


def test_set_resolution_scale_1(game_instance):
    game_instance.set_resolution(1)
    assert game_instance.resolution_scale == 1
    assert game_instance.window_width == 1 * WINDOW_WIDTH
    assert game_instance.window_height == 1 * WINDOW_HEIGHT
    assert game_instance.local_settings_dict["resolution_scale"] == "1"
    assert not (game_instance.window_surf.get_flags() & pg.FULLSCREEN)


@patch("pygame.quit")
@patch("builtins.exit")
def test_quit(mock_exit, mock_pg_quit, game_instance):
    game_instance.quit()
    mock_pg_quit.assert_called_once()
    mock_exit.assert_called_once()


def test_event_keydown_up(game_instance):
    event = pg.event.Event(pg.KEYDOWN, {"key": pg.K_UP})
    game_instance.event(event)
    assert game_instance.is_up_pressed is True
    assert game_instance.is_up_just_pressed is True


def test_event_keyup_up(game_instance):
    event = pg.event.Event(pg.KEYUP, {"key": pg.K_UP})
    game_instance.event(event)
    assert game_instance.is_up_pressed is False
    assert game_instance.is_up_just_released is True


def test_reset_just_events(game_instance):
    game_instance.is_up_just_pressed = True
    game_instance.is_up_just_released = True
    game_instance.reset_just_events()
    assert game_instance.is_up_just_pressed is False
    assert game_instance.is_up_just_released is False


@patch("json.load", return_value={"resolution_scale": "2"})
@patch("builtins.open", new_callable=mock_open, read_data='{"resolution_scale": "2"}')
def test_init_loads_settings_from_file(mock_open, mock_json_load):
    game = Game(initial_scene="MainMenu")

    # Checking that open was called correctly
    expected_call = call(JSONS_PATHS_DICT["settings.json"], "r")
    actual_call = mock_open.call_args

    assert expected_call == actual_call or actual_call == call(
        JSONS_PATHS_DICT["settings.json"]
    ), f"Expected call: {expected_call}, but got: {actual_call}"

    # Checking that json.load was called once
    mock_json_load.assert_called_once()

    # Verify the settings are loaded correctly
    assert game.local_settings_dict["resolution_scale"] == "2"
