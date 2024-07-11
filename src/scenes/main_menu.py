from enum import auto
from enum import Enum
from typing import TYPE_CHECKING

from constants import NATIVE_HEIGHT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import pg
from constants import PNGS_PATHS_DICT
from nodes.button import Button
from nodes.button_container import ButtonContainer
from nodes.curtain import Curtain
from nodes.state_machine import StateMachine
from nodes.timer import Timer
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class MainMenu:
    class State(Enum):
        JUST_ENTERED_SCENE = auto()
        OPENING_SCENE_CURTAIN = auto()
        OPENED_SCENE_CURTAIN = auto()
        CLOSING_SCENE_CURTAIN = auto()
        CLOSED_SCENE_CURTAIN = auto()

    def __init__(self, game: "Game"):
        # Initialize game
        self.game = game

        # Colors
        self.clear_color: str = "#000000"
        self.font_color: str = "#ffffff"

        # Curtain setup
        self._setup_curtain()

        # Timers setup
        self._setup_timers()

        # Surfs setup
        self._setup_surfs()

        # Buttons setup
        self._setup_buttons()

        # State machines for update and draw
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
        self.entry_delay_timer: Timer = Timer(duration=1000.0)
        self.entry_delay_timer.add_event_listener(self.on_entry_delay_timer_end, Timer.END)

        self.exit_delay_timer: Timer = Timer(duration=1000.0)
        self.exit_delay_timer.add_event_listener(self.on_exit_delay_timer_end, Timer.END)

    def _setup_surfs(self) -> None:
        """Setup background surf."""
        self.background_surf: pg.Surface = pg.image.load(PNGS_PATHS_DICT["main_menu_background.png"])

    def _setup_buttons(self) -> None:
        """Setup buttons."""
        self.new_game_button: Button = Button((48, 9), (30, 94), "new game", (4, 2), "start a new game")
        self.continue_button: Button = Button((48, 9), (30, 94), "continue", (4, 2), "continue from last save")
        self.options_button: Button = Button((48, 9), (30, 94), "options", (4, 2), "adjust game settings")
        self.exit_button: Button = Button((48, 9), (30, 94), "exit", (4, 2), "exit game")
        self.animation_json_generator: Button = Button(
            (48, 9), (30, 94), "animation", (4, 2), "animation json generator"
        )
        self.sprite_sheet_json_generator: Button = Button(
            (48, 9), (30, 94), "sprite", (4, 2), "sprite sheet json generator"
        )
        self.button_container: ButtonContainer = ButtonContainer(
            buttons=[
                self.new_game_button,
                self.continue_button,
                self.options_button,
                self.exit_button,
                self.animation_json_generator,
                self.sprite_sheet_json_generator,
            ],
            offset=0,
            limit=4,
            is_pagination=True,
            game=self.game,
        )
        self.button_container.add_event_listener(self.on_button_selected, ButtonContainer.BUTTON_SELECTED)
        self.selected_button: Button = self.new_game_button

    def _create_state_machine_update(self) -> StateMachine:
        """Create state machine for update."""
        return StateMachine(
            initial_state=MainMenu.State.JUST_ENTERED_SCENE,
            state_handlers={
                MainMenu.State.JUST_ENTERED_SCENE: self._JUST_ENTERED_SCENE,
                MainMenu.State.OPENING_SCENE_CURTAIN: self._OPENING_SCENE_CURTAIN,
                MainMenu.State.OPENED_SCENE_CURTAIN: self._SCENE_CURTAIN_OPENED,
                MainMenu.State.CLOSING_SCENE_CURTAIN: self._CLOSING_SCENE_CURTAIN,
                MainMenu.State.CLOSED_SCENE_CURTAIN: self._SCENE_CURTAIN_CLOSED,
            },
            transition_actions={
                (
                    MainMenu.State.JUST_ENTERED_SCENE,
                    MainMenu.State.OPENING_SCENE_CURTAIN,
                ): self._JUST_ENTERED_SCENE_to_OPENING_SCENE_CURTAIN,
                (
                    MainMenu.State.OPENING_SCENE_CURTAIN,
                    MainMenu.State.OPENED_SCENE_CURTAIN,
                ): self._OPENING_SCENE_CURTAIN_to_SCENE_CURTAIN_OPENED,
                (
                    MainMenu.State.OPENED_SCENE_CURTAIN,
                    MainMenu.State.CLOSING_SCENE_CURTAIN,
                ): self._SCENE_CURTAIN_OPENED_to_CLOSING_SCENE_CURTAIN,
                (
                    MainMenu.State.CLOSING_SCENE_CURTAIN,
                    MainMenu.State.CLOSED_SCENE_CURTAIN,
                ): self._CLOSING_SCENE_CURTAIN_to_SCENE_CURTAIN_CLOSED,
            },
        )

    def _create_state_machine_draw(self) -> StateMachine:
        """Create state machine for draw."""
        return StateMachine(
            initial_state=MainMenu.State.JUST_ENTERED_SCENE,
            state_handlers={
                MainMenu.State.JUST_ENTERED_SCENE: self._JUST_ENTERED_SCENE_DRAW,
                MainMenu.State.OPENING_SCENE_CURTAIN: self._OPENING_SCENE_CURTAIN_DRAW,
                MainMenu.State.OPENED_SCENE_CURTAIN: self._SCENE_CURTAIN_OPENED_DRAW,
                MainMenu.State.CLOSING_SCENE_CURTAIN: self._CLOSING_SCENE_CURTAIN_DRAW,
                MainMenu.State.CLOSED_SCENE_CURTAIN: self._SCENE_CURTAIN_CLOSED_DRAW,
            },
            transition_actions={},
        )

    # State draw logics
    def _JUST_ENTERED_SCENE_DRAW(self, _dt: int) -> None:
        pass

    def _OPENING_SCENE_CURTAIN_DRAW(self, _dt: int) -> None:
        NATIVE_SURF.blit(self.background_surf, (0, 0))
        self.button_container.draw(NATIVE_SURF)
        self.curtain.draw(NATIVE_SURF, 0)

    def _SCENE_CURTAIN_OPENED_DRAW(self, _dt: int) -> None:
        NATIVE_SURF.blit(self.background_surf, (0, 0))
        self.button_container.draw(NATIVE_SURF)

    def _CLOSING_SCENE_CURTAIN_DRAW(self, _dt: int) -> None:
        NATIVE_SURF.blit(self.background_surf, (0, 0))
        self.button_container.draw(NATIVE_SURF)
        self.curtain.draw(NATIVE_SURF, 0)

    def _SCENE_CURTAIN_CLOSED_DRAW(self, _dt: int) -> None:
        pass

    # State update logics
    def _JUST_ENTERED_SCENE(self, dt: int) -> None:
        self.entry_delay_timer.update(dt)

    def _OPENING_SCENE_CURTAIN(self, dt: int) -> None:
        self.curtain.update(dt)

    def _SCENE_CURTAIN_OPENED(self, dt: int) -> None:
        self.button_container.event(self.game)
        self.button_container.update(dt)

    def _CLOSING_SCENE_CURTAIN(self, dt: int) -> None:
        self.curtain.update(dt)
        self.button_container.update(dt)

    def _SCENE_CURTAIN_CLOSED(self, dt: int) -> None:
        self.exit_delay_timer.update(dt)

    # State transitions
    def _JUST_ENTERED_SCENE_to_OPENING_SCENE_CURTAIN(self) -> None:
        self.curtain.go_to_invisible()

    def _OPENING_SCENE_CURTAIN_to_SCENE_CURTAIN_OPENED(self) -> None:
        self.button_container.set_is_input_allowed(True)

    def _SCENE_CURTAIN_OPENED_to_CLOSING_SCENE_CURTAIN(self) -> None:
        self.button_container.set_is_input_allowed(False)
        self.curtain.go_to_opaque()
        # TODO: make the load screen be like the options screen.
        # TODO: let music play on load screen.
        # if self.selected_button == self.exit_button:
        # Fades out music and stop after.
        self.game.music_manager.fade_out_music(int(self.curtain.fade_duration))

    def _CLOSING_SCENE_CURTAIN_to_SCENE_CURTAIN_CLOSED(self) -> None:
        NATIVE_SURF.fill(self.clear_color)

    # Callbacks
    def on_entry_delay_timer_end(self) -> None:
        self.state_machine_update.change_state(MainMenu.State.OPENING_SCENE_CURTAIN)
        self.state_machine_draw.change_state(MainMenu.State.OPENING_SCENE_CURTAIN)

    def on_exit_delay_timer_end(self) -> None:
        if self.selected_button == self.exit_button:
            self.game.event_handler.quit()

        elif self.selected_button == self.animation_json_generator:
            self.game.set_scene("AnimationJsonGenerator")

        elif self.selected_button == self.sprite_sheet_json_generator:
            self.game.set_scene("SpriteSheetJsonGenerator")

    def on_curtain_invisible(self) -> None:
        self.state_machine_update.change_state(MainMenu.State.OPENED_SCENE_CURTAIN)
        self.state_machine_draw.change_state(MainMenu.State.OPENED_SCENE_CURTAIN)

    def on_curtain_opaque(self) -> None:
        self.state_machine_update.change_state(MainMenu.State.CLOSED_SCENE_CURTAIN)
        self.state_machine_draw.change_state(MainMenu.State.CLOSED_SCENE_CURTAIN)

    def on_button_selected(self, selected_button: Button) -> None:
        """
        Remember selected
        Need to wait for curtain to go to opaque
        Then use remembered button to switch statement to go somewhere
        """
        self.selected_button = selected_button

        if self.new_game_button == self.selected_button:
            pass

        elif self.new_game_button == self.selected_button:
            pass

        elif self.options_button == self.selected_button:
            # Update and draw options menu, stop my update
            self.game.set_is_options_menu_active(True)

        elif self.exit_button == self.selected_button:
            self.state_machine_update.change_state(MainMenu.State.CLOSING_SCENE_CURTAIN)
            self.state_machine_draw.change_state(MainMenu.State.CLOSING_SCENE_CURTAIN)

        elif self.animation_json_generator == self.selected_button:
            self.state_machine_update.change_state(MainMenu.State.CLOSING_SCENE_CURTAIN)
            self.state_machine_draw.change_state(MainMenu.State.CLOSING_SCENE_CURTAIN)

        elif self.sprite_sheet_json_generator == self.selected_button:
            self.state_machine_update.change_state(MainMenu.State.CLOSING_SCENE_CURTAIN)
            self.state_machine_draw.change_state(MainMenu.State.CLOSING_SCENE_CURTAIN)

    def draw(self) -> None:
        self.state_machine_draw.handle(0)

    def update(self, dt: int) -> None:
        # REMOVE IN BUILD
        self.game.debug_draw.add(
            {
                "type": "text",
                "layer": 6,
                "x": 0,
                "y": 6,
                "text": (f"main menu " f"state: {self.state_machine_update.state.name}"),
            }
        )

        self.state_machine_update.handle(dt)
