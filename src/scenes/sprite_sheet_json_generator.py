import re
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
from schemas import SPRITE_SHEET_METADATA_SCHEMA
from schemas import validate_json
from typeguard import typechecked

if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class SpriteSheetJsonGenerator:
    HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
    SLOW_FADE_DURATION = 1000.0
    FAST_FADE_DURATION = 250.0

    class State(Enum):
        JUST_ENTERED_SCENE = auto()
        OPENING_SCENE_CURTAIN = auto()
        OPENED_SCENE_CURTAIN = auto()
        SPRITE_SHEET_PNG_PATH_QUERY = auto()
        SPRITE_SHEET_ROOM_MAP_BODY_COLOR_QUERY = auto()
        SPRITE_SHEET_ROOM_MAP_SUB_DIVISION_COLOR_QUERY = auto()
        SPRITE_SHEET_ROOM_MAP_BORDER_COLOR_QUERY = auto()
        SPRITE_NAME_QUERY = auto()
        SPRITE_LAYER_QUERY = auto()
        SPRITE_TYPE_QUERY = auto()
        SPRITE_TILE_TYPE_QUERY = auto()
        SPRITE_TILE_MIX_QUERY = auto()
        ADD_SPRITES = auto()
        ADD_OTHER_SPRITES = auto()
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
        self._setup_collision_map()
        self._setup_surfs()
        self._setup_second_rect_region_feature()
        self._setup_loop_options()
        self._setup_music()
        self._setup_state_machine_update()
        self._setup_state_machine_draw()

        # If image is smaller than camera no need to move camera
        self.is_sprite_smaller_than_camera: bool = True

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
        self.sprite_room_map_body_color: str = ""
        self.sprite_room_map_sub_division_color: str = ""
        self.sprite_room_map_border_color: str = ""
        self.sprite_name: str = ""
        self.sprite_type: str = ""
        self.sprite_layer: int = 0
        self.sprite_tile_type: str = ""
        self.sprite_is_tile_mix: int = 0

        # Sprite sheet surf
        self.sprite_sheet_png_path: (None | str) = None
        self.sprite_sheet_surf: (None | pg.Surface) = None
        self.sprite_sheet_rect: (None | pg.Rect) = None

        # To be saved json
        self.local_sprite_json: dict = {}
        self.local_sprites_list: list = []

    def _setup_camera(self) -> None:
        self.camera_anchor_vector: Vector2 = Vector2(0.0, 0.0)
        self.camera: Camera = Camera(
            self.camera_anchor_vector,
            # REMOVE IN BUILD
            self.game.debug_draw,
        )
        self.camera_speed: float = 0.09  # Px / ms

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

    def _setup_second_rect_region_feature(self) -> None:
        self.first_world_selected_tile_rect = pg.FRect(0.0, 0.0, TILE_SIZE, TILE_SIZE)
        self.second_world_selected_tile_rect = pg.FRect(0.0, 0.0, TILE_SIZE, TILE_SIZE)
        self.combined_world_selected_tile_rect = pg.FRect(0.0, 0.0, TILE_SIZE, TILE_SIZE)
        self.screen_combined_world_selected_tile_rect_x: float = 0.0
        self.screen_combined_world_selected_tile_rect_y: float = 0.0
        self.combined_world_selected_tile_rect_width_tu: int = 0
        self.combined_world_selected_tile_rect_height_tu: int = 0
        self.combined_world_selected_tile_rect_x_tu: int = 0
        self.combined_world_selected_tile_rect_y_tu: int = 0

    def _setup_music(self) -> None:
        # Load editor screen music. Played in my set state
        self.game_music_manager.set_current_music_path(OGGS_PATHS_DICT["xdeviruchi_take_some_rest_and_eat_some_food.ogg"])
        self.game_music_manager.play_music(-1, 0.0, 0)

    def _setup_state_machine_update(self) -> None:
        """
        Create state machine for update.
        """

        self.state_machine_update = StateMachine(
            initial_state=SpriteSheetJsonGenerator.State.JUST_ENTERED_SCENE,
            state_handlers={
                SpriteSheetJsonGenerator.State.JUST_ENTERED_SCENE: self._JUST_ENTERED_SCENE,
                SpriteSheetJsonGenerator.State.OPENING_SCENE_CURTAIN: self._OPENING_SCENE_CURTAIN,
                SpriteSheetJsonGenerator.State.OPENED_SCENE_CURTAIN: self._OPENED_SCENE_CURTAIN,
                SpriteSheetJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY: self._SPRITE_SHEET_PNG_PATH_QUERY,
                SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_BODY_COLOR_QUERY: self._SPRITE_SHEET_ROOM_MAP_BODY_COLOR_QUERY,
                SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_SUB_DIVISION_COLOR_QUERY: self._SPRITE_SHEET_ROOM_MAP_SUB_DIVISION_COLOR_QUERY,
                SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_BORDER_COLOR_QUERY: self._SPRITE_SHEET_ROOM_MAP_BORDER_COLOR_QUERY,
                SpriteSheetJsonGenerator.State.SPRITE_NAME_QUERY: self._SPRITE_NAME_QUERY,
                SpriteSheetJsonGenerator.State.SPRITE_LAYER_QUERY: self._SPRITE_LAYER_QUERY,
                SpriteSheetJsonGenerator.State.SPRITE_TYPE_QUERY: self._SPRITE_TYPE_QUERY,
                SpriteSheetJsonGenerator.State.SPRITE_TILE_TYPE_QUERY: self._SPRITE_TILE_TYPE_QUERY,
                SpriteSheetJsonGenerator.State.SPRITE_TILE_MIX_QUERY: self._SPRITE_TILE_MIX_QUERY,
                SpriteSheetJsonGenerator.State.ADD_SPRITES: self._ADD_SPRITES,
                SpriteSheetJsonGenerator.State.ADD_OTHER_SPRITES: self._ADD_OTHER_SPRITES,
                SpriteSheetJsonGenerator.State.SAVE_QUIT_REDO_QUERY: self._SAVE_QUIT_REDO_QUERY,
                SpriteSheetJsonGenerator.State.CLOSING_SCENE_CURTAIN: self._CLOSING_SCENE_CURTAIN,
                SpriteSheetJsonGenerator.State.CLOSED_SCENE_CURTAIN: self._CLOSED_SCENE_CURTAIN,
            },
            transition_actions={
                (
                    SpriteSheetJsonGenerator.State.JUST_ENTERED_SCENE,
                    SpriteSheetJsonGenerator.State.OPENING_SCENE_CURTAIN,
                ): self._JUST_ENTERED_SCENE_to_OPENING_SCENE_CURTAIN,
                (
                    SpriteSheetJsonGenerator.State.OPENING_SCENE_CURTAIN,
                    SpriteSheetJsonGenerator.State.OPENED_SCENE_CURTAIN,
                ): self._OPENING_SCENE_CURTAIN_to_OPENED_SCENE_CURTAIN,
                (
                    SpriteSheetJsonGenerator.State.OPENED_SCENE_CURTAIN,
                    SpriteSheetJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY,
                ): self._OPENED_SCENE_CURTAIN_to_SPRITE_SHEET_PNG_PATH_QUERY,
                (
                    SpriteSheetJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY,
                    SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_BODY_COLOR_QUERY,
                ): self._SPRITE_SHEET_PNG_PATH_QUERY_to_SPRITE_SHEET_ROOM_MAP_BODY_COLOR_QUERY,
                (
                    SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_BODY_COLOR_QUERY,
                    SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_SUB_DIVISION_COLOR_QUERY,
                ): self._SPRITE_SHEET_ROOM_MAP_BODY_COLOR_QUERY_to_SPRITE_SHEET_ROOM_MAP_SUB_DIVISION_COLOR_QUERY,
                (
                    SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_SUB_DIVISION_COLOR_QUERY,
                    SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_BORDER_COLOR_QUERY,
                ): self._SPRITE_SHEET_ROOM_MAP_SUB_DIVISION_COLOR_QUERY_to_SPRITE_SHEET_ROOM_MAP_BORDER_COLOR_QUERY,
                (
                    SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_BORDER_COLOR_QUERY,
                    SpriteSheetJsonGenerator.State.SPRITE_NAME_QUERY,
                ): self._SPRITE_SHEET_ROOM_MAP_BORDER_COLOR_QUERY_to_SPRITE_NAME_QUERY,
                (
                    SpriteSheetJsonGenerator.State.SPRITE_NAME_QUERY,
                    SpriteSheetJsonGenerator.State.SPRITE_LAYER_QUERY,
                ): self._SPRITE_NAME_QUERY_to_SPRITE_LAYER_QUERY,
                (
                    SpriteSheetJsonGenerator.State.SPRITE_LAYER_QUERY,
                    SpriteSheetJsonGenerator.State.SPRITE_TYPE_QUERY,
                ): self._SPRITE_LAYER_QUERY_to_SPRITE_TYPE_QUERY,
                (
                    SpriteSheetJsonGenerator.State.SPRITE_TYPE_QUERY,
                    SpriteSheetJsonGenerator.State.SPRITE_TILE_TYPE_QUERY,
                ): self._SPRITE_TYPE_QUERY_to_SPRITE_TILE_TYPE_QUERY,
                (
                    SpriteSheetJsonGenerator.State.SPRITE_TILE_TYPE_QUERY,
                    SpriteSheetJsonGenerator.State.SPRITE_TILE_MIX_QUERY,
                ): self._SPRITE_TILE_TYPE_QUERY_to_SPRITE_TILE_MIX_QUERY,
                (
                    SpriteSheetJsonGenerator.State.SPRITE_TILE_MIX_QUERY,
                    SpriteSheetJsonGenerator.State.ADD_SPRITES,
                ): self._SPRITE_TILE_MIX_QUERY_to_ADD_SPRITES,
                (
                    SpriteSheetJsonGenerator.State.ADD_SPRITES,
                    SpriteSheetJsonGenerator.State.ADD_OTHER_SPRITES,
                ): self._ADD_SPRITES_to_ADD_OTHER_SPRITES,
                (
                    SpriteSheetJsonGenerator.State.ADD_OTHER_SPRITES,
                    SpriteSheetJsonGenerator.State.SAVE_QUIT_REDO_QUERY,
                ): self._ADD_OTHER_SPRITES_to_SAVE_QUIT_REDO_QUERY,
                (
                    SpriteSheetJsonGenerator.State.SAVE_QUIT_REDO_QUERY,
                    SpriteSheetJsonGenerator.State.SPRITE_NAME_QUERY,
                ): self._SAVE_QUIT_REDO_QUERY_to_SPRITE_NAME_QUERY,
                (
                    SpriteSheetJsonGenerator.State.SAVE_QUIT_REDO_QUERY,
                    SpriteSheetJsonGenerator.State.ADD_SPRITES,
                ): self._SAVE_QUIT_REDO_QUERY_to_ADD_SPRITES,
                (
                    SpriteSheetJsonGenerator.State.CLOSING_SCENE_CURTAIN,
                    SpriteSheetJsonGenerator.State.CLOSED_SCENE_CURTAIN,
                ): self._CLOSING_SCENE_CURTAIN_to_CLOSED_SCENE_CURTAIN,
            },
        )

    def _setup_state_machine_draw(self) -> None:
        """
        Create state machine for draw.
        """

        self.state_machine_draw = StateMachine(
            initial_state=SpriteSheetJsonGenerator.State.JUST_ENTERED_SCENE,
            state_handlers={
                SpriteSheetJsonGenerator.State.JUST_ENTERED_SCENE: self._NOTHING,
                SpriteSheetJsonGenerator.State.OPENING_SCENE_CURTAIN: self._QUERIES,
                SpriteSheetJsonGenerator.State.OPENED_SCENE_CURTAIN: self._QUERIES,
                SpriteSheetJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_BODY_COLOR_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_SUB_DIVISION_COLOR_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_BORDER_COLOR_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.SPRITE_NAME_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.SPRITE_LAYER_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.SPRITE_TYPE_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.SPRITE_TILE_TYPE_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.SPRITE_TILE_MIX_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.ADD_SPRITES: self._ADD_SPRITES_DRAW,
                SpriteSheetJsonGenerator.State.ADD_OTHER_SPRITES: self._ADD_OTHER_SPRITES_DRAW,
                SpriteSheetJsonGenerator.State.SAVE_QUIT_REDO_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.CLOSING_SCENE_CURTAIN: self._QUERIES,
                SpriteSheetJsonGenerator.State.CLOSED_SCENE_CURTAIN: self._NOTHING,
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
        # Draw promt and input
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
        mouse_position_x_tuple_scaled: int | float = mouse_position_x_tuple // self.game.get_one_local_settings_dict_value(
            "resolution_scale"
        )
        mouse_position_y_tuple_scaled: int | float = mouse_position_y_tuple // self.game.get_one_local_settings_dict_value(
            "resolution_scale"
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
        # Convert positions
        self.world_mouse_x = mouse_position_x_tuple_scaled + self.camera.rect.x
        self.world_mouse_y = mouse_position_y_tuple_scaled + self.camera.rect.y
        if self.sprite_sheet_rect is not None:
            self.world_mouse_x = min(
                self.world_mouse_x,
                self.sprite_sheet_rect.right - TILE_SIZE,
            )
            self.world_mouse_y = min(
                self.world_mouse_y,
                self.sprite_sheet_rect.bottom - TILE_SIZE,
            )
        self.world_mouse_tu_x = int(self.world_mouse_x // TILE_SIZE)
        self.world_mouse_tu_y = int(self.world_mouse_y // TILE_SIZE)
        self.world_mouse_snapped_x = int(self.world_mouse_tu_x * TILE_SIZE)
        self.world_mouse_snapped_y = int(self.world_mouse_tu_y * TILE_SIZE)
        self.screen_mouse_x = self.world_mouse_snapped_x - self.camera.rect.x
        self.screen_mouse_y = self.world_mouse_snapped_y - self.camera.rect.y
        # Draw cursor
        pg.draw.rect(
            NATIVE_SURF,
            "green",
            [
                self.screen_mouse_x,
                self.screen_mouse_y,
                TILE_SIZE,
                TILE_SIZE,
            ],
            1,
        )

        # Curtain
        self.curtain.draw(NATIVE_SURF, 0)

    def _ADD_OTHER_SPRITES_DRAW(self, _dt: int) -> None:
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

        # Draw and update cursor position
        # When it is done only, so that it does not mess with saving
        if self.curtain.is_done:
            # Get mouse position
            mouse_position_tuple: tuple[int, int] = pg.mouse.get_pos()
            mouse_position_x_tuple: int = mouse_position_tuple[0]
            mouse_position_y_tuple: int = mouse_position_tuple[1]
            # Scale mouse position
            mouse_position_x_tuple_scaled: int | float = mouse_position_x_tuple // self.game.get_one_local_settings_dict_value(
                "resolution_scale"
            )
            mouse_position_y_tuple_scaled: int | float = mouse_position_y_tuple // self.game.get_one_local_settings_dict_value(
                "resolution_scale"
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
            # Convert positions
            self.world_mouse_x = mouse_position_x_tuple_scaled + self.camera.rect.x
            self.world_mouse_y = mouse_position_y_tuple_scaled + self.camera.rect.y
            if self.sprite_sheet_rect is not None:
                self.world_mouse_x = min(
                    self.world_mouse_x,
                    self.sprite_sheet_rect.right - TILE_SIZE,
                )
                self.world_mouse_y = min(
                    self.world_mouse_y,
                    self.sprite_sheet_rect.bottom - TILE_SIZE,
                )
            self.world_mouse_tu_x = int(self.world_mouse_x // TILE_SIZE)
            self.world_mouse_tu_y = int(self.world_mouse_y // TILE_SIZE)
            self.world_mouse_snapped_x = int(self.world_mouse_tu_x * TILE_SIZE)
            self.world_mouse_snapped_y = int(self.world_mouse_tu_y * TILE_SIZE)
            self.screen_mouse_x = self.world_mouse_snapped_x - self.camera.rect.x
            self.screen_mouse_y = self.world_mouse_snapped_y - self.camera.rect.y
            # Combine the first rect with this cursor
            self.second_world_selected_tile_rect.x = self.world_mouse_snapped_x
            self.second_world_selected_tile_rect.y = self.world_mouse_snapped_y
            self.combined_world_selected_tile_rect = self.first_world_selected_tile_rect.union(
                self.second_world_selected_tile_rect
            )
            self.screen_combined_world_selected_tile_rect_x = self.combined_world_selected_tile_rect.x - self.camera.rect.x
            self.screen_combined_world_selected_tile_rect_y = self.combined_world_selected_tile_rect.y - self.camera.rect.y
            # Draw combined cursor
            pg.draw.rect(
                NATIVE_SURF,
                "green",
                [
                    self.screen_combined_world_selected_tile_rect_x,
                    self.screen_combined_world_selected_tile_rect_y,
                    self.combined_world_selected_tile_rect.width,
                    self.combined_world_selected_tile_rect.height,
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
        - Get user input.
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
        - Get user input.
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
                    self.is_sprite_smaller_than_camera = False
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
                self.curtain.go_to_opaque()
            else:
                self._set_input_text("png path does not exist!")

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_SHEET_ROOM_MAP_BODY_COLOR_QUERY(self, dt: int) -> None:
        """
        - Get user input.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            if self.input_text != "":
                # Valid hex?
                if self.HEX_COLOR_PATTERN.match(self.input_text):
                    self.sprite_room_map_body_color = self.input_text
                    # Close curtain
                    self.curtain.go_to_opaque()
                else:
                    raise ValueError(f"Invalid hex color code: '{self.input_text}'")

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_SHEET_ROOM_MAP_SUB_DIVISION_COLOR_QUERY(self, dt: int) -> None:
        """
        - Get user input.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            if self.input_text != "":
                # Valid hex?
                if self.HEX_COLOR_PATTERN.match(self.input_text):
                    self.sprite_room_map_sub_division_color = self.input_text
                    # Close curtain
                    self.curtain.go_to_opaque()
                else:
                    raise ValueError(f"Invalid hex color code: '{self.input_text}'")

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_SHEET_ROOM_MAP_BORDER_COLOR_QUERY(self, dt: int) -> None:
        """
        - Get user input.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            if self.input_text != "":
                # Valid hex?
                if self.HEX_COLOR_PATTERN.match(self.input_text):
                    self.sprite_room_map_border_color = self.input_text
                    # Close curtain
                    self.curtain.go_to_opaque()
                else:
                    raise ValueError(f"Invalid hex color code: '{self.input_text}'")

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_NAME_QUERY(self, dt: int) -> None:
        """
        - Get user input.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            if self.input_text != "":
                self.sprite_name = self.input_text
                self.curtain.go_to_opaque()

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_LAYER_QUERY(self, dt: int) -> None:
        """
        - Get user input.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            if self.input_text.isdigit():
                self.sprite_layer = max(int(self.input_text), 0)
                self.curtain.go_to_opaque()
            else:
                self._set_input_text("type int only please!")

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_TYPE_QUERY(self, dt: int) -> None:
        """
        - Get user input.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            if self.input_text != "":
                self.sprite_type = self.input_text
                self.curtain.go_to_opaque()

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_TILE_TYPE_QUERY(self, dt: int) -> None:
        """
        - Get user input.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            if self.input_text != "":
                self.sprite_tile_type = self.input_text
                self.curtain.go_to_opaque()

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_TILE_MIX_QUERY(self, dt: int) -> None:
        """
        - Get user input.
        - Updates curtain alpha.
        """

        # Accept logic
        def _accept_callback() -> None:
            options: dict = {
                "y": 1,
                "n": 0,
            }
            if self.input_text in options:
                self.sprite_is_tile_mix = options[self.input_text]
                # Close curtain
                self.curtain.go_to_opaque()
            else:
                self._set_input_text("type y or n only please!")

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
                # Get what is clicked
                found_tile_lmb_pressed: int = self._get_tile_from_room_collision_map_list(
                    self.world_mouse_tu_x,
                    self.world_mouse_tu_y,
                )
                # Clicked on empty?
                if found_tile_lmb_pressed != 1:
                    # Remember first selected tile rect
                    self.first_world_selected_tile_rect.x = self.world_mouse_snapped_x
                    self.first_world_selected_tile_rect.y = self.world_mouse_snapped_y
                    # Go to ADD_OTHER_SPRITES
                    self.state_machine_update.change_state(SpriteSheetJsonGenerator.State.ADD_OTHER_SPRITES)
                    self.state_machine_draw.change_state(SpriteSheetJsonGenerator.State.ADD_OTHER_SPRITES)

        # Update curtain
        self.curtain.update(dt)

    def _ADD_OTHER_SPRITES(self, dt: int) -> None:
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
                self.combined_world_selected_tile_rect_width_tu = int(self.combined_world_selected_tile_rect.width // TILE_SIZE)
                self.combined_world_selected_tile_rect_height_tu = int(self.combined_world_selected_tile_rect.height // TILE_SIZE)
                self.combined_world_selected_tile_rect_x_tu = int(self.combined_world_selected_tile_rect.x // TILE_SIZE)
                self.combined_world_selected_tile_rect_y_tu = int(self.combined_world_selected_tile_rect.y // TILE_SIZE)
                for world_mouse_tu_xi in range(self.combined_world_selected_tile_rect_width_tu):
                    # Found occupied? Return
                    if is_lmb_just_pressed_occupied:
                        break
                    for world_mouse_tu_yi in range(self.combined_world_selected_tile_rect_height_tu):
                        world_mouse_tu_x: int = self.combined_world_selected_tile_rect_x_tu + world_mouse_tu_xi
                        world_mouse_tu_y: int = self.combined_world_selected_tile_rect_y_tu + world_mouse_tu_yi
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
                    self._fill_selected_region_with_one()
                    self._update_local_with_user_state_input()
                    # Validate the json before write to disk
                    if not validate_json(self.local_sprite_json, SPRITE_SHEET_METADATA_SCHEMA):
                        raise ValueError("Invalid sprite sheet json against schema")
                    self.game.POST_file_to_disk_dynamic_path(
                        join(JSONS_REPO_DIR_PATH, f"{self.file_name}.json"),
                        self.local_sprite_json,
                    )
                    self.game_music_manager.fade_out_music(int(self.curtain.fade_duration))
                    self.curtain.go_to_opaque()
                # 2 = Save and redo
                elif self.selected_choice_after_add_sprites_state == self.save_and_redo_choice_after_add_sprites_state:
                    self._fill_selected_region_with_one()
                    self._update_local_with_user_state_input()
                    self.curtain.go_to_opaque()
                # 3 = Redo
                elif self.selected_choice_after_add_sprites_state == self.redo_choice_after_add_sprites_state:
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

    def _SPRITE_SHEET_PNG_PATH_QUERY_to_SPRITE_SHEET_ROOM_MAP_BODY_COLOR_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the sprite room map body hex color,")

    def _SPRITE_SHEET_ROOM_MAP_BODY_COLOR_QUERY_to_SPRITE_SHEET_ROOM_MAP_SUB_DIVISION_COLOR_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the sprite room map sub division hex color,")

    def _SPRITE_SHEET_ROOM_MAP_SUB_DIVISION_COLOR_QUERY_to_SPRITE_SHEET_ROOM_MAP_BORDER_COLOR_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the sprite room map border hex color,")

    def _SPRITE_SHEET_ROOM_MAP_BORDER_COLOR_QUERY_to_SPRITE_NAME_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the sprite name,")

    def _SPRITE_NAME_QUERY_to_SPRITE_LAYER_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the sprite layer,")

    def _SPRITE_LAYER_QUERY_to_SPRITE_TYPE_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the sprite type,")

    def _SPRITE_TYPE_QUERY_to_SPRITE_TILE_TYPE_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the sprite tile type,")

    def _SPRITE_TILE_TYPE_QUERY_to_SPRITE_TILE_MIX_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("does the tile mix (y/n)?")

    def _SPRITE_TILE_MIX_QUERY_to_ADD_SPRITES(self) -> None:
        self._empty_selected_sprite()

    def _ADD_SPRITES_to_ADD_OTHER_SPRITES(self) -> None:
        pass

    def _ADD_OTHER_SPRITES_to_SAVE_QUIT_REDO_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("save and quit, save and redo, redo, quit (1/2/3/4)?")

    def _SAVE_QUIT_REDO_QUERY_to_SPRITE_NAME_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the sprite name,")

    def _SAVE_QUIT_REDO_QUERY_to_ADD_SPRITES(self) -> None:
        self._empty_selected_sprite()

    def _CLOSING_SCENE_CURTAIN_to_CLOSED_SCENE_CURTAIN(self) -> None:
        NATIVE_SURF.fill("black")

    #############
    # CALLBACKS #
    #############
    def _on_entry_delay_timer_end(self) -> None:
        self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.OPENING_SCENE_CURTAIN)

    def _on_exit_delay_timer_end(self) -> None:
        # Load title screen music. Played in my set state
        self.game_music_manager.set_current_music_path(OGGS_PATHS_DICT["xdeviruchi_title_theme.ogg"])
        self.game_music_manager.play_music(-1, 0.0, 0)
        self.game.set_scene("MainMenu")

    def _on_curtain_invisible(self) -> None:
        if self.state_machine_update.state == SpriteSheetJsonGenerator.State.OPENING_SCENE_CURTAIN:
            self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.OPENED_SCENE_CURTAIN)

    def _on_curtain_opaque(self) -> None:
        state_actions: dict[Enum, Callable] = {
            SpriteSheetJsonGenerator.State.OPENED_SCENE_CURTAIN: self._CURTAIN_OPENED_SCENE_CURTAIN,
            SpriteSheetJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY: self._CURTAIN_SPRITE_SHEET_PNG_PATH_QUERY,
            SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_BODY_COLOR_QUERY: self._CURTAIN_SPRITE_SHEET_ROOM_MAP_BODY_COLOR_QUERY,
            SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_SUB_DIVISION_COLOR_QUERY: self._CURTAIN_SPRITE_SHEET_ROOM_MAP_SUB_DIVISION_COLOR_QUERY,
            SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_BORDER_COLOR_QUERY: self._CURTAIN_SPRITE_SHEET_ROOM_MAP_BORDER_COLOR_QUERY,
            SpriteSheetJsonGenerator.State.SPRITE_NAME_QUERY: self._CURTAIN_SPRITE_NAME_QUERY,
            SpriteSheetJsonGenerator.State.SPRITE_LAYER_QUERY: self._CURTAIN_SPRITE_LAYER_QUERY,
            SpriteSheetJsonGenerator.State.SPRITE_TYPE_QUERY: self._CURTAIN_SPRITE_TYPE_QUERY,
            SpriteSheetJsonGenerator.State.SPRITE_TILE_TYPE_QUERY: self._CURTAIN_SPRITE_TILE_TYPE_QUERY,
            SpriteSheetJsonGenerator.State.SPRITE_TILE_MIX_QUERY: self._CURTAIN_SPRITE_TILE_MIX_QUERY,
            SpriteSheetJsonGenerator.State.ADD_OTHER_SPRITES: self._CURTAIN_ADD_OTHER_SPRITES,
            SpriteSheetJsonGenerator.State.SAVE_QUIT_REDO_QUERY: self._CURTAIN_SAVE_QUIT_REDO_QUERY,
            SpriteSheetJsonGenerator.State.CLOSING_SCENE_CURTAIN: self._CURTAIN_CLOSING_SCENE_CURTAIN,
        }
        handler = state_actions.get(self.state_machine_update.state)
        if handler:
            handler()

    ###########################
    # CURTAIN CALLBACKS STATE #
    ###########################
    def _CURTAIN_OPENED_SCENE_CURTAIN(self) -> None:
        self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_SPRITE_SHEET_PNG_PATH_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_BODY_COLOR_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_SPRITE_SHEET_ROOM_MAP_BODY_COLOR_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_SUB_DIVISION_COLOR_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_SPRITE_SHEET_ROOM_MAP_SUB_DIVISION_COLOR_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.SPRITE_SHEET_ROOM_MAP_BORDER_COLOR_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_SPRITE_SHEET_ROOM_MAP_BORDER_COLOR_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.SPRITE_NAME_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_SPRITE_NAME_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.SPRITE_LAYER_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_SPRITE_LAYER_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.SPRITE_TYPE_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_SPRITE_TYPE_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.SPRITE_TILE_TYPE_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_SPRITE_TILE_TYPE_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.SPRITE_TILE_MIX_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_SPRITE_TILE_MIX_QUERY(self) -> None:
        self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.ADD_SPRITES)
        self.curtain.go_to_invisible()

    def _CURTAIN_ADD_OTHER_SPRITES(self) -> None:
        self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.SAVE_QUIT_REDO_QUERY)
        self.curtain.go_to_invisible()

    def _CURTAIN_SAVE_QUIT_REDO_QUERY(self) -> None:
        if self.selected_choice_after_add_sprites_state == (self.save_and_redo_choice_after_add_sprites_state):
            self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.SPRITE_NAME_QUERY)
            self.curtain.go_to_invisible()
        elif self.selected_choice_after_add_sprites_state == (self.redo_choice_after_add_sprites_state):
            self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.ADD_SPRITES)
            self.curtain.go_to_invisible()
        elif self.selected_choice_after_add_sprites_state == (self.save_and_quit_choice_after_add_sprites_state):
            self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.CLOSED_SCENE_CURTAIN)
        elif self.selected_choice_after_add_sprites_state == (self.quit_choice_after_add_sprites_state):
            self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.CLOSED_SCENE_CURTAIN)

    def _CURTAIN_CLOSING_SCENE_CURTAIN(self) -> None:
        self._change_update_and_draw_state_machine(SpriteSheetJsonGenerator.State.CLOSED_SCENE_CURTAIN)
        self.curtain.go_to_invisible()

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
                "text": (f"sprite sheet json generator " f"state: {self.state_machine_update.state.name}"),
            }
        )

        # All states here can go to options, update and draw options menu, stop my update
        if self.game_event_handler.is_pause_just_pressed:
            self.game.set_is_options_menu_active(True)

        self.state_machine_update.handle(dt)

    ###########
    # HELPERS #
    ###########
    def _empty_selected_sprite(self) -> None:
        self.first_world_selected_tile_rect = pg.FRect(0.0, 0.0, TILE_SIZE, TILE_SIZE)
        self.second_world_selected_tile_rect = pg.FRect(0.0, 0.0, TILE_SIZE, TILE_SIZE)
        self.combined_world_selected_tile_rect = pg.FRect(0.0, 0.0, TILE_SIZE, TILE_SIZE)
        self.screen_combined_world_selected_tile_rect_x = 0.0
        self.screen_combined_world_selected_tile_rect_y = 0.0
        self.combined_world_selected_tile_rect_width_tu = 0
        self.combined_world_selected_tile_rect_height_tu = 0
        self.combined_world_selected_tile_rect_x_tu = 0
        self.combined_world_selected_tile_rect_y_tu = 0

    def _draw_grid(self) -> None:
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

    def _init_room_collision_map_list(
        self,
        room_width_tu: int,
        room_height_tu: int,
    ) -> None:
        self.room_collision_map_width_tu = room_width_tu
        self.room_collision_map_height_tu = room_height_tu
        self.room_collision_map_list = [0 for _ in range(self.room_collision_map_width_tu * self.room_collision_map_height_tu)]

    def _set_input_text(self, value: str) -> None:
        self.input_text = value
        self.input_rect = FONT.get_rect(self.input_text)
        self.input_rect.center = NATIVE_RECT.center

    def _set_prompt_text(self, value: str) -> None:
        local_settings_dict_enter = pg.key.name(self.game.get_one_local_settings_dict_value("enter"))
        self.prompt_text = f"{value} " f"hit {local_settings_dict_enter} " "to proceed"
        self.prompt_rect = FONT.get_rect(self.prompt_text)
        self.prompt_rect.center = NATIVE_RECT.center
        self.prompt_rect.y -= FONT_HEIGHT + 1

    def _get_tile_from_room_collision_map_list(
        self,
        world_tu_x: int,
        world_tu_y: int,
    ) -> int:
        """
        Returns -1 if out of bounds
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
        Returns -1 if out of bounds
        Because camera needs extra 1 and thus may get out of bound.
        """
        if 0 <= world_tu_x < self.room_collision_map_width_tu and 0 <= world_tu_y < self.room_collision_map_height_tu:
            self.room_collision_map_list[world_tu_y * self.room_collision_map_width_tu + world_tu_x] = value
            return None
        else:
            return -1

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
        if not self.is_sprite_smaller_than_camera:
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

    def _fill_selected_region_with_one(self) -> None:
        # Iterate size to set 1
        for world_mouse_tu_xi2 in range(self.combined_world_selected_tile_rect_width_tu):
            for world_mouse_tu_yi2 in range(self.combined_world_selected_tile_rect_height_tu):
                world_mouse_tu_x2 = self.combined_world_selected_tile_rect_x_tu + world_mouse_tu_xi2
                world_mouse_tu_y2 = self.combined_world_selected_tile_rect_y_tu + world_mouse_tu_yi2
                # Store each one in room_collision_map_list
                self._set_tile_from_room_collision_map_list(
                    world_mouse_tu_x2,
                    world_mouse_tu_y2,
                    1,
                )
                # Draw marker on sprite sheet
                if self.sprite_sheet_surf is not None:
                    self.sprite_sheet_surf.blit(
                        self.selected_surf_marker,
                        (
                            world_mouse_tu_x2 * TILE_SIZE,
                            world_mouse_tu_y2 * TILE_SIZE,
                        ),
                    )

    def _update_local_with_user_state_input(self) -> None:
        """
        Prepare local to be saved.
        """
        # Add to list
        self.local_sprites_list.append(
            {
                "sprite_name": self.sprite_name,
                "sprite_layer": self.sprite_layer,
                "sprite_tile_type": self.sprite_tile_type,
                "sprite_type": self.sprite_type,
                "sprite_is_tile_mix": self.sprite_is_tile_mix,
                "width": int(self.combined_world_selected_tile_rect.width),
                "height": int(self.combined_world_selected_tile_rect.height),
                "x": int(self.combined_world_selected_tile_rect.x),
                "y": int(self.combined_world_selected_tile_rect.y),
            }
        )
        # Get file name
        if self.sprite_sheet_png_path is not None:
            sprite_sheet_png_path_obj = Path(self.sprite_sheet_png_path)
            sprite_sheet_png_name = sprite_sheet_png_path_obj.name
            self.local_sprite_json = {
                "sprite_sheet_png_name": sprite_sheet_png_name,
                "sprite_room_map_body_color": self.sprite_room_map_body_color,
                "sprite_room_map_sub_division_color": self.sprite_room_map_sub_division_color,
                "sprite_room_map_border_color": self.sprite_room_map_border_color,
                "sprites_list": self.local_sprites_list,
            }

    def _change_update_and_draw_state_machine(self, value: Enum) -> None:
        """
        Update and change are the same, so use this to change both.
        """
        self.state_machine_update.change_state(value)
        self.state_machine_draw.change_state(value)
