from typing import TYPE_CHECKING

from constants import FONT
from constants import NATIVE_RECT
from constants import NATIVE_SURF
from constants import pg
from constants import TILE_S
from nodes.curtain import Curtain
from nodes.timer import Timer
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class TitleScreen:
    """
    Fades in and out to show a text that shows my name.
    Player can skip for an early fade out if they input during fade in.
    """

    JUST_ENTERED = 0
    GOING_TO_INVISIBLE = 1
    REACHED_INVISIBLE = 2
    GOING_TO_OPAQUE = 3
    REACHED_OPAQUE = 4

    def __init__(self, game: "Game"):
        self.game = game

        self.initial_state = self.JUST_ENTERED

        self.native_clear_color: str = "#191919"
        self.font_color: str = "#fcfcfc"

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

        self.screen_time_timer: Timer = Timer(1000)
        self.screen_time_timer.add_event_listener(
            self.on_screen_time_timer_end, Timer.END
        )

        self.title_text: str = "gestalt illusion"
        self.title_rect: pg.Rect = FONT.get_rect(self.title_text)
        self.title_rect.center = NATIVE_RECT.center

        self.prompt_text: str = (
            f"press {pg.key.name(self.game.key_bindings['enter'])}"
        )
        self.prompt_rect: pg.Rect = FONT.get_rect(self.prompt_text)
        self.prompt_rect.center = NATIVE_RECT.center
        self.prompt_rect.y += TILE_S

        self.prompt_surface: pg.Surface = pg.Surface(
            (self.prompt_rect.width, self.prompt_rect.height)
        )

        self.prompt_curtain_duration: float = 1000.0
        self.prompt_curtain_max_alpha: int = 125
        self.prompt_curtain: Curtain = Curtain(
            self.prompt_curtain_duration,
            Curtain.INVISIBLE,
            self.prompt_curtain_max_alpha,
            self.prompt_surface,
            is_invisible=True,
        )
        self.prompt_curtain.add_event_listener(
            self.on_prompt_curtain_invisible, Curtain.INVISIBLE_END
        )
        self.prompt_curtain.add_event_listener(
            self.on_prompt_curtain_opaque, Curtain.OPAQUE_END
        )
        self.prompt_curtain.rect.center = self.prompt_rect.center

        FONT.render_to(
            self.prompt_curtain.surface,
            (0, 0),
            self.prompt_text,
            self.font_color,
        )

        self.state: int = self.initial_state

        self.init_state()

    def init_state(self):
        """
        This is set state for none to initial state.
        """
        self.curtain.draw()

    def on_entry_delay_timer_end(self):
        self.set_state(self.GOING_TO_INVISIBLE)

    def on_exit_delay_timer_end(self):
        self.game.quit()

    def on_screen_time_timer_end(self):
        self.set_state(self.GOING_TO_OPAQUE)

    def on_curtain_invisible(self):
        self.set_state(self.REACHED_INVISIBLE)

    def on_curtain_opaque(self):
        self.set_state(self.REACHED_OPAQUE)

    def on_prompt_curtain_invisible(self):
        self.prompt_curtain.go_to_opaque()

    def on_prompt_curtain_opaque(self):
        self.prompt_curtain.go_to_invisible()

    def draw(self):
        if self.state in [self.GOING_TO_OPAQUE, self.GOING_TO_INVISIBLE]:
            NATIVE_SURF.fill(self.native_clear_color)
            FONT.render_to(
                NATIVE_SURF, self.title_rect, self.title_text, self.font_color
            )
            self.curtain.draw()

        elif self.state == self.REACHED_INVISIBLE:
            NATIVE_SURF.fill(self.native_clear_color)
            FONT.render_to(
                NATIVE_SURF, self.title_rect, self.title_text, self.font_color
            )
            self.prompt_curtain.draw()

    def update(self, dt: int):
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
            self.prompt_curtain.update(dt)
            # TODO: start to blink prompt.
            # Use curtain and set font as curtain surf.
            pass
            # self.screen_time_timer.update(dt)

        elif self.state == self.GOING_TO_OPAQUE:
            self.curtain.update(dt)

        elif self.state == self.REACHED_OPAQUE:
            self.exit_delay_timer.update(dt)

    def set_state(self, value: int):
        old_state: int = self.state
        self.state = value

        if old_state == self.JUST_ENTERED:
            if self.state == self.GOING_TO_INVISIBLE:
                self.curtain.go_to_invisible()

        elif old_state == self.GOING_TO_INVISIBLE:
            if self.state == self.GOING_TO_OPAQUE:
                self.curtain.go_to_opaque()
            elif self.state == self.REACHED_INVISIBLE:
                self.prompt_curtain.go_to_opaque()

        elif old_state == self.REACHED_INVISIBLE:
            if self.state == self.GOING_TO_OPAQUE:
                self.curtain.go_to_opaque()

        # elif old_state == self.GOING_TO_OPAQUE:
        #     if self.state == self.REACHED_OPAQUE:
        #         print("end delay start")
