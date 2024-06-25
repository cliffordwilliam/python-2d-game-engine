from typing import List
from typing import TYPE_CHECKING

from constants import FONT
from constants import NATIVE_HEIGHT
from constants import NATIVE_RECT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import pg
from constants import PNGS_PATHS_DICT
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

    JUST_ENTERED: int = 0
    GOING_TO_INVISIBLE: int = 1
    REACHED_INVISIBLE: int = 2
    LEAVE_FADE_PROMPT: int = 3
    GOING_TO_OPAQUE: int = 4
    REACHED_OPAQUE: int = 5

    # REMOVE IN BUILD
    state_names: List = [
        "JUST_ENTERED",
        "GOING_TO_INVISIBLE",
        "REACHED_INVISIBLE",
        "LEAVE_FADE_PROMPT",
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

        self.gestalt_illusion_logo_surf: pg.Surface = pg.image.load(
            PNGS_PATHS_DICT["gestalt_illusion_logo.png"]
        )
        self.gestalt_illusion_logo_rect: pg.Rect = (
            self.gestalt_illusion_logo_surf.get_rect()
        )
        self.gestalt_illusion_logo_rect.topleft = (77, 74)

        self.prompt_text: str = "press any key to continue"
        self.prompt_rect: pg.Rect = FONT.get_rect(self.prompt_text)
        self.prompt_rect.center = NATIVE_RECT.center
        # TODO: Move magic numbers to self props
        self.prompt_rect.y = 120

        self.version_text: str = "0.x.x"
        self.version_rect: pg.Rect = FONT.get_rect(self.version_text)
        self.version_rect.bottomright = NATIVE_RECT.bottomright
        self.version_rect.x -= 1
        self.version_rect.y -= 1

        self.prompt_curtain_duration: float = 1000.0
        self.prompt_curtain_max_alpha: int = 125
        self.prompt_curtain: Curtain = Curtain(
            self.prompt_curtain_duration,
            Curtain.INVISIBLE,
            self.prompt_curtain_max_alpha,
            (self.prompt_rect.width, self.prompt_rect.height),
            True,
            "black",
        )
        self.prompt_curtain.add_event_listener(
            self.on_prompt_curtain_invisible, Curtain.INVISIBLE_END
        )
        self.prompt_curtain.add_event_listener(
            self.on_prompt_curtain_opaque, Curtain.OPAQUE_END
        )
        self.prompt_curtain.rect.center = self.prompt_rect.center

        FONT.render_to(
            self.prompt_curtain.surf,
            (0, 0),
            self.prompt_text,
            self.font_color,
        )

        self.state: int = self.initial_state

    def on_entry_delay_timer_end(self) -> None:
        self.set_state(self.GOING_TO_INVISIBLE)

    def on_exit_delay_timer_end(self) -> None:
        self.game.set_scene("MainMenu")

    def on_curtain_invisible(self) -> None:
        self.set_state(self.REACHED_INVISIBLE)

    def on_curtain_opaque(self) -> None:
        self.set_state(self.REACHED_OPAQUE)

    def on_prompt_curtain_invisible(self) -> None:
        if self.state == self.LEAVE_FADE_PROMPT:
            self.set_state(self.GOING_TO_OPAQUE)
            return

        self.prompt_curtain.go_to_opaque()

    def on_prompt_curtain_opaque(self) -> None:
        self.prompt_curtain.go_to_invisible()

    def draw(self) -> None:
        NATIVE_SURF.fill(self.native_clear_color)
        NATIVE_SURF.blit(
            self.gestalt_illusion_logo_surf,
            self.gestalt_illusion_logo_rect,
        )
        FONT.render_to(
            NATIVE_SURF,
            self.version_rect,
            self.version_text,
            self.font_color,
        )
        self.prompt_curtain.draw(NATIVE_SURF, 0)
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
                    f"title screen state "
                    f"state: {self.state_names[self.state]}"
                ),
            }
        )

        if self.state == self.JUST_ENTERED:
            self.entry_delay_timer.update(dt)

        elif self.state == self.GOING_TO_INVISIBLE:
            self.curtain.update(dt)

        elif self.state == self.REACHED_INVISIBLE:
            if self.game.is_any_key_just_pressed:
                self.set_state(self.LEAVE_FADE_PROMPT)
                return

            self.prompt_curtain.update(dt)

        elif self.state == self.LEAVE_FADE_PROMPT:
            self.prompt_curtain.update(dt)

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
                self.prompt_curtain.go_to_opaque()

        elif old_state == self.REACHED_INVISIBLE:
            if self.state == self.LEAVE_FADE_PROMPT:
                self.prompt_curtain.set_max_alpha(255)
                self.prompt_curtain.jump_to_opaque()
                self.prompt_curtain.go_to_invisible()

        elif old_state == self.LEAVE_FADE_PROMPT:
            if self.state == self.GOING_TO_OPAQUE:
                self.curtain.go_to_opaque()

        elif old_state == self.GOING_TO_OPAQUE:
            if self.state == self.REACHED_OPAQUE:
                NATIVE_SURF.fill("black")
