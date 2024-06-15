from typing import List
from typing import TYPE_CHECKING

from constants import FONT
from constants import NATIVE_H
from constants import NATIVE_RECT
from constants import NATIVE_SURF
from constants import NATIVE_W
from constants import pg
from nodes.curtain import Curtain
from nodes.timer import Timer
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class CreatedBySplashScreen:
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
        self.curtain_surf: pg.Surface = pg.Surface((NATIVE_W, NATIVE_H))
        self.curtain_surf.fill(self.native_clear_color)
        self.curtain_is_invisible: bool = False
        self.curtain: Curtain = Curtain(
            self.curtain_duration,
            self.curtain_start,
            self.curtain_max_alpha,
            self.curtain_surf,
            self.curtain_is_invisible,
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

        self.screen_time_timer_duration: float = 1000
        self.screen_time_timer: Timer = Timer(self.screen_time_timer_duration)
        self.screen_time_timer.add_event_listener(
            self.on_screen_time_timer_end, Timer.END
        )

        self.title_text: str = "made by clifford william"
        self.title_rect: pg.Rect = FONT.get_rect(self.title_text)
        self.title_rect.center = NATIVE_RECT.center

        self.tips_text: str = (
            f"press {pg.key.name(self.game.key_bindings['enter'])} to skip"
        )
        self.tips_rect: pg.Rect = FONT.get_rect(self.tips_text)
        self.tips_rect.bottomright = NATIVE_RECT.bottomright
        self.tips_rect.x -= 1
        self.tips_rect.y -= 1

        self.state: int = self.initial_state

        self.init_state()

    def init_state(self) -> None:
        """
        This is set state for none to initial state.
        """
        self.curtain.draw(NATIVE_SURF)

    def on_entry_delay_timer_end(self) -> None:
        self.set_state(self.GOING_TO_INVISIBLE)

    def on_exit_delay_timer_end(self) -> None:
        self.game.set_scene("MadeWithSplashScreen")

    def on_screen_time_timer_end(self) -> None:
        self.set_state(self.GOING_TO_OPAQUE)

    def on_curtain_invisible(self) -> None:
        self.set_state(self.REACHED_INVISIBLE)

    def on_curtain_opaque(self) -> None:
        self.set_state(self.REACHED_OPAQUE)

    def draw(self) -> None:
        NATIVE_SURF.fill(self.native_clear_color)
        FONT.render_to(
            NATIVE_SURF, self.title_rect, self.title_text, self.font_color
        )
        FONT.render_to(
            NATIVE_SURF, self.tips_rect, self.tips_text, self.font_color
        )
        self.curtain.draw(NATIVE_SURF)

    def update(self, dt: int) -> None:
        # REMOVE IN BUILD
        self.game.debug_draw.add(
            {
                "type": "text",
                "layer": 6,
                "x": 0,
                "y": 6,
                "text": (
                    f"created by splash screen state "
                    f"state: {self.state_names[self.state]}"
                ),
            }
        )

        if self.state == self.JUST_ENTERED:
            self.entry_delay_timer.update(dt)

        elif self.state == self.GOING_TO_INVISIBLE:
            if self.game.is_enter_just_pressed:
                self.set_state(self.GOING_TO_OPAQUE)
                return

            self.curtain.update(dt)

        elif self.state == self.REACHED_INVISIBLE:
            self.screen_time_timer.update(dt)

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
            if self.state == self.GOING_TO_OPAQUE:
                self.curtain.go_to_opaque()

            elif self.state == self.REACHED_INVISIBLE:
                pass

        elif old_state == self.REACHED_INVISIBLE:
            if self.state == self.GOING_TO_OPAQUE:
                self.curtain.go_to_opaque()

        elif old_state == self.GOING_TO_OPAQUE:
            if self.state == self.REACHED_OPAQUE:
                NATIVE_SURF.fill("black")
