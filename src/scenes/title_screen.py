from enum import auto
from enum import Enum
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
from nodes.state_machine import StateMachine
from nodes.timer import Timer
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class TitleScreen:
    class State(Enum):
        JUST_ENTERED_SCENE = auto()
        OPENING_SCENE_CURTAIN = auto()
        OPENED_SCENE_CURTAIN = auto()
        LEAVE_FADE_PROMPT = auto()
        CLOSING_SCENE_CURTAIN = auto()
        CLOSED_SCENE_CURTAIN = auto()

    def __init__(self, game: "Game"):
        # Initialize game
        self.game = game
        self.game_sound_manager = self.game.sound_manager
        self.game_music_manager = self.game.music_manager
        self.game_event_handler = self.game.event_handler

        # Colors
        self.clear_color: str = "#000000"
        self.font_color: str = "#ffffff"

        # Setups
        self._setup_curtain()
        self._setup_timers()
        self._setup_surfs()
        self._setup_texts()
        self.game_music_manager.set_current_music_path(OGGS_PATHS_DICT["xdeviruchi_title_theme.ogg"])

        # State machines init
        self.state_machine_update = self._create_state_machine_update()
        self.state_machine_draw = self._create_state_machine_draw()

    # Setups
    def _setup_curtain(self) -> None:
        """Setup curtain with event listeners."""
        self.curtain: Curtain = Curtain(
            duration=1000.0,
            start_state=Curtain.OPAQUE,
            max_alpha=255,
            surf_size_tuple=(NATIVE_WIDTH, NATIVE_HEIGHT),
            is_invisible=False,
            color=self.clear_color,
        )
        self.curtain.add_event_listener(self.on_curtain_invisible, Curtain.INVISIBLE_END)
        self.curtain.add_event_listener(self.on_curtain_opaque, Curtain.OPAQUE_END)

    def _setup_timers(self) -> None:
        """Setup timers with event listeners."""
        self.entry_delay_timer: Timer = Timer(1000.0)
        self.entry_delay_timer.add_event_listener(self.on_entry_delay_timer_end, Timer.END)

        self.exit_delay_timer: Timer = Timer(1000.0)
        self.exit_delay_timer.add_event_listener(self.on_exit_delay_timer_end, Timer.END)

    def _setup_surfs(self) -> None:
        """Setup Gestalt Illusion logo."""
        self.gestalt_illusion_logo_surf: pg.Surface = pg.image.load(
            PNGS_PATHS_DICT["gestalt_illusion_logo.png"]
        ).convert_alpha()
        self.gestalt_illusion_logo_surf_topleft = (84, 76)

    def _setup_texts(self) -> None:
        """Setup text for prompt and version."""
        self.version_text: str = "0.x.x"
        self.version_rect: pg.Rect = FONT.get_rect(self.version_text)
        self.version_rect.bottomright = NATIVE_RECT.bottomright
        self.version_rect.x -= 1
        self.version_rect.y -= 1

        # To be drawn on prompt curtain
        self.prompt_text: str = "press any key to continue"
        self.prompt_rect: pg.Rect = FONT.get_rect(self.prompt_text)
        self.prompt_rect.center = NATIVE_RECT.center
        self.prompt_rect.y = 135

        self.prompt_curtain: Curtain = Curtain(
            duration=1000.0,
            start_state=Curtain.INVISIBLE,
            max_alpha=125,
            surf_size_tuple=(self.prompt_rect.width, self.prompt_rect.height),
            is_invisible=True,
            color="black",
        )
        self.prompt_curtain.add_event_listener(self.on_prompt_curtain_invisible, Curtain.INVISIBLE_END)
        self.prompt_curtain.add_event_listener(self.on_prompt_curtain_opaque, Curtain.OPAQUE_END)
        self.prompt_curtain.rect.center = self.prompt_rect.center
        FONT.render_to(
            self.prompt_curtain.surf,
            (0, 0),
            self.prompt_text,
            self.font_color,
        )

    # State machines init
    def _create_state_machine_update(self) -> StateMachine:
        """Create state machine for update."""
        return StateMachine(
            initial_state=TitleScreen.State.JUST_ENTERED_SCENE,
            state_handlers={
                TitleScreen.State.JUST_ENTERED_SCENE: self._JUST_ENTERED_SCENE,
                TitleScreen.State.OPENING_SCENE_CURTAIN: self._OPENING_SCENE_CURTAIN,
                TitleScreen.State.OPENED_SCENE_CURTAIN: self._OPENED_SCENE_CURTAIN,
                TitleScreen.State.LEAVE_FADE_PROMPT: self._LEAVE_FADE_PROMPT,
                TitleScreen.State.CLOSING_SCENE_CURTAIN: self._CLOSING_SCENE_CURTAIN,
                TitleScreen.State.CLOSED_SCENE_CURTAIN: self._CLOSED_SCENE_CURTAIN,
            },
            transition_actions={
                (
                    TitleScreen.State.JUST_ENTERED_SCENE,
                    TitleScreen.State.OPENING_SCENE_CURTAIN,
                ): self._JUST_ENTERED_SCENE_to_OPENING_SCENE_CURTAIN,
                (
                    TitleScreen.State.OPENING_SCENE_CURTAIN,
                    TitleScreen.State.OPENED_SCENE_CURTAIN,
                ): self._OPENING_SCENE_CURTAIN_to_SCENE_CURTAIN_OPENED,
                (
                    TitleScreen.State.OPENED_SCENE_CURTAIN,
                    TitleScreen.State.LEAVE_FADE_PROMPT,
                ): self._SCENE_CURTAIN_OPENED_to_LEAVE_FADE_PROMPT,
                (
                    TitleScreen.State.LEAVE_FADE_PROMPT,
                    TitleScreen.State.CLOSING_SCENE_CURTAIN,
                ): self._LEAVE_FADE_PROMPT_to_CLOSING_SCENE_CURTAIN,
                (
                    TitleScreen.State.CLOSING_SCENE_CURTAIN,
                    TitleScreen.State.CLOSED_SCENE_CURTAIN,
                ): self._CLOSING_SCENE_CURTAIN_to_SCENE_CURTAIN_CLOSED,
            },
        )

    def _create_state_machine_draw(self) -> StateMachine:
        """Create state machine for draw."""
        return StateMachine(
            initial_state=TitleScreen.State.JUST_ENTERED_SCENE,
            state_handlers={
                TitleScreen.State.JUST_ENTERED_SCENE: self._JUST_ENTERED_SCENE_DRAW,
                TitleScreen.State.OPENING_SCENE_CURTAIN: self._OPENING_SCENE_CURTAIN_DRAW,
                TitleScreen.State.OPENED_SCENE_CURTAIN: self._OPENED_SCENE_CURTAIN_DRAW,
                TitleScreen.State.LEAVE_FADE_PROMPT: self._LEAVE_FADE_PROMPT_DRAW,
                TitleScreen.State.CLOSING_SCENE_CURTAIN: self._CLOSING_SCENE_CURTAIN_DRAW,
                TitleScreen.State.CLOSED_SCENE_CURTAIN: self._CLOSED_SCENE_CURTAIN_DRAW,
            },
            transition_actions={},
        )

    # State draw logics
    def _JUST_ENTERED_SCENE_DRAW(self, _dt: int) -> None:
        pass

    def _OPENING_SCENE_CURTAIN_DRAW(self, _dt: int) -> None:
        NATIVE_SURF.fill(self.clear_color)
        NATIVE_SURF.blit(
            self.gestalt_illusion_logo_surf,
            self.gestalt_illusion_logo_surf_topleft,
        )
        FONT.render_to(
            NATIVE_SURF,
            self.version_rect,
            self.version_text,
            self.font_color,
        )
        self.curtain.draw(NATIVE_SURF, 0)

    def _OPENED_SCENE_CURTAIN_DRAW(self, _dt: int) -> None:
        NATIVE_SURF.fill(self.clear_color)
        NATIVE_SURF.blit(
            self.gestalt_illusion_logo_surf,
            self.gestalt_illusion_logo_surf_topleft,
        )
        FONT.render_to(
            NATIVE_SURF,
            self.version_rect,
            self.version_text,
            self.font_color,
        )
        self.prompt_curtain.draw(NATIVE_SURF, 0)

    def _LEAVE_FADE_PROMPT_DRAW(self, _dt: int) -> None:
        NATIVE_SURF.fill(self.clear_color)
        NATIVE_SURF.blit(
            self.gestalt_illusion_logo_surf,
            self.gestalt_illusion_logo_surf_topleft,
        )
        FONT.render_to(
            NATIVE_SURF,
            self.version_rect,
            self.version_text,
            self.font_color,
        )
        self.prompt_curtain.draw(NATIVE_SURF, 0)

    def _CLOSING_SCENE_CURTAIN_DRAW(self, _dt: int) -> None:
        NATIVE_SURF.fill(self.clear_color)
        NATIVE_SURF.blit(
            self.gestalt_illusion_logo_surf,
            self.gestalt_illusion_logo_surf_topleft,
        )
        FONT.render_to(
            NATIVE_SURF,
            self.version_rect,
            self.version_text,
            self.font_color,
        )
        self.curtain.draw(NATIVE_SURF, 0)

    def _CLOSED_SCENE_CURTAIN_DRAW(self, _dt: int) -> None:
        pass

    # State update logics
    def _JUST_ENTERED_SCENE(self, dt: int) -> None:
        self.entry_delay_timer.update(dt)

    def _OPENING_SCENE_CURTAIN(self, dt: int) -> None:
        self.curtain.update(dt)

    def _OPENED_SCENE_CURTAIN(self, dt: int) -> None:
        if self.game_event_handler.is_any_key_just_pressed:
            self.game_sound_manager.play_sound("confirm.ogg", 0, 0, 0)
            self.state_machine_update.change_state(TitleScreen.State.LEAVE_FADE_PROMPT)
            self.state_machine_draw.change_state(TitleScreen.State.LEAVE_FADE_PROMPT)
            return

        self.prompt_curtain.update(dt)

    def _LEAVE_FADE_PROMPT(self, dt: int) -> None:
        self.prompt_curtain.update(dt)

    def _CLOSING_SCENE_CURTAIN(self, dt: int) -> None:
        self.curtain.update(dt)

    def _CLOSED_SCENE_CURTAIN(self, dt: int) -> None:
        self.exit_delay_timer.update(dt)

    # State transitions
    def _JUST_ENTERED_SCENE_to_OPENING_SCENE_CURTAIN(self) -> None:
        self.curtain.go_to_invisible()
        self.game_music_manager.play_music(-1, 0.0, 0)

    def _OPENING_SCENE_CURTAIN_to_SCENE_CURTAIN_OPENED(self) -> None:
        self.prompt_curtain.go_to_opaque()

    def _SCENE_CURTAIN_OPENED_to_LEAVE_FADE_PROMPT(self) -> None:
        self.prompt_curtain.set_max_alpha(255)
        self.prompt_curtain.jump_to_opaque()
        self.prompt_curtain.go_to_invisible()

    def _LEAVE_FADE_PROMPT_to_CLOSING_SCENE_CURTAIN(self) -> None:
        self.curtain.go_to_opaque()

    def _CLOSING_SCENE_CURTAIN_to_SCENE_CURTAIN_CLOSED(self) -> None:
        pass

    # Callbacks
    def on_entry_delay_timer_end(self) -> None:
        self.state_machine_update.change_state(TitleScreen.State.OPENING_SCENE_CURTAIN)
        self.state_machine_draw.change_state(TitleScreen.State.OPENING_SCENE_CURTAIN)

    def on_exit_delay_timer_end(self) -> None:
        self.game.set_scene("MainMenu")

    def on_curtain_invisible(self) -> None:
        self.state_machine_update.change_state(TitleScreen.State.OPENED_SCENE_CURTAIN)
        self.state_machine_draw.change_state(TitleScreen.State.OPENED_SCENE_CURTAIN)

    def on_curtain_opaque(self) -> None:
        self.state_machine_update.change_state(TitleScreen.State.CLOSED_SCENE_CURTAIN)
        self.state_machine_draw.change_state(TitleScreen.State.CLOSED_SCENE_CURTAIN)

    def on_prompt_curtain_invisible(self) -> None:
        if self.state_machine_update.state == TitleScreen.State.LEAVE_FADE_PROMPT:
            self.state_machine_update.change_state(TitleScreen.State.CLOSING_SCENE_CURTAIN)
            self.state_machine_draw.change_state(TitleScreen.State.CLOSING_SCENE_CURTAIN)
            return

        self.prompt_curtain.go_to_opaque()

    def on_prompt_curtain_opaque(self) -> None:
        self.prompt_curtain.go_to_invisible()

    # Draw
    def draw(self) -> None:
        self.state_machine_draw.handle(0)

    # Update
    def update(self, dt: int) -> None:
        # REMOVE IN BUILD
        self.game.debug_draw.add(
            {
                "type": "text",
                "layer": 6,
                "x": 0,
                "y": 6,
                "text": (f"title screen " f"state: {self.state_machine_update.state.name}"),
            }
        )

        self.state_machine_update.handle(dt)
