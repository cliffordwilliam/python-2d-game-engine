from typing import TYPE_CHECKING

from constants import NATIVE_SURF
from constants import pg
from constants import PNGS_PATHS
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
    LEAVE_FADE_PROMPT: int = 3
    GOING_TO_OPAQUE: int = 4
    REACHED_OPAQUE: int = 5

    def __init__(self, game: "Game"):
        self.game = game

        self.initial_state: int = self.JUST_ENTERED

        self.native_clear_color: str = "#000000"
        self.font_color: str = "#ffffff"

        self.curtain_duration: float = 1000.0
        self.curtain_max_alpha: int = 255
        self.curtain: Curtain = Curtain(
            self.curtain_duration, Curtain.OPAQUE, self.curtain_max_alpha
        )
        self.curtain.add_event_listener(
            self.on_curtain_invisible, Curtain.INVISIBLE_END
        )
        self.curtain.add_event_listener(
            self.on_curtain_opaque, Curtain.OPAQUE_END
        )

        self.entry_delay_timer: Timer = Timer(1000)
        self.entry_delay_timer.add_event_listener(
            self.on_entry_delay_timer_end, Timer.END
        )

        self.exit_delay_timer: Timer = Timer(1000)
        self.exit_delay_timer.add_event_listener(
            self.on_exit_delay_timer_end, Timer.END
        )

        self.background_surf: pg.Surface = pg.image.load(
            PNGS_PATHS["main_menu_background.png"]
        )

        # Mock button
        self.new_game_button: Button = Button(
            48, 9, (30, 94), "new game", (4, 2), "start a new game"
        )
        self.continue_button: Button = Button(
            48, 9, (30, 104), "continue", (4, 2), "continue from last save"
        )
        self.load_game_button: Button = Button(
            48, 9, (30, 114), "load game", (4, 2), "select a save slot to load"
        )
        self.button_container: ButtonContainer = ButtonContainer(
            [self.new_game_button, self.continue_button, self.load_game_button]
        )

        self.state: int = self.initial_state

        self.init_state()

    def init_state(self) -> None:
        """
        This is set state for none to initial state.
        """
        self.curtain.draw()

    def on_entry_delay_timer_end(self) -> None:
        self.set_state(self.GOING_TO_INVISIBLE)

    def on_exit_delay_timer_end(self) -> None:
        self.game.quit()

    def on_curtain_invisible(self) -> None:
        self.set_state(self.REACHED_INVISIBLE)

    def on_curtain_opaque(self) -> None:
        self.set_state(self.REACHED_OPAQUE)

    def draw(self) -> None:
        NATIVE_SURF.blit(self.background_surf, (0, 0))
        self.new_game_button.draw()
        self.continue_button.draw()
        self.load_game_button.draw()
        self.curtain.draw()

    def update(self, dt: int) -> None:
        # REMOVE IN BUILD
        self.game.debug_draw.add(
            {
                "type": "text",
                "layer": 6,
                "x": 0,
                "y": 5,
                "text": f"state: {self.state}",
            }
        )

        if self.state == self.JUST_ENTERED:
            self.entry_delay_timer.update(dt)

        elif self.state == self.GOING_TO_INVISIBLE:
            self.curtain.update(dt)

        elif self.state == self.REACHED_INVISIBLE:
            self.button_container.event(self.game)

            # This only updates when they are lerping
            self.new_game_button.update(dt)
            self.continue_button.update(dt)
            self.load_game_button.update(dt)

        elif self.state == self.GOING_TO_OPAQUE:
            self.curtain.update(dt)

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
                self.curtain.go_to_opaque()

        elif old_state == self.GOING_TO_OPAQUE:
            if self.state == self.REACHED_OPAQUE:
                NATIVE_SURF.fill("black")
