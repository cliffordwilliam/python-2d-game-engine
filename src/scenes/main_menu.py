from typing import List
from typing import TYPE_CHECKING

from constants import NATIVE_HEIGHT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import pg
from constants import PNGS_PATHS_DICT
from nodes.button import Button
from nodes.button_container import ButtonContainer
from nodes.curtain import Curtain
from nodes.timer import Timer
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class MainMenu:
    """
    Fades in and out to show a text that shows my name.
    Player can skip for an early fade out if they input during fade in.
    """

    JUST_ENTERED: int = 0
    GOING_TO_INVISIBLE: int = 1
    REACHED_INVISIBLE: int = 2
    GOING_TO_OPAQUE: int = 3
    REACHED_OPAQUE: int = 4

    # REMOVE IN BUILD
    state_names: List = [
        "JUST_ENTERED",
        "GOING_TO_INVISIBLE",
        "REACHED_INVISIBLE",
        "GOING_TO_OPAQUE",
        "REACHED_OPAQUE",
    ]

    def __init__(self, game: "Game"):
        self.game = game

        self.initial_state: int = self.JUST_ENTERED

        self.native_clear_color: str = "#000000"
        self.font_color: str = "#ffffff"

        self.curtain_duration: float = 1000.0
        self.curtain_start: int = Curtain.OPAQUE
        self.curtain_max_alpha: int = 255
        self.curtain_is_invisible: bool = False
        self.curtain: Curtain = Curtain(
            self.curtain_duration,
            self.curtain_start,
            self.curtain_max_alpha,
            (NATIVE_WIDTH, NATIVE_HEIGHT),
            self.curtain_is_invisible,
            self.native_clear_color,
        )
        self.curtain.add_event_listener(
            self.on_curtain_invisible, Curtain.INVISIBLE_END
        )
        self.curtain.add_event_listener(
            self.on_curtain_opaque, Curtain.OPAQUE_END
        )

        self.entry_delay_timer_duration: float = 1000
        self.entry_delay_timer: Timer = Timer(self.entry_delay_timer_duration)
        self.entry_delay_timer.add_event_listener(
            self.on_entry_delay_timer_end, Timer.END
        )

        self.exit_delay_timer_duration: float = 1000
        self.exit_delay_timer: Timer = Timer(self.exit_delay_timer_duration)
        self.exit_delay_timer.add_event_listener(
            self.on_exit_delay_timer_end, Timer.END
        )

        self.background_surf: pg.Surface = pg.image.load(
            PNGS_PATHS_DICT["main_menu_background.png"]
        )

        self.new_game_button: Button = Button(
            (48, 9), (30, 94), "new game", (4, 2), "start a new game"
        )
        self.continue_button: Button = Button(
            (48, 9), (30, 94), "continue", (4, 2), "continue from last save"
        )
        self.options_button: Button = Button(
            (48, 9), (30, 94), "options", (4, 2), "adjust game settings"
        )
        self.exit_button: Button = Button(
            (48, 9), (30, 94), "exit", (4, 2), "exit game"
        )
        self.animation_json_generator: Button = Button(
            (48, 9), (30, 94), "animation", (4, 2), "animation json generator"
        )
        self.button_container: ButtonContainer = ButtonContainer(
            [
                self.new_game_button,
                self.continue_button,
                self.options_button,
                self.exit_button,
                self.animation_json_generator,
            ],
            0,
            4,
            True,
            self.game,
        )

        self.button_container.add_event_listener(
            self.on_button_selected, ButtonContainer.BUTTON_SELECTED
        )

        self.selected_button: Button = self.new_game_button

        self.state: int = self.initial_state

    def on_entry_delay_timer_end(self) -> None:
        self.set_state(self.GOING_TO_INVISIBLE)

    def on_exit_delay_timer_end(self) -> None:
        if self.selected_button == self.exit_button:
            self.game.quit()

        elif self.selected_button == self.animation_json_generator:
            self.game.set_scene("AnimationJsonGenerator")

    def on_curtain_invisible(self) -> None:
        self.set_state(self.REACHED_INVISIBLE)

    def on_curtain_opaque(self) -> None:
        self.set_state(self.REACHED_OPAQUE)

    def on_button_selected(self, selected_button: Button) -> None:
        """
        Remember selected
        Need to wait for curtain to go to opaque
        Then use remembered button to switch statement to go somewhere
        """
        self.selected_button = selected_button

        if self.new_game_button == self.selected_button:
            pass

        elif self.new_game_button == self.selected_button:
            pass

        elif self.options_button == self.selected_button:
            # Update and draw options menu, stop my update
            self.game.set_is_options_menu_active(True)

        elif self.exit_button == self.selected_button:
            self.set_state(self.GOING_TO_OPAQUE)

        elif self.animation_json_generator == self.selected_button:
            self.set_state(self.GOING_TO_OPAQUE)

    def draw(self) -> None:
        NATIVE_SURF.blit(self.background_surf, (0, 0))
        self.button_container.draw(NATIVE_SURF)
        self.curtain.draw(NATIVE_SURF, 0)

    def update(self, dt: int) -> None:
        # REMOVE IN BUILD
        self.game.debug_draw.add(
            {
                "type": "text",
                "layer": 6,
                "x": 0,
                "y": 6,
                "text": (
                    f"main menu state "
                    f"state: {self.state_names[self.state]}"
                ),
            }
        )

        if self.state == self.JUST_ENTERED:
            self.entry_delay_timer.update(dt)

        elif self.state == self.GOING_TO_INVISIBLE:
            self.curtain.update(dt)

        elif self.state == self.REACHED_INVISIBLE:
            self.button_container.event(self.game)
            self.button_container.update(dt)

        elif self.state == self.GOING_TO_OPAQUE:
            self.curtain.update(dt)
            self.button_container.update(dt)

        elif self.state == self.REACHED_OPAQUE:
            self.exit_delay_timer.update(dt)

    def set_state(self, value: int) -> None:
        old_state: int = self.state
        self.state = value

        if old_state == self.JUST_ENTERED:
            if self.state == self.GOING_TO_INVISIBLE:
                self.curtain.go_to_invisible()

        elif old_state == self.GOING_TO_INVISIBLE:
            if self.state == self.REACHED_INVISIBLE:
                self.button_container.set_is_input_allowed(True)

        elif old_state == self.REACHED_INVISIBLE:
            if self.state == self.GOING_TO_OPAQUE:
                self.button_container.set_is_input_allowed(False)
                self.curtain.go_to_opaque()
                # TODO: let music play on load screen.
                # if self.selected_button == self.exit_button:
                # Fades out music and stop after.
                self.game.music_manager.fade_out_music(
                    int(self.curtain_duration)
                )

        elif old_state == self.GOING_TO_OPAQUE:
            if self.state == self.REACHED_OPAQUE:
                pass
