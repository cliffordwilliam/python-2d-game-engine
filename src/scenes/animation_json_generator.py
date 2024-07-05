from typing import List
from typing import TYPE_CHECKING

from constants import FONT
from constants import FONT_HEIGHT
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
class AnimationJsonGenerator:
    """
    Fades in and out to show created by text.
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
            - file_text.
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
        self.native_clear_color: str = "#fefefe"
        self.font_color: str = "#000000"

        # Curtain.
        self.curtain_duration: float = 1000.0
        self.curtain_start: int = Curtain.OPAQUE
        self.curtain_max_alpha: int = 255
        self.curtain_is_invisible: bool = False
        self.curtain_color: str = "#000000"
        self.curtain: Curtain = Curtain(
            self.curtain_duration,
            self.curtain_start,
            self.curtain_max_alpha,
            (NATIVE_WIDTH, NATIVE_HEIGHT),
            self.curtain_is_invisible,
            self.curtain_color,
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

        # Texts.
        # File name prompt.
        self.file_name_text_prompt = (
            "type the file name to be saved, "
            f"hit {pg.key.name(self.game.local_settings_dict['enter'])} "
            "to proceed"
        )

        self.file_name_prompt_rect: pg.Rect = FONT.get_rect(
            self.file_name_text_prompt
        )
        self.file_name_prompt_rect.center = NATIVE_RECT.center
        self.file_name_prompt_rect.y -= FONT_HEIGHT + 1
        # File name.
        self.file_name_text: str = ""
        self.file_name_rect: pg.Rect = FONT.get_rect(self.file_name_text)
        self.file_name_rect.center = NATIVE_RECT.center

    # Callbacks.
    def on_entry_delay_timer_end(self) -> None:
        self.set_state(self.GOING_TO_INVISIBLE)

    def on_exit_delay_timer_end(self) -> None:
        self.game.set_scene("MadeWithSplashScreen")

    def on_curtain_invisible(self) -> None:
        self.set_state(self.REACHED_INVISIBLE)

    def on_curtain_opaque(self) -> None:
        self.set_state(self.REACHED_OPAQUE)

    def draw(self) -> None:
        """
        - clear NATIVE_SURF.
        - file_text.
        - tips_text.
        - curtain.
        """

        NATIVE_SURF.fill(self.native_clear_color)
        FONT.render_to(
            NATIVE_SURF,
            self.file_name_prompt_rect,
            self.file_name_text_prompt,
            self.font_color,
        )
        FONT.render_to(
            NATIVE_SURF,
            self.file_name_rect,
            self.file_name_text,
            self.font_color,
        )
        self.curtain.draw(NATIVE_SURF, 0)

    def set_file_name_text(self, value: str) -> None:
        self.file_name_text = value
        self.file_name_rect = FONT.get_rect(self.file_name_text)
        self.file_name_rect.center = NATIVE_RECT.center

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
                    f"animation json generator state"
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
            - Updates curtain alpha.
            """

            self.curtain.update(dt)

        elif self.state == self.REACHED_INVISIBLE:
            """
            - Get user input for file name.
            """
            if self.game.this_frame_event:
                if self.game.this_frame_event.type == pg.KEYDOWN:
                    if self.game.this_frame_event.key == pg.K_RETURN:
                        print(self.file_name_text)
                        new_value: str = ""
                        self.set_file_name_text(new_value)
                    elif self.game.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.file_name_text[:-1]
                        self.set_file_name_text(new_value)
                    else:
                        new_value = (
                            self.file_name_text
                            + self.game.this_frame_event.unicode
                        )
                        self.set_file_name_text(new_value)

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
            # To REACHED_INVISIBLE.
            if self.state == self.REACHED_INVISIBLE:
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
