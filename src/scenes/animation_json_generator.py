from enum import auto
from enum import Enum
from os.path import exists
from os.path import join
from pathlib import Path
from typing import Callable
from typing import TYPE_CHECKING

from constants import FONT
from constants import FONT_HEIGHT
from constants import JSONS_REPO_DIR_PATH
from constants import NATIVE_HEIGHT
from constants import NATIVE_RECT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import NATIVE_WIDTH_TU
from constants import OGGS_PATHS_DICT
from constants import pg
from constants import TILE_SIZE
from nodes.camera import Camera
from nodes.curtain import Curtain
from nodes.state_machine import StateMachine
from nodes.timer import Timer
from pygame.math import clamp
from pygame.math import Vector2
from schemas import ANIMATION_SCHEMA
from schemas import validate_json
from typeguard import typechecked

if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class AnimationJsonGenerator:
    SLOW_FADE_DURATION = 1000.0
    FAST_FADE_DURATION = 250.0

    class State(Enum):
        JUST_ENTERED_SCENE = auto()
        OPENING_SCENE_CURTAIN = auto()
        OPENED_SCENE_CURTAIN = auto()
        SPRITE_SHEET_PNG_PATH_QUERY = auto()
        SPRITE_SIZE_QUERY = auto()
        SPRITE_WIDTH_QUERY = auto()
        ANIMATION_NAME_QUERY = auto()
        LOOP_QUERY = auto()
        NEXT_ANIMATION_QUERY = auto()
        DURATION_QUERY = auto()
        ADD_SPRITES = auto()
        SAVE_QUIT_REDO_QUERY = auto()
        CLOSING_SCENE_CURTAIN = auto()
        CLOSED_SCENE_CURTAIN = auto()

    def __init__(self, game: "Game"):
        # Initialize game
        self.game = game
        self.game_event_handler = self.game.event_handler
        self.game_sound_manager = self.game.sound_manager
        self.game_music_manager = self.game.music_manager

        # Colors
        self.clear_color: str = "#7f7f7f"
        self.grid_line_color: str = "#999999"
        self.font_color: str = "#ffffff"

        # Setups
        self._setup_curtain()
        self._setup_timers()
        self._setup_texts()
        self._setup_user_input_store()
        self._setup_camera()
        self._setup_mouse_positions()
        self._setup_collision_map()
        self._setup_surfs()
        self._setup_loop_options()
        self._setup_music()
        self._setup_state_machine_update()
        self._setup_state_machine_draw()

        # If image is smaller than camera no need to move camera
        self.is_sprite_sheet_smaller_than_camera: bool = True

    ##########
    # SETUPS #
    ##########
    def _setup_curtain(self) -> None:
        """Setup curtain with event listeners."""
        self.curtain: Curtain = Curtain(
            duration=self.SLOW_FADE_DURATION,
            start_state=Curtain.OPAQUE,
            max_alpha=255,
            surf_size_tuple=(NATIVE_WIDTH, NATIVE_HEIGHT),
            is_invisible=False,
            color="#000000",
        )
        self.curtain.add_event_listener(self._on_curtain_invisible, Curtain.INVISIBLE_END)
        self.curtain.add_event_listener(self._on_curtain_opaque, Curtain.OPAQUE_END)

    def _setup_timers(self) -> None:
        """Setup timers with event listeners."""
        self.entry_delay_timer: Timer = Timer(duration=self.SLOW_FADE_DURATION)
        self.entry_delay_timer.add_event_listener(self._on_entry_delay_timer_end, Timer.END)

        self.exit_delay_timer: Timer = Timer(duration=self.SLOW_FADE_DURATION)
        self.exit_delay_timer.add_event_listener(self._on_exit_delay_timer_end, Timer.END)

    def _setup_texts(self) -> None:
        """Setup text for title and tips."""
        self.prompt_text: str = ""
        self.prompt_rect: pg.Rect = FONT.get_rect(self.prompt_text)

        self.input_text: str = ""
        self.input_rect: pg.Rect = FONT.get_rect(self.input_text)
        self.input_rect.center = NATIVE_RECT.center

    def _setup_user_input_store(self) -> None:
        """Store user inputs"""
        self.file_name: str = ""
        self.animation_sprite_height: int = TILE_SIZE
        self.animation_sprite_height_tu: int = int(self.animation_sprite_height // TILE_SIZE)
        self.animation_sprite_width: int = TILE_SIZE
        self.animation_sprite_width_tu: int = int(self.animation_sprite_width // TILE_SIZE)
        self.animation_name: str = ""
        self.animation_is_loop: int = 0
        self.next_animation_name: str = ""
        self.animation_duration: int = 0

        # Sprite sheet surf metadata
        self.sprite_sheet_png_path: (None | str) = None
        self.sprite_sheet_surf: (None | pg.Surface) = None
        self.sprite_sheet_rect: (None | pg.Rect) = None

        # To be saved JSON
        self.local_animation_json: dict = {}
        self.local_animation_sprites_list: list = []

    def _setup_camera(self) -> None:
        self.camera_anchor_vector: Vector2 = Vector2(0.0, 0.0)
        self.camera: Camera = Camera(
            self.camera_anchor_vector,
            # REMOVE IN BUILD
            self.game.debug_draw,
        )
        self.camera_speed: float = 0.09  # Px / ms

    def _setup_mouse_positions(self) -> None:
        self.world_mouse_x: float = 0.0
        self.world_mouse_y: float = 0.0
        self.world_mouse_tu_x: int = 0
        self.world_mouse_tu_y: int = 0
        self.world_mouse_snapped_x: int = 0
        self.world_mouse_snapped_y: int = 0
        self.screen_mouse_x: float = 0.0
        self.screen_mouse_y: float = 0.0

    def _setup_collision_map(self) -> None:
        self.room_collision_map_list: list[int] = []
        self.room_collision_map_width_tu: int = 0
        self.room_collision_map_height_tu: int = 0

    def _setup_surfs(self) -> None:
        # Selected surf marker
        self.selected_surf_marker: pg.Surface = pg.Surface((TILE_SIZE, TILE_SIZE))
        self.selected_surf_marker.fill("red")

        # Grid surf
        self.grid_horizontal_line_surf: pg.Surface = pg.Surface((NATIVE_WIDTH, 1))
        self.grid_horizontal_line_surf.fill("black")
        self.grid_horizontal_line_surf.set_alpha(21)
        self.grid_vertical_line_surf: pg.Surface = pg.Surface((1, NATIVE_HEIGHT))
        self.grid_vertical_line_surf.fill("black")
        self.grid_vertical_line_surf.set_alpha(21)

    def _setup_loop_options(self) -> None:
        """
        Save, quit and redo option at final state.
        """

        # This one stores the selected option
        self.selected_choice_after_add_sprites_state: int = 0
        # These are the options
        self.save_and_quit_choice_after_add_sprites_state: int = 1
        self.save_and_redo_choice_after_add_sprites_state: int = 2
        self.redo_choice_after_add_sprites_state: int = 3
        self.quit_choice_after_add_sprites_state: int = 4

    def _setup_music(self) -> None:
        # Load editor screen music. Played in my set state
        self.game_music_manager.set_current_music_path(OGGS_PATHS_DICT["xdeviruchi_take_some_rest_and_eat_some_food.ogg"])
        self.game_music_manager.play_music(-1, 0.0, 0)

    def _setup_state_machine_update(self) -> None:
        """
        Create state machine for update.
        """

        self.state_machine_update = StateMachine(
            initial_state=AnimationJsonGenerator.State.JUST_ENTERED_SCENE,
            state_handlers={
                AnimationJsonGenerator.State.JUST_ENTERED_SCENE: self._JUST_ENTERED_SCENE,
                AnimationJsonGenerator.State.OPENING_SCENE_CURTAIN: self._OPENING_SCENE_CURTAIN,
                AnimationJsonGenerator.State.OPENED_SCENE_CURTAIN: self._OPENED_SCENE_CURTAIN,
                AnimationJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY: self._SPRITE_SHEET_PNG_PATH_QUERY,
                AnimationJsonGenerator.State.SPRITE_SIZE_QUERY: self._SPRITE_SIZE_QUERY,
                AnimationJsonGenerator.State.SPRITE_WIDTH_QUERY: self._SPRITE_WIDTH_QUERY,
                AnimationJsonGenerator.State.ANIMATION_NAME_QUERY: self._ANIMATION_NAME_QUERY,
                AnimationJsonGenerator.State.LOOP_QUERY: self._LOOP_QUERY,
                AnimationJsonGenerator.State.NEXT_ANIMATION_QUERY: self._NEXT_ANIMATION_QUERY,
                AnimationJsonGenerator.State.DURATION_QUERY: self._DURATION_QUERY,
                AnimationJsonGenerator.State.ADD_SPRITES: self._ADD_SPRITES,
                AnimationJsonGenerator.State.SAVE_QUIT_REDO_QUERY: self._SAVE_QUIT_REDO_QUERY,
                AnimationJsonGenerator.State.CLOSING_SCENE_CURTAIN: self._CLOSING_SCENE_CURTAIN,
                AnimationJsonGenerator.State.CLOSED_SCENE_CURTAIN: self._CLOSED_SCENE_CURTAIN,
            },
            transition_actions={
                (
                    AnimationJsonGenerator.State.JUST_ENTERED_SCENE,
                    AnimationJsonGenerator.State.OPENING_SCENE_CURTAIN,
                ): self._JUST_ENTERED_SCENE_to_OPENING_SCENE_CURTAIN,
                (
                    AnimationJsonGenerator.State.OPENING_SCENE_CURTAIN,
                    AnimationJsonGenerator.State.OPENED_SCENE_CURTAIN,
                ): self._OPENING_SCENE_CURTAIN_to_OPENED_SCENE_CURTAIN,
                (
                    AnimationJsonGenerator.State.OPENED_SCENE_CURTAIN,
                    AnimationJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY,
                ): self._OPENED_SCENE_CURTAIN_to_SPRITE_SHEET_PNG_PATH_QUERY,
                (
                    AnimationJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY,
                    AnimationJsonGenerator.State.SPRITE_SIZE_QUERY,
                ): self._SPRITE_SHEET_PNG_PATH_QUERY_to_SPRITE_SIZE_QUERY,
                (
                    AnimationJsonGenerator.State.SPRITE_SIZE_QUERY,
                    AnimationJsonGenerator.State.SPRITE_WIDTH_QUERY,
                ): self._SPRITE_SIZE_QUERY_to_SPRITE_WIDTH_QUERY,
                (
                    AnimationJsonGenerator.State.SPRITE_WIDTH_QUERY,
                    AnimationJsonGenerator.State.ANIMATION_NAME_QUERY,
                ): self._SPRITE_WIDTH_QUERY_to_ANIMATION_NAME_QUERY,
                (
                    AnimationJsonGenerator.State.ANIMATION_NAME_QUERY,
                    AnimationJsonGenerator.State.LOOP_QUERY,
                ): self._ANIMATION_NAME_QUERY_to_LOOP_QUERY,
                (
                    AnimationJsonGenerator.State.LOOP_QUERY,
                    AnimationJsonGenerator.State.NEXT_ANIMATION_QUERY,
                ): self._LOOP_QUERY_to_NEXT_ANIMATION_QUERY,
                (
                    AnimationJsonGenerator.State.NEXT_ANIMATION_QUERY,
                    AnimationJsonGenerator.State.DURATION_QUERY,
                ): self._NEXT_ANIMATION_QUERY_to_DURATION_QUERY,
                (
                    AnimationJsonGenerator.State.DURATION_QUERY,
                    AnimationJsonGenerator.State.ADD_SPRITES,
                ): self._DURATION_QUERY_to_ADD_SPRITES,
                (
                    AnimationJsonGenerator.State.ADD_SPRITES,
                    AnimationJsonGenerator.State.SAVE_QUIT_REDO_QUERY,
                ): self._ADD_SPRITES_to_SAVE_QUIT_REDO_QUERY,
                (
                    AnimationJsonGenerator.State.SAVE_QUIT_REDO_QUERY,
                    AnimationJsonGenerator.State.ANIMATION_NAME_QUERY,
                ): self._SAVE_QUIT_REDO_QUERY_to_ANIMATION_NAME_QUERY,
                (
                    AnimationJsonGenerator.State.SAVE_QUIT_REDO_QUERY,
                    AnimationJsonGenerator.State.ADD_SPRITES,
                ): self._SAVE_QUIT_REDO_QUERY_to_ADD_SPRITES,
                (
                    AnimationJsonGenerator.State.CLOSING_SCENE_CURTAIN,
                    AnimationJsonGenerator.State.CLOSED_SCENE_CURTAIN,
                ): self._CLOSING_SCENE_CURTAIN_to_CLOSED_SCENE_CURTAIN,
            },
        )

    def _setup_state_machine_draw(self) -> None:
        """
        Create state machine for draw.
        """

        self.state_machine_draw = StateMachine(
            initial_state=AnimationJsonGenerator.State.JUST_ENTERED_SCENE,
            state_handlers={
                AnimationJsonGenerator.State.JUST_ENTERED_SCENE: self._NOTHING,
                AnimationJsonGenerator.State.OPENING_SCENE_CURTAIN: self._QUERIES,
                AnimationJsonGenerator.State.OPENED_SCENE_CURTAIN: self._QUERIES,
                AnimationJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY: self._QUERIES,
                AnimationJsonGenerator.State.SPRITE_SIZE_QUERY: self._QUERIES,
                AnimationJsonGenerator.State.SPRITE_WIDTH_QUERY: self._QUERIES,
                AnimationJsonGenerator.State.ANIMATION_NAME_QUERY: self._QUERIES,
                AnimationJsonGenerator.State.LOOP_QUERY: self._QUERIES,
                AnimationJsonGenerator.State.NEXT_ANIMATION_QUERY: self._QUERIES,
                AnimationJsonGenerator.State.DURATION_QUERY: self._QUERIES,
                AnimationJsonGenerator.State.ADD_SPRITES: self._ADD_SPRITES_DRAW,
                AnimationJsonGenerator.State.SAVE_QUIT_REDO_QUERY: self._QUERIES,
                AnimationJsonGenerator.State.CLOSING_SCENE_CURTAIN: self._QUERIES,
                AnimationJsonGenerator.State.CLOSED_SCENE_CURTAIN: self._NOTHING,
            },
            transition_actions={},
        )

    #####################
    # STATE DRAW LOGICS #
    #####################
    def _NOTHING(self, _dt: int) -> None:
        pass

    def _QUERIES(self, _dt: int) -> None:
        # Clear
        NATIVE_SURF.fill(self.clear_color)
        # Draw grid with camera offset
        self._draw_grid()
        # Draw prompt and input
        FONT.render_to(
            NATIVE_SURF,
            self.prompt_rect,
            self.prompt_text,
            self.font_color,
        )
        FONT.render_to(
            NATIVE_SURF,
            self.input_rect,
            self.input_text,
            self.font_color,
        )
        # Curtain
        self.curtain.draw(NATIVE_SURF, 0)

    def _ADD_SPRITES_DRAW(self, _dt: int) -> None:
        # Clear
        NATIVE_SURF.fill(self.clear_color)

        # Draw selected sprite sheet with camera offset
        if self.sprite_sheet_surf is not None:
            NATIVE_SURF.blit(
                self.sprite_sheet_surf,
                (
                    -self.camera.rect.x,
                    -self.camera.rect.y,
                ),
            )

        # Draw grid
        self._draw_grid()

        # Draw cursor
        # Get mouse position
        mouse_position_tuple: tuple[int, int] = pg.mouse.get_pos()
        mouse_position_x_tuple: int = mouse_position_tuple[0]
        mouse_position_y_tuple: int = mouse_position_tuple[1]
        # Scale mouse position
        mouse_position_x_tuple_scaled: int | float = (
            mouse_position_x_tuple // self.game.local_settings_metadata_instance.resolution_scale
        )
        mouse_position_y_tuple_scaled: int | float = (
            mouse_position_y_tuple // self.game.local_settings_metadata_instance.resolution_scale
        )
        # Keep mouse inside scaled NATIVE_RECT
        mouse_position_x_tuple_scaled = clamp(
            mouse_position_x_tuple_scaled,
            NATIVE_RECT.left,
            # Because this will refer to top left of a cell
            # If it is flushed to the right it is out of bound
            NATIVE_RECT.right - 1,
        )
        mouse_position_y_tuple_scaled = clamp(
            mouse_position_y_tuple_scaled,
            NATIVE_RECT.top,
            # Because this will refer to top left of a cell
            # If it is flushed to the bottom it is out of bound
            NATIVE_RECT.bottom - 1,
        )
        # Convert positions and store it as state
        self.world_mouse_x = mouse_position_x_tuple_scaled + self.camera.rect.x
        self.world_mouse_y = mouse_position_y_tuple_scaled + self.camera.rect.y
        if self.sprite_sheet_rect is not None:
            self.world_mouse_x = min(
                self.world_mouse_x,
                self.sprite_sheet_rect.right - self.animation_sprite_width,
            )
            self.world_mouse_y = min(
                self.world_mouse_y,
                self.sprite_sheet_rect.bottom - self.animation_sprite_height,
            )
        self.world_mouse_tu_x = int(self.world_mouse_x // TILE_SIZE)
        self.world_mouse_tu_y = int(self.world_mouse_y // TILE_SIZE)
        self.world_mouse_snapped_x = self.world_mouse_tu_x * TILE_SIZE
        self.world_mouse_snapped_y = self.world_mouse_tu_y * TILE_SIZE
        self.screen_mouse_x = self.world_mouse_snapped_x - self.camera.rect.x
        self.screen_mouse_y = self.world_mouse_snapped_y - self.camera.rect.y
        # Draw cursor
        pg.draw.rect(
            NATIVE_SURF,
            "green",
            [
                self.screen_mouse_x,
                self.screen_mouse_y,
                self.animation_sprite_width,
                self.animation_sprite_height,
            ],
            1,
        )

        # Curtain
        self.curtain.draw(NATIVE_SURF, 0)

    #######################
    # STATE UPDATE LOGICS #
    #######################
    def _JUST_ENTERED_SCENE(self, dt: int) -> None:
        """
        - Counts up entry delay time.
        """

        self.entry_delay_timer.update(dt)

    def _OPENING_SCENE_CURTAIN(self, dt: int) -> None:
        """
        - Updates curtain alpha.
        """

        self.curtain.update(dt)

    def _OPENED_SCENE_CURTAIN(self, dt: int) -> None:
        """
        - Get user input for file name.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            if self.input_text != "":
                self.file_name = self.input_text
                self.curtain.go_to_opaque()

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_SHEET_PNG_PATH_QUERY(self, dt: int) -> None:
        """
        - Get user input for png path.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            if exists(self.input_text) and self.input_text.endswith(".png"):
                # Setup the sprite sheet data
                self.sprite_sheet_png_path = self.input_text
                self.sprite_sheet_surf = pg.image.load(self.sprite_sheet_png_path).convert_alpha()
                self.sprite_sheet_rect = self.sprite_sheet_surf.get_rect()
                is_narrower = self.sprite_sheet_rect.width < self.camera.rect.width
                is_shorter = self.sprite_sheet_rect.height < self.camera.rect.height
                if not (is_narrower or is_shorter):
                    # Sprite sheet is not smaller than camera here
                    self.is_sprite_sheet_smaller_than_camera = False
                    # Setup camera limits
                    self.camera.set_rect_limit(
                        float(self.sprite_sheet_rect.top),
                        float(self.sprite_sheet_rect.bottom),
                        float(self.sprite_sheet_rect.left),
                        float(self.sprite_sheet_rect.right),
                    )
                # Init room collision map list
                sprite_sheet_width_tu: int = self.sprite_sheet_rect.width // TILE_SIZE
                sprite_sheet_height_tu: int = self.sprite_sheet_rect.height // TILE_SIZE
                self._init_room_collision_map_list(
                    sprite_sheet_width_tu,
                    sprite_sheet_height_tu,
                )
                # Close curtain
                self.curtain.go_to_opaque()
            else:
                self._set_input_text("png path does not exist!")

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_SIZE_QUERY(self, dt: int) -> None:
        """
        - Get user input for sprite size.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            if self.input_text.isdigit():
                if self.sprite_sheet_rect is not None:
                    # Setup the sprite height
                    self.animation_sprite_height = max(int(self.input_text) * TILE_SIZE, 0)
                    self.animation_sprite_height = min(self.sprite_sheet_rect.height, self.animation_sprite_height)
                    self.animation_sprite_height_tu = int(self.animation_sprite_height // TILE_SIZE)
                    # Close curtain
                    self.curtain.go_to_opaque()
            else:
                self._set_input_text("type int only please!")

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_WIDTH_QUERY(self, dt: int) -> None:
        """
        - Get user input for sprite size.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            if self.input_text.isdigit():
                if self.sprite_sheet_rect is not None:
                    # Setup the sprite width
                    self.animation_sprite_width = max(int(self.input_text) * TILE_SIZE, 0)
                    self.animation_sprite_width = min(self.sprite_sheet_rect.width, self.animation_sprite_width)
                    self.animation_sprite_width_tu = int(self.animation_sprite_width // TILE_SIZE)
                    # Close curtain
                    self.curtain.go_to_opaque()
            else:
                self._set_input_text("type int only please!")

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _ANIMATION_NAME_QUERY(self, dt: int) -> None:
        """
        - Get user input for sprite size.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            if self.input_text != "":
                self.animation_name = self.input_text
                # Close curtain
                self.curtain.go_to_opaque()

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _LOOP_QUERY(self, dt: int) -> None:
        """
        - Get user input for sprite size.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            options: dict = {
                "y": 1,
                "n": 0,
            }
            if self.input_text in options:
                self.animation_is_loop = options[self.input_text]
                # Close curtain
                self.curtain.go_to_opaque()
            else:
                self._set_input_text("type y or n only please!")

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _NEXT_ANIMATION_QUERY(self, dt: int) -> None:
        """
        - Get user input for sprite size.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            if self.input_text != "":
                self.next_animation_name = self.input_text
                # Close curtain
                self.curtain.go_to_opaque()

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _DURATION_QUERY(self, dt: int) -> None:
        """
        - Get user input for sprite size.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            if self.input_text.isdigit():
                # Setup the sprite_size
                self.animation_duration = int(self.input_text)
                # Close curtain
                self.curtain.go_to_opaque()
            else:
                self._set_input_text("type int only please!")

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _ADD_SPRITES(self, dt: int) -> None:
        """
        - Move camera and add frames to be saved.
        - Updates curtain alpha.
        """
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            self._update_camera_anchor_position_with_input(dt)

            # Lmb just pressed
            if self.game_event_handler.is_lmb_just_pressed:
                is_lmb_just_pressed_occupied: bool = False
                # Look in selection if got collision
                for world_mouse_tu_xi in range(self.animation_sprite_width_tu):
                    # Found occupied? Return
                    if is_lmb_just_pressed_occupied:
                        break
                    for world_mouse_tu_yi in range(self.animation_sprite_height_tu):
                        world_mouse_tu_x: int = self.world_mouse_tu_x + world_mouse_tu_xi
                        world_mouse_tu_y: int = self.world_mouse_tu_y + world_mouse_tu_yi
                        # Get each one in room_collision_map_list
                        found_tile_lmb_pressed: int = self._get_tile_from_room_collision_map_list(
                            world_mouse_tu_x,
                            world_mouse_tu_y,
                        )
                        # Found occupied? Return
                        if found_tile_lmb_pressed == 1:
                            is_lmb_just_pressed_occupied = True
                            break
                # All cells are empty
                if not is_lmb_just_pressed_occupied:
                    # Iterate size to set each to 1
                    for world_mouse_tu_xi2 in range(self.animation_sprite_width_tu):
                        for world_mouse_tu_yi2 in range(self.animation_sprite_height_tu):
                            world_mouse_tu_x2: int = self.world_mouse_tu_x + world_mouse_tu_xi2
                            world_mouse_tu_y2: int = self.world_mouse_tu_y + world_mouse_tu_yi2
                            # Store each one in room_collision_map_list
                            self._set_tile_from_room_collision_map_list(
                                world_mouse_tu_x2,
                                world_mouse_tu_y2,
                                1,
                            )
                            if self.sprite_sheet_surf is not None:
                                # Draw marker on sprite sheet
                                self.sprite_sheet_surf.blit(
                                    self.selected_surf_marker,
                                    (
                                        world_mouse_tu_x2 * TILE_SIZE,
                                        world_mouse_tu_y2 * TILE_SIZE,
                                    ),
                                )
                    # Add to list
                    self.local_animation_sprites_list.append(
                        {
                            "x": self.world_mouse_snapped_x,
                            "y": self.world_mouse_snapped_y,
                        }
                    )

            # Enter just pressed, prioritize lmb
            elif self.game_event_handler.is_enter_just_pressed:
                # Exit to ask save quit, save again, redo
                self.curtain.go_to_opaque()

        # Update curtain
        self.curtain.update(dt)

    def _SAVE_QUIT_REDO_QUERY(self, dt: int) -> None:
        """
        - Get user input for save quit, save again, redo.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            if int(self.input_text) in [
                self.save_and_quit_choice_after_add_sprites_state,
                self.save_and_redo_choice_after_add_sprites_state,
                self.redo_choice_after_add_sprites_state,
                self.quit_choice_after_add_sprites_state,
            ]:
                # Remember selected option
                self.selected_choice_after_add_sprites_state = int(self.input_text)
                # 1 = Save and quit
                if self.selected_choice_after_add_sprites_state == self.save_and_quit_choice_after_add_sprites_state:
                    self._update_local_with_user_state_input()
                    # Validate the JSON before write to disk
                    if not validate_json(self.local_animation_json, ANIMATION_SCHEMA):
                        raise ValueError("Invalid animation json against schema")
                    # Get settings_json_path
                    settings_json_path: str = join(JSONS_REPO_DIR_PATH, f"{self.file_name}.json")
                    # POST to disk. SAVE local_animation_json to disk
                    self.game.POST_file_to_disk_dynamic_path(
                        settings_json_path,
                        self.local_animation_json,
                    )
                    self.game_music_manager.fade_out_music(int(self.curtain.fade_duration))
                    self.curtain.go_to_opaque()
                # 2 = Save and redo
                elif self.selected_choice_after_add_sprites_state == self.save_and_redo_choice_after_add_sprites_state:
                    self._update_local_with_user_state_input()
                    self._redo_cleanup_logic()
                    self.curtain.go_to_opaque()
                # 3 = Redo
                elif self.selected_choice_after_add_sprites_state == self.redo_choice_after_add_sprites_state:
                    self._redo_cleanup_logic()
                    self.curtain.go_to_opaque()
                # 4 = Quit
                elif self.selected_choice_after_add_sprites_state == self.quit_choice_after_add_sprites_state:
                    self.game_music_manager.fade_out_music(int(self.curtain.fade_duration))
                    self.curtain.go_to_opaque()
            else:
                self._set_input_text("type 1, 2, 3 or 4 only please!")

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _CLOSING_SCENE_CURTAIN(self, dt: int) -> None:
        """
        - Updates curtain alpha.
        """

        self.curtain.update(dt)

    def _CLOSED_SCENE_CURTAIN(self, dt: int) -> None:
        """
        - Counts up exit delay time.
        """

        self.exit_delay_timer.update(dt)

    #####################
    # STATE TRANSITIONS #
    #####################
    def _JUST_ENTERED_SCENE_to_OPENING_SCENE_CURTAIN(self) -> None:
        self.curtain.go_to_invisible()

    def _OPENING_SCENE_CURTAIN_to_OPENED_SCENE_CURTAIN(self) -> None:
        # Make curtain faster for in state blink
        self.curtain.set_duration(self.FAST_FADE_DURATION)
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the file name to be saved,")

    def _OPENED_SCENE_CURTAIN_to_SPRITE_SHEET_PNG_PATH_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the png path to be loaded,")

    def _SPRITE_SHEET_PNG_PATH_QUERY_to_SPRITE_SIZE_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the sprite height in tile units to be used,")

    def _SPRITE_SIZE_QUERY_to_SPRITE_WIDTH_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the sprite width in tile units to be used,")

    def _SPRITE_WIDTH_QUERY_to_ANIMATION_NAME_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the animation name,")

    def _ANIMATION_NAME_QUERY_to_LOOP_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("does the animation loops (y/n)?")

    def _LOOP_QUERY_to_NEXT_ANIMATION_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the next animation name (optional),")

    def _NEXT_ANIMATION_QUERY_to_DURATION_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the animation duration (ms),")

    def _DURATION_QUERY_to_ADD_SPRITES(self) -> None:
        pass

    def _ADD_SPRITES_to_SAVE_QUIT_REDO_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("save and quit, save and redo, redo, quit (1/2/3/4)?")

    def _SAVE_QUIT_REDO_QUERY_to_ANIMATION_NAME_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the animation name,")

    def _SAVE_QUIT_REDO_QUERY_to_ADD_SPRITES(self) -> None:
        pass

    def _CLOSING_SCENE_CURTAIN_to_CLOSED_SCENE_CURTAIN(self) -> None:
        NATIVE_SURF.fill("black")

    #############
    # CALLBACKS #
    #############
    def _on_entry_delay_timer_end(self) -> None:
        self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.OPENING_SCENE_CURTAIN)

    def _on_exit_delay_timer_end(self) -> None:
        # Load title screen music. Played in my set state
        self.game_music_manager.set_current_music_path(OGGS_PATHS_DICT["xdeviruchi_title_theme.ogg"])
        self.game_music_manager.play_music(-1, 0.0, 0)
        self.game.set_scene("MainMenu")

    def _on_curtain_invisible(self) -> None:
        if self.state_machine_update.state == AnimationJsonGenerator.State.OPENING_SCENE_CURTAIN:
            self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.OPENED_SCENE_CURTAIN)

    def _on_curtain_opaque(self) -> None:
        state_actions: dict[Enum, Callable] = {
            AnimationJsonGenerator.State.OPENED_SCENE_CURTAIN: self._CURTAIN_OPENED_SCENE_CURTAIN,
            AnimationJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY: self._CURTAIN_SPRITE_SHEET_PNG_PATH_QUERY,
            AnimationJsonGenerator.State.SPRITE_SIZE_QUERY: self._CURTAIN_SPRITE_SIZE_QUERY,
            AnimationJsonGenerator.State.SPRITE_WIDTH_QUERY: self._CURTAIN_SPRITE_WIDTH_QUERY,
            AnimationJsonGenerator.State.ANIMATION_NAME_QUERY: self._CURTAIN_ANIMATION_NAME_QUERY,
            AnimationJsonGenerator.State.LOOP_QUERY: self._CURTAIN_LOOP_QUERY,
            AnimationJsonGenerator.State.NEXT_ANIMATION_QUERY: self._CURTAIN_NEXT_ANIMATION_QUERY,
            AnimationJsonGenerator.State.DURATION_QUERY: self._CURTAIN_DURATION_QUERY,
            AnimationJsonGenerator.State.ADD_SPRITES: self._CURTAIN_ADD_SPRITES,
            AnimationJsonGenerator.State.SAVE_QUIT_REDO_QUERY: self._CURTAIN_SAVE_QUIT_REDO_QUERY,
            AnimationJsonGenerator.State.CLOSING_SCENE_CURTAIN: self._CURTAIN_CLOSING_SCENE_CURTAIN,
        }
        handler = state_actions.get(self.state_machine_update.state)
        if handler:
            handler()

    ###########################
    # CURTAIN CALLBACKS STATE #
    ###########################
    def _CURTAIN_OPENED_SCENE_CURTAIN(self) -> None:
        self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_SPRITE_SHEET_PNG_PATH_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.SPRITE_SIZE_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_SPRITE_SIZE_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.SPRITE_WIDTH_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_SPRITE_WIDTH_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.ANIMATION_NAME_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_ANIMATION_NAME_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.LOOP_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_LOOP_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.NEXT_ANIMATION_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_NEXT_ANIMATION_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.DURATION_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_DURATION_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.ADD_SPRITES)
        self.curtain.go_to_invisible()

    def _CURTAIN_ADD_SPRITES(self) -> None:
        self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.SAVE_QUIT_REDO_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_SAVE_QUIT_REDO_QUERY(self) -> None:
        if self.selected_choice_after_add_sprites_state == (self.save_and_redo_choice_after_add_sprites_state):
            self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.ANIMATION_NAME_QUERY)
            self.curtain.go_to_invisible()
        elif self.selected_choice_after_add_sprites_state == (self.redo_choice_after_add_sprites_state):
            self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.ADD_SPRITES)
            self.curtain.go_to_invisible()
        elif self.selected_choice_after_add_sprites_state == (self.save_and_quit_choice_after_add_sprites_state):
            self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.CLOSED_SCENE_CURTAIN)
        elif self.selected_choice_after_add_sprites_state == (self.quit_choice_after_add_sprites_state):
            self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.CLOSED_SCENE_CURTAIN)

    def _CURTAIN_CLOSING_SCENE_CURTAIN(self) -> None:
        self._change_update_and_draw_state_machine(AnimationJsonGenerator.State.CLOSED_SCENE_CURTAIN)

    ########
    # DRAW #
    ########
    def draw(self) -> None:
        self.state_machine_draw.handle(0)

    ##########
    # UPDATE #
    ##########
    def update(self, dt: int) -> None:
        # REMOVE IN BUILD
        self.game.debug_draw.add(
            {
                "type": "text",
                "layer": 6,
                "x": 0,
                "y": 0,
                "text": (f"animation json generator " f"state: {self.state_machine_update.state.name}"),
            }
        )

        # All states here can go to options, update and draw options menu, stop my update
        if self.game_event_handler.is_pause_just_pressed:
            self.game.set_is_options_menu_active(True)

        # Update state machine
        self.state_machine_update.handle(dt)

    ###########
    # HELPERS #
    ###########
    def _change_update_and_draw_state_machine(self, value: Enum) -> None:
        """
        Update and change are the same, so use this to change both.
        """
        self.state_machine_update.change_state(value)
        self.state_machine_draw.change_state(value)

    def _redo_cleanup_logic(self) -> None:
        """
        Prepare to reselect again.
        """
        # Get fresh selected sprite sheet again
        if self.sprite_sheet_png_path is not None:
            self.sprite_sheet_surf = pg.image.load(self.sprite_sheet_png_path).convert_alpha()
            # Empty the selected sprites list
            self.local_animation_sprites_list = []
            # Empty collision map
            self._init_room_collision_map_list(
                self.room_collision_map_width_tu,
                self.room_collision_map_height_tu,
            )

    def _update_local_with_user_state_input(self) -> None:
        """
        Prepare local to be saved.
        """
        # Get name from path
        if self.sprite_sheet_png_path is not None:
            sprite_sheet_png_path_obj = Path(self.sprite_sheet_png_path)
            sprite_sheet_png_name = sprite_sheet_png_path_obj.name
            # Save this animation to local
            self.local_animation_json[self.animation_name] = {
                "animation_is_loop": self.animation_is_loop,
                "next_animation_name": self.next_animation_name,
                "animation_duration": self.animation_duration,
                "animation_sprite_height": self.animation_sprite_height,
                "animation_sprite_width": self.animation_sprite_width,
                "sprite_sheet_png_name": sprite_sheet_png_name,
                "animation_sprites_list": self.local_animation_sprites_list,
            }

    def _draw_grid(self) -> None:
        """
        Draw grid on sprite sheet surf.
        """
        blit_sequence = []
        for i in range(NATIVE_WIDTH_TU):
            vertical_line_x_position: float = (TILE_SIZE * i - self.camera.rect.x) % NATIVE_WIDTH
            blit_sequence.append(
                (
                    self.grid_vertical_line_surf,
                    (vertical_line_x_position, 0.0),
                )
            )
            horizontal_line_y_position: float = (TILE_SIZE * i - self.camera.rect.y) % NATIVE_WIDTH
            blit_sequence.append(
                (
                    self.grid_horizontal_line_surf,
                    (0.0, horizontal_line_y_position),
                )
            )

        NATIVE_SURF.fblits(blit_sequence)

    def _get_tile_from_room_collision_map_list(
        self,
        world_tu_x: int,
        world_tu_y: int,
    ) -> int:
        """
        Returns -1 if out of bounds.
        Because camera needs extra 1 and thus may get out of bound.
        """
        if 0 <= world_tu_x < self.room_collision_map_width_tu and 0 <= world_tu_y < self.room_collision_map_height_tu:
            return self.room_collision_map_list[world_tu_y * self.room_collision_map_width_tu + world_tu_x]
        else:
            return -1

    def _set_tile_from_room_collision_map_list(
        self,
        world_tu_x: int,
        world_tu_y: int,
        value: int,
    ) -> None | int:
        """
        Returns -1 if out of bounds.
        Because camera needs extra 1 and thus may get out of bound.
        """
        if 0 <= world_tu_x < self.room_collision_map_width_tu and 0 <= world_tu_y < self.room_collision_map_height_tu:
            self.room_collision_map_list[world_tu_y * self.room_collision_map_width_tu + world_tu_x] = value
            return None
        else:
            return -1

    def _init_room_collision_map_list(
        self,
        room_width_tu: int,
        room_height_tu: int,
    ) -> None:
        """
        Init the room collision list with 0.
        """
        self.room_collision_map_width_tu = room_width_tu
        self.room_collision_map_height_tu = room_height_tu
        self.room_collision_map_list = [0 for _ in range(self.room_collision_map_width_tu * self.room_collision_map_height_tu)]

    def _set_input_text(self, value: str) -> None:
        """
        User input texts.
        """
        self.input_text = value
        self.input_rect = FONT.get_rect(self.input_text)
        self.input_rect.center = NATIVE_RECT.center

    def _set_prompt_text(self, value: str) -> None:
        """
        User query texts.
        """
        local_settings_dict_enter = pg.key.name(self.game.local_settings_metadata_instance.enter)
        self.prompt_text = f"{value} " f"hit {local_settings_dict_enter} " "to proceed"
        self.prompt_rect = FONT.get_rect(self.prompt_text)
        self.prompt_rect.center = NATIVE_RECT.center
        self.prompt_rect.y -= FONT_HEIGHT + 1

    def _handle_query_input(self, accept_callback: Callable) -> None:
        """
        The query typing logic.
        """
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.game_event_handler.this_frame_event:
                if self.game_event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept
                    if self.game_event_handler.this_frame_event.key == pg.K_RETURN:
                        accept_callback()
                    # Delete
                    elif self.game_event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self._set_input_text(new_value)
                        # Play text
                        self.game_sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add
                    else:
                        new_value = self.input_text + self.game_event_handler.this_frame_event.unicode
                        self._set_input_text(new_value)
                        # Play text
                        self.game_sound_manager.play_sound("text_1.ogg", 0, 0, 0)

    def _update_camera_anchor_position_with_input(self, dt: int) -> None:
        # If image is smaller than camera no need to move camera
        if not self.is_sprite_sheet_smaller_than_camera:
            # Camera movement
            # Get direction_horizontal
            direction_horizontal: int = self.game_event_handler.is_right_pressed - self.game_event_handler.is_left_pressed
            # Update camera anchor position with direction and speed
            self.camera_anchor_vector.x += direction_horizontal * self.camera_speed * dt
            # Get direction_vertical
            direction_vertical: int = self.game_event_handler.is_down_pressed - self.game_event_handler.is_up_pressed
            # Update camera anchor position with direction and speed
            self.camera_anchor_vector.y += direction_vertical * self.camera_speed * dt
            # Lerp camera position to target camera anchor
            self.camera.update(dt)
