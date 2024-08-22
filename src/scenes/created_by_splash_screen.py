from enum import auto
from enum import Enum
from typing import TYPE_CHECKING

from constants import FONT
from constants import NATIVE_HEIGHT
from constants import NATIVE_RECT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import pg
from nodes.curtain import Curtain
from nodes.state_machine import StateMachine
from nodes.timer import Timer
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class CreatedBySplashScreen:
    class State(Enum):
        JUST_ENTERED_SCENE = auto()
        OPENING_SCENE_CURTAIN = auto()
        OPENED_SCENE_CURTAIN = auto()
        CLOSING_SCENE_CURTAIN = auto()
        CLOSED_SCENE_CURTAIN = auto()

    def __init__(self, game: "Game"):
        # Initialize game
        self.game = game
        self.event_handler = self.game.event_handler

        # Colors
        self.clear_color: str = "#000000"
        self.font_color: str = "#ffffff"

        # Setups
        self._setup_curtain()
        self._setup_timers()
        self._setup_texts()
        self._setup_state_machine_update()
        self._setup_state_machine_draw()

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
        self.curtain.add_event_listener(self._on_curtain_invisible, Curtain.INVISIBLE_END)
        self.curtain.add_event_listener(self._on_curtain_opaque, Curtain.OPAQUE_END)

    def _setup_timers(self) -> None:
        """Setup timers with event listeners."""
        self.entry_delay_timer: Timer = Timer(duration=1000.0)
        self.entry_delay_timer.add_event_listener(self._on_entry_delay_timer_end, Timer.END)

        self.exit_delay_timer: Timer = Timer(duration=1000.0)
        self.exit_delay_timer.add_event_listener(self._on_exit_delay_timer_end, Timer.END)

        self.screen_time_timer: Timer = Timer(duration=1000.0)
        self.screen_time_timer.add_event_listener(self._on_screen_time_timer_end, Timer.END)

    def _setup_texts(self) -> None:
        """Setup text for title and tips."""
        self.title_text: str = "made by clifford william"
        self.title_rect: pg.Rect = FONT.get_rect(self.title_text)
        self.title_rect.center = NATIVE_RECT.center

        self.tips_text: str = "press any key to skip"
        self.tips_rect: pg.Rect = FONT.get_rect(self.tips_text)
        self.tips_rect.bottomright = NATIVE_RECT.bottomright
        self.tips_rect.x -= 1
        self.tips_rect.y -= 1

    def _setup_state_machine_update(self) -> None:
        """
        Create state machine for update.
        """

        self.state_machine_update = StateMachine(
            initial_state=CreatedBySplashScreen.State.JUST_ENTERED_SCENE,
            state_handlers={
                CreatedBySplashScreen.State.JUST_ENTERED_SCENE: self._JUST_ENTERED_SCENE,
                CreatedBySplashScreen.State.OPENING_SCENE_CURTAIN: self._OPENING_SCENE_CURTAIN,
                CreatedBySplashScreen.State.OPENED_SCENE_CURTAIN: self._SCENE_CURTAIN_OPENED,
                CreatedBySplashScreen.State.CLOSING_SCENE_CURTAIN: self._CLOSING_SCENE_CURTAIN,
                CreatedBySplashScreen.State.CLOSED_SCENE_CURTAIN: self._SCENE_CURTAIN_CLOSED,
            },
            transition_actions={
                (
                    CreatedBySplashScreen.State.JUST_ENTERED_SCENE,
                    CreatedBySplashScreen.State.OPENING_SCENE_CURTAIN,
                ): self._JUST_ENTERED_SCENE_to_OPENING_SCENE_CURTAIN,
                (
                    CreatedBySplashScreen.State.OPENING_SCENE_CURTAIN,
                    CreatedBySplashScreen.State.CLOSING_SCENE_CURTAIN,
                ): self._OPENING_SCENE_CURTAIN_to_CLOSING_SCENE_CURTAIN,
                (
                    CreatedBySplashScreen.State.OPENING_SCENE_CURTAIN,
                    CreatedBySplashScreen.State.OPENED_SCENE_CURTAIN,
                ): self._OPENING_SCENE_CURTAIN_to_SCENE_CURTAIN_OPENED,
                (
                    CreatedBySplashScreen.State.OPENED_SCENE_CURTAIN,
                    CreatedBySplashScreen.State.CLOSING_SCENE_CURTAIN,
                ): self._SCENE_CURTAIN_OPENED_to_CLOSING_SCENE_CURTAIN,
                (
                    CreatedBySplashScreen.State.CLOSING_SCENE_CURTAIN,
                    CreatedBySplashScreen.State.CLOSED_SCENE_CURTAIN,
                ): self._CLOSING_SCENE_CURTAIN_to_SCENE_CURTAIN_CLOSED,
            },
        )

    def _setup_state_machine_draw(self) -> None:
        """
        Create state machine for draw.
        """

        self.state_machine_draw = StateMachine(
            initial_state=CreatedBySplashScreen.State.JUST_ENTERED_SCENE,
            state_handlers={
                CreatedBySplashScreen.State.JUST_ENTERED_SCENE: self._SCENE_CURTAIN_CLOSED_DRAW,
                CreatedBySplashScreen.State.OPENING_SCENE_CURTAIN: self._CURTAIN_FADING_DRAW,
                CreatedBySplashScreen.State.OPENED_SCENE_CURTAIN: self._SCENE_CURTAIN_OPENED_DRAW,
                CreatedBySplashScreen.State.CLOSING_SCENE_CURTAIN: self._CURTAIN_FADING_DRAW,
                CreatedBySplashScreen.State.CLOSED_SCENE_CURTAIN: self._SCENE_CURTAIN_CLOSED_DRAW,
            },
            transition_actions={},
        )

    # State draw logics
    def _CURTAIN_FADING_DRAW(self, _dt: int) -> None:
        NATIVE_SURF.fill(self.clear_color)
        FONT.render_to(NATIVE_SURF, self.title_rect, self.title_text, self.font_color)
        FONT.render_to(NATIVE_SURF, self.tips_rect, self.tips_text, self.font_color)
        self.curtain.draw(NATIVE_SURF, 0)

    def _SCENE_CURTAIN_OPENED_DRAW(self, _dt: int) -> None:
        pass

    def _SCENE_CURTAIN_CLOSED_DRAW(self, _dt: int) -> None:
        pass

    # State update logics
    def _JUST_ENTERED_SCENE(self, dt: int) -> None:
        self.entry_delay_timer.update(dt)

    def _OPENING_SCENE_CURTAIN(self, dt: int) -> None:
        if self.event_handler.is_any_key_just_pressed:
            self.state_machine_update.change_state(CreatedBySplashScreen.State.CLOSING_SCENE_CURTAIN)
            self.state_machine_draw.change_state(CreatedBySplashScreen.State.CLOSING_SCENE_CURTAIN)
            return

        self.curtain.update(dt)

    def _SCENE_CURTAIN_OPENED(self, dt: int) -> None:
        self.screen_time_timer.update(dt)

    def _CLOSING_SCENE_CURTAIN(self, dt: int) -> None:
        self.curtain.update(dt)

    def _SCENE_CURTAIN_CLOSED(self, dt: int) -> None:
        self.exit_delay_timer.update(dt)

    # State transitions
    def _JUST_ENTERED_SCENE_to_OPENING_SCENE_CURTAIN(self) -> None:
        self.curtain.go_to_invisible()

    def _OPENING_SCENE_CURTAIN_to_CLOSING_SCENE_CURTAIN(self) -> None:
        self.curtain.go_to_opaque()

    def _OPENING_SCENE_CURTAIN_to_SCENE_CURTAIN_OPENED(self) -> None:
        pass

    def _SCENE_CURTAIN_OPENED_to_CLOSING_SCENE_CURTAIN(self) -> None:
        self.curtain.go_to_opaque()

    def _CLOSING_SCENE_CURTAIN_to_SCENE_CURTAIN_CLOSED(self) -> None:
        NATIVE_SURF.fill(self.clear_color)

    # Callbacks
    def _on_entry_delay_timer_end(self) -> None:
        self.state_machine_update.change_state(CreatedBySplashScreen.State.OPENING_SCENE_CURTAIN)
        self.state_machine_draw.change_state(CreatedBySplashScreen.State.OPENING_SCENE_CURTAIN)

    def _on_exit_delay_timer_end(self) -> None:
        self.game.set_scene("MadeWithSplashScreen")

    def _on_screen_time_timer_end(self) -> None:
        self.state_machine_update.change_state(CreatedBySplashScreen.State.CLOSING_SCENE_CURTAIN)
        self.state_machine_draw.change_state(CreatedBySplashScreen.State.CLOSING_SCENE_CURTAIN)

    def _on_curtain_invisible(self) -> None:
        self.state_machine_update.change_state(CreatedBySplashScreen.State.OPENED_SCENE_CURTAIN)
        self.state_machine_draw.change_state(CreatedBySplashScreen.State.OPENED_SCENE_CURTAIN)

    def _on_curtain_opaque(self) -> None:
        self.state_machine_update.change_state(CreatedBySplashScreen.State.CLOSED_SCENE_CURTAIN)
        self.state_machine_draw.change_state(CreatedBySplashScreen.State.CLOSED_SCENE_CURTAIN)

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
                "y": 0,
                "text": (f"created by splash screen " f"state: {self.state_machine_update.state.name}"),
            }
        )

        self.state_machine_update.handle(dt)
