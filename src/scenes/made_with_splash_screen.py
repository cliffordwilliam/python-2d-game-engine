from typing import List
from typing import TYPE_CHECKING

from constants import FONT
from constants import NATIVE_HEIGHT
from constants import NATIVE_RECT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import pg
from nodes.curtain import Curtain
from nodes.timer import Timer
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class MadeWithSplashScreen:
    """
    Fades in and out to show a text that shows my name.
    Player can skip for an early fade out if they input during fade in.

    States:
    - JUST_ENTERED.
    - GOING_TO_INVISIBLE.
    - REACHED_INVISIBLE.
    - GOING_TO_OPAQUE.
    - REACHED_OPAQUE.

    Parameters:
    - game.

    Properties:
    - game.
    - state.
    - color.
    - curtain.
    - timer.
    - text.

    Methods:
        - callbacks.
        - update:
            - state machine.
        - draw:
            - clear NATIVE_SURF.
            - title_text.
            - tips_text.
            - curtain.
        - set_state.
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
        # - Set scene.
        # - Debug draw.
        # - Events.
        self.game = game

        # Initial state.
        self.initial_state: int = self.JUST_ENTERED
        # Null to initial state.
        self.state: int = self.initial_state

        # Colors.
        self.native_clear_color: str = "#000000"
        self.font_color: str = "#ffffff"

        # Curtain.
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

        # Timers.
        # Entry delay.
        self.entry_delay_timer_duration: float = 1000
        self.entry_delay_timer: Timer = Timer(self.entry_delay_timer_duration)
        self.entry_delay_timer.add_event_listener(
            self.on_entry_delay_timer_end, Timer.END
        )
        # Exit delay.
        self.exit_delay_timer_duration: float = 1000
        self.exit_delay_timer: Timer = Timer(self.exit_delay_timer_duration)
        self.exit_delay_timer.add_event_listener(
            self.on_exit_delay_timer_end, Timer.END
        )
        # Screen time.
        self.screen_time_timer_duration: float = 1000
        self.screen_time_timer: Timer = Timer(self.screen_time_timer_duration)
        self.screen_time_timer.add_event_listener(
            self.on_screen_time_timer_end, Timer.END
        )

        # Texts.
        # Title.
        self.title_text: str = "made with python"
        self.title_rect: pg.Rect = FONT.get_rect(self.title_text)
        self.title_rect.center = NATIVE_RECT.center
        # Tips.
        self.tips_text: str = "press any key to skip"
        self.tips_rect: pg.Rect = FONT.get_rect(self.tips_text)
        self.tips_rect.bottomright = NATIVE_RECT.bottomright
        self.tips_rect.x -= 1
        self.tips_rect.y -= 1

    # Callbacks.

    def on_entry_delay_timer_end(self) -> None:
        self.set_state(self.GOING_TO_INVISIBLE)

    def on_exit_delay_timer_end(self) -> None:
        self.game.set_scene("TitleScreen")

    def on_screen_time_timer_end(self) -> None:
        self.set_state(self.GOING_TO_OPAQUE)

    def on_curtain_invisible(self) -> None:
        self.set_state(self.REACHED_INVISIBLE)

    def on_curtain_opaque(self) -> None:
        self.set_state(self.REACHED_OPAQUE)

    def draw(self) -> None:
        """
        - clear NATIVE_SURF.
        - title_text.
        - tips_text.
        - curtain.
        """

        NATIVE_SURF.fill(self.native_clear_color)
        FONT.render_to(
            NATIVE_SURF, self.title_rect, self.title_text, self.font_color
        )
        FONT.render_to(
            NATIVE_SURF, self.tips_rect, self.tips_text, self.font_color
        )
        self.curtain.draw(NATIVE_SURF, 0)

    def update(self, dt: int) -> None:
        """
        - state machine.
        """

        # REMOVE IN BUILD
        self.game.debug_draw.add(
            {
                "type": "text",
                "layer": 6,
                "x": 0,
                "y": 6,
                "text": (
                    f"made with splash screen state "
                    f"state: {self.state_names[self.state]}"
                ),
            }
        )

        if self.state == self.JUST_ENTERED:
            """
            - Counts up entry delay time.
            """
            self.entry_delay_timer.update(dt)

        elif self.state == self.GOING_TO_INVISIBLE:
            """
            - Enter pressed? Exit to GOING_TO_OPAQUE state.
            - Updates curtain alpha.
            """
            if self.game.is_any_key_just_pressed:
                self.set_state(self.GOING_TO_OPAQUE)
                return

            self.curtain.update(dt)

        elif self.state == self.REACHED_INVISIBLE:
            """
            - Counts up screen time.
            """
            self.screen_time_timer.update(dt)

        elif self.state == self.GOING_TO_OPAQUE:
            """
            - Updates curtain alpha.
            """
            self.curtain.update(dt)

        elif self.state == self.REACHED_OPAQUE:
            """
            - Counts up exit delay time.
            """
            self.exit_delay_timer.update(dt)

    def set_state(self, value: int) -> None:
        old_state: int = self.state
        self.state = value

        # From JUST_ENTERED.
        if old_state == self.JUST_ENTERED:
            # To GOING_TO_INVISIBLE.
            if self.state == self.GOING_TO_INVISIBLE:
                self.curtain.go_to_invisible()

        # From GOING_TO_INVISIBLE.
        elif old_state == self.GOING_TO_INVISIBLE:
            # To GOING_TO_OPAQUE.
            if self.state == self.GOING_TO_OPAQUE:
                self.curtain.go_to_opaque()

            # To REACHED_INVISIBLE.
            elif self.state == self.REACHED_INVISIBLE:
                pass

        # From REACHED_INVISIBLE.
        elif old_state == self.REACHED_INVISIBLE:
            # To GOING_TO_OPAQUE.
            if self.state == self.GOING_TO_OPAQUE:
                self.curtain.go_to_opaque()

        # From GOING_TO_OPAQUE.
        elif old_state == self.GOING_TO_OPAQUE:
            # To REACHED_OPAQUE.
            if self.state == self.REACHED_OPAQUE:
                NATIVE_SURF.fill("black")
