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
    - JUST_ENTERED_SCENE.
    - OPENING_SCENE_CURTAIN.
    - SCENE_CURTAIN_OPENED.
    - CLOSING_SCENE_CURTAIN.
    - SCENE_CURTAIN_CLOSED.

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

    JUST_ENTERED_SCENE: int = 0
    OPENING_SCENE_CURTAIN: int = 1
    SCENE_CURTAIN_OPENED: int = 2
    CLOSING_SCENE_CURTAIN: int = 3
    SCENE_CURTAIN_CLOSED: int = 4

    # REMOVE IN BUILD
    state_names: List = [
        "JUST_ENTERED_SCENE",
        "OPENING_SCENE_CURTAIN",
        "SCENE_CURTAIN_OPENED",
        "CLOSING_SCENE_CURTAIN",
        "SCENE_CURTAIN_CLOSED",
    ]

    def __init__(self, game: "Game"):
        # - Set scene.
        # - Debug draw.
        # - Events.
        self.game = game

        # Initial state.
        self.initial_state: int = self.JUST_ENTERED_SCENE
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
        self.set_state(self.OPENING_SCENE_CURTAIN)

    def on_exit_delay_timer_end(self) -> None:
        self.game.set_scene("TitleScreen")

    def on_screen_time_timer_end(self) -> None:
        self.set_state(self.CLOSING_SCENE_CURTAIN)

    def on_curtain_invisible(self) -> None:
        self.set_state(self.SCENE_CURTAIN_OPENED)

    def on_curtain_opaque(self) -> None:
        self.set_state(self.SCENE_CURTAIN_CLOSED)

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
                    f"made with splash screen "
                    f"state: {self.state_names[self.state]}"
                ),
            }
        )

        if self.state == self.JUST_ENTERED_SCENE:
            """
            - Counts up entry delay time.
            """
            self.entry_delay_timer.update(dt)

        elif self.state == self.OPENING_SCENE_CURTAIN:
            """
            - Enter pressed? Exit to CLOSING_SCENE_CURTAIN state.
            - Updates curtain alpha.
            """
            if self.game.is_any_key_just_pressed:
                self.set_state(self.CLOSING_SCENE_CURTAIN)
                return

            self.curtain.update(dt)

        elif self.state == self.SCENE_CURTAIN_OPENED:
            """
            - Counts up screen time.
            """
            self.screen_time_timer.update(dt)

        elif self.state == self.CLOSING_SCENE_CURTAIN:
            """
            - Updates curtain alpha.
            """
            self.curtain.update(dt)

        elif self.state == self.SCENE_CURTAIN_CLOSED:
            """
            - Counts up exit delay time.
            """
            self.exit_delay_timer.update(dt)

    def set_state(self, value: int) -> None:
        old_state: int = self.state
        self.state = value

        # From JUST_ENTERED_SCENE.
        if old_state == self.JUST_ENTERED_SCENE:
            # To OPENING_SCENE_CURTAIN.
            if self.state == self.OPENING_SCENE_CURTAIN:
                self.curtain.go_to_invisible()

        # From OPENING_SCENE_CURTAIN.
        elif old_state == self.OPENING_SCENE_CURTAIN:
            # To CLOSING_SCENE_CURTAIN.
            if self.state == self.CLOSING_SCENE_CURTAIN:
                self.curtain.go_to_opaque()

            # To SCENE_CURTAIN_OPENED.
            elif self.state == self.SCENE_CURTAIN_OPENED:
                pass

        # From SCENE_CURTAIN_OPENED.
        elif old_state == self.SCENE_CURTAIN_OPENED:
            # To CLOSING_SCENE_CURTAIN.
            if self.state == self.CLOSING_SCENE_CURTAIN:
                self.curtain.go_to_opaque()

        # From CLOSING_SCENE_CURTAIN.
        elif old_state == self.CLOSING_SCENE_CURTAIN:
            # To SCENE_CURTAIN_CLOSED.
            if self.state == self.SCENE_CURTAIN_CLOSED:
                NATIVE_SURF.fill("black")
