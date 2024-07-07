from typing import List
from typing import TYPE_CHECKING

from constants import FONT
from constants import NATIVE_HEIGHT
from constants import NATIVE_RECT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import OGGS_PATHS_DICT
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

    States:
    - JUST_ENTERED_SCENE.
    - OPENING_SCENE_CURTAIN.
    - SCENE_CURTAIN_OPENED.
    - LEAVE_FADE_PROMPT.
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
    - surfaces.
    - text.

    Methods:
        - callbacks.
        - update:
            - state machine.
        - draw:
            - clear NATIVE_SURF.
            - logo.
            - version_text.
            - prompt_curtain.
            - curtain.
        - set_state.
    """

    JUST_ENTERED_SCENE: int = 0
    OPENING_SCENE_CURTAIN: int = 1
    SCENE_CURTAIN_OPENED: int = 2
    LEAVE_FADE_PROMPT: int = 3
    CLOSING_SCENE_CURTAIN: int = 4
    SCENE_CURTAIN_CLOSED: int = 5

    # REMOVE IN BUILD
    state_names: List = [
        "JUST_ENTERED_SCENE",
        "OPENING_SCENE_CURTAIN",
        "SCENE_CURTAIN_OPENED",
        "LEAVE_FADE_PROMPT",
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

        # Surfaces.
        # Logo.
        self.gestalt_illusion_logo_surf: pg.Surface = pg.image.load(
            PNGS_PATHS_DICT["gestalt_illusion_logo.png"]
        )
        self.gestalt_illusion_logo_rect: pg.Rect = (
            self.gestalt_illusion_logo_surf.get_rect()
        )
        self.gestalt_illusion_logo_rect.topleft = (77, 74)

        # Texts.
        # Prompt.
        self.prompt_text: str = "press any key to continue"
        self.prompt_rect: pg.Rect = FONT.get_rect(self.prompt_text)
        self.prompt_rect.center = NATIVE_RECT.center
        self.prompt_rect.y = 120
        # Version.
        self.version_text: str = "0.x.x"
        self.version_rect: pg.Rect = FONT.get_rect(self.version_text)
        self.version_rect.bottomright = NATIVE_RECT.bottomright
        self.version_rect.x -= 1
        self.version_rect.y -= 1
        # Prompt curtain.
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

        # Load title screen music. Played in my set state.
        self.game.music_manager.set_current_music_path(
            OGGS_PATHS_DICT["xdeviruchi_title_theme.ogg"]
        )

    # Callbacks.
    def on_entry_delay_timer_end(self) -> None:
        self.set_state(self.OPENING_SCENE_CURTAIN)

    def on_exit_delay_timer_end(self) -> None:
        self.game.set_scene("MainMenu")

    def on_curtain_invisible(self) -> None:
        self.set_state(self.SCENE_CURTAIN_OPENED)

    def on_curtain_opaque(self) -> None:
        self.set_state(self.SCENE_CURTAIN_CLOSED)

    def on_prompt_curtain_invisible(self) -> None:
        # Exits to going to opaque.
        if self.state == self.LEAVE_FADE_PROMPT:
            self.set_state(self.CLOSING_SCENE_CURTAIN)
            return

        # Oscillates.
        self.prompt_curtain.go_to_opaque()

    def on_prompt_curtain_opaque(self) -> None:
        self.prompt_curtain.go_to_invisible()

    def draw(self) -> None:
        """
        - clear NATIVE_SURF.
        - logo.
        - version_text.
        - prompt_curtain.
        - curtain.
        """

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
                    f"title screen " f"state: {self.state_names[self.state]}"
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
            - Updates curtain alpha.
            """

            self.curtain.update(dt)

        elif self.state == self.SCENE_CURTAIN_OPENED:
            """
            - Enter pressed? Exit to LEAVE_FADE_PROMPT state.
            - Updates curtain alpha.
            """

            if self.game.is_any_key_just_pressed:
                # Play confirm sound.
                self.game.sound_manager.play_sound("confirm.ogg", 0, 0, 0)
                # Exit to LEAVE_FADE_PROMPT.
                self.set_state(self.LEAVE_FADE_PROMPT)
                return

            self.prompt_curtain.update(dt)

        elif self.state == self.LEAVE_FADE_PROMPT:
            """
            - Updates curtain alpha.
            """

            self.prompt_curtain.update(dt)

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
                self.game.music_manager.play_music(-1, 0.0, 0)

        # From OPENING_SCENE_CURTAIN.
        elif old_state == self.OPENING_SCENE_CURTAIN:
            # To CLOSING_SCENE_CURTAIN.
            if self.state == self.CLOSING_SCENE_CURTAIN:
                self.curtain.go_to_opaque()

            # To SCENE_CURTAIN_OPENED.
            elif self.state == self.SCENE_CURTAIN_OPENED:
                self.prompt_curtain.go_to_opaque()

        # From SCENE_CURTAIN_OPENED.
        elif old_state == self.SCENE_CURTAIN_OPENED:
            # To LEAVE_FADE_PROMPT.
            if self.state == self.LEAVE_FADE_PROMPT:
                self.prompt_curtain.set_max_alpha(255)
                self.prompt_curtain.jump_to_opaque()
                self.prompt_curtain.go_to_invisible()

        # From LEAVE_FADE_PROMPT.
        elif old_state == self.LEAVE_FADE_PROMPT:
            # To CLOSING_SCENE_CURTAIN.
            if self.state == self.CLOSING_SCENE_CURTAIN:
                self.curtain.go_to_opaque()

        # From CLOSING_SCENE_CURTAIN.
        elif old_state == self.CLOSING_SCENE_CURTAIN:
            # To SCENE_CURTAIN_CLOSED.
            if self.state == self.SCENE_CURTAIN_CLOSED:
                NATIVE_SURF.fill("black")
