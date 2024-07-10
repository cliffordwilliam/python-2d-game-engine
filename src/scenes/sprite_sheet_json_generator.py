from typing import List
from typing import TYPE_CHECKING

from constants import NATIVE_HEIGHT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import OGGS_PATHS_DICT
from nodes.curtain import Curtain
from nodes.timer import Timer
from typeguard import typechecked

if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class SpriteSheetJsonGenerator:
    """
    Prefix the file name to be saved.
    With the sprite sheet name.
    Because for performance sake 1 json is for 1 sprite sheet.
    Asks for file name to be saved to JSONS_DIR_PATH.
    Careful for overriding data.

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
            - file_text.
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

        # Colors.
        self.native_clear_color: str = "#7f7f7f"
        self.font_color: str = "#ffffff"

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
        self.curtain.add_event_listener(self.on_curtain_invisible, Curtain.INVISIBLE_END)
        self.curtain.add_event_listener(self.on_curtain_opaque, Curtain.OPAQUE_END)

        # Timers.
        # Entry delay.
        self.entry_delay_timer_duration: float = 1000
        self.entry_delay_timer: Timer = Timer(self.entry_delay_timer_duration)
        self.entry_delay_timer.add_event_listener(self.on_entry_delay_timer_end, Timer.END)
        # Exit delay.
        self.exit_delay_timer_duration: float = 1000
        self.exit_delay_timer: Timer = Timer(self.exit_delay_timer_duration)
        self.exit_delay_timer.add_event_listener(self.on_exit_delay_timer_end, Timer.END)

        # Options after add sprites state.
        self.selected_choice_after_add_sprites_state: int = 0
        self.save_and_quit_choice_after_add_sprites_state: int = 1
        self.save_and_redo_choice_after_add_sprites_state: int = 2
        self.redo_choice_after_add_sprites_state: int = 3
        self.quit_choice_after_add_sprites_state: int = 4

        # Load editor screen music. Played in my set state.
        self.game.music_manager.set_current_music_path(
            OGGS_PATHS_DICT["xdeviruchi_take_some_rest_and_eat_some_food.ogg"]
        )
        self.game.music_manager.play_music(-1, 0.0, 0)

        # Initial state.
        self.initial_state: int = self.JUST_ENTERED_SCENE
        # Null to initial state.
        self.state: int = self.initial_state
        # State logics.
        self.state_logics: List = [
            self.just_entered_scene_state,
            self.opening_scene_curtain_state,
            self.scene_curtain_opened_state,
            self.closing_scene_curtain_state,
            self.scene_curtain_closed_state,
        ]

    # State logics.
    def just_entered_scene_state(self, dt: int) -> None:
        """
        - Counts up entry delay time.
        """

        self.entry_delay_timer.update(dt)

    def opening_scene_curtain_state(self, dt: int) -> None:
        """
        - Updates curtain alpha.
        """

        self.curtain.update(dt)

    def scene_curtain_opened_state(self, dt: int) -> None:
        """
        - asd
        """
        pass

    def closing_scene_curtain_state(self, dt: int) -> None:
        """
        - Updates curtain alpha.
        """

        self.curtain.update(dt)

    def scene_curtain_closed_state(self, dt: int) -> None:
        """
        - Counts up exit delay time.
        """

        self.exit_delay_timer.update(dt)

    # Callbacks.
    def on_entry_delay_timer_end(self) -> None:
        self.set_state(self.OPENING_SCENE_CURTAIN)

    def on_exit_delay_timer_end(self) -> None:
        # Load title screen music. Played in my set state.
        self.game.music_manager.set_current_music_path(OGGS_PATHS_DICT["xdeviruchi_title_theme.ogg"])
        self.game.music_manager.play_music(-1, 0.0, 0)
        self.game.set_scene("MainMenu")

    def on_curtain_invisible(self) -> None:
        self.set_state(self.SCENE_CURTAIN_OPENED)

    def on_curtain_opaque(self) -> None:
        self.set_state(self.SCENE_CURTAIN_CLOSED)

    def draw(self) -> None:
        """
        - clear NATIVE_SURF.
        - curtain.
        """

        # Clear.
        NATIVE_SURF.fill(self.native_clear_color)

        # Curtain.
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
                "text": (f"animation json generator " f"state: {self.state_names[self.state]}"),
            }
        )

        # All states here can go to options
        if self.game.is_pause_just_pressed:
            # Update and draw options menu, stop my update
            self.game.set_is_options_menu_active(True)

        self.state_logics[self.state](dt)

    def set_state(self, value: int) -> None:
        # TODO: Create state management.
        old_state: int = self.state
        self.state = value

        # From JUST_ENTERED_SCENE.
        if old_state == self.JUST_ENTERED_SCENE:
            # To OPENING_SCENE_CURTAIN.
            if self.state == self.OPENING_SCENE_CURTAIN:
                self.curtain.go_to_invisible()

        # From OPENING_SCENE_CURTAIN.
        elif old_state == self.OPENING_SCENE_CURTAIN:
            # To SCENE_CURTAIN_OPENED.
            if self.state == self.SCENE_CURTAIN_OPENED:
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
