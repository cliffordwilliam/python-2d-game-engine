import pytest
from nodes.game import Game
from scenes.title_screen import TitleScreen


@pytest.fixture
def game_instance():
    return Game(initial_scene="MainMenu")


@pytest.fixture
def title_screen_instance(game_instance):
    return TitleScreen(game_instance)


def test_on_curtain_invisible_listener_registered(title_screen_instance):
    curtain = title_screen_instance.curtain
    assert any(
        listener == title_screen_instance.on_curtain_invisible
        for listener in curtain.listener_invisible_ends
    )


def test_on_curtain_opaque_listener_registered(title_screen_instance):
    curtain = title_screen_instance.curtain
    assert any(
        listener == title_screen_instance.on_curtain_opaque
        for listener in curtain.listener_opaque_ends
    )


def test_on_prompt_curtain_invisible_listener_registered(title_screen_instance):
    prompt_curtain = title_screen_instance.prompt_curtain
    assert any(
        listener == title_screen_instance.on_prompt_curtain_invisible
        for listener in prompt_curtain.listener_invisible_ends
    )
