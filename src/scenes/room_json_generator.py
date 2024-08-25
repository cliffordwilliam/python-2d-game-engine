from enum import auto
from enum import Enum
from os import listdir
from os.path import exists
from os.path import join
from typing import Any
from typing import TYPE_CHECKING

from constants import FONT
from constants import FONT_HEIGHT
from constants import JSONS_ROOMS_DIR_PATH
from constants import NATIVE_HEIGHT
from constants import NATIVE_RECT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import NATIVE_WIDTH_TU
from constants import OGGS_PATHS_DICT
from constants import pg
from constants import PNGS_PATHS_DICT
from constants import ROOM_HEIGHT
from constants import ROOM_WIDTH
from constants import SPRITE_TILE_TYPE_BINARY_TO_OFFSET_DICT
from constants import SPRITE_TILE_TYPE_SPRITE_ADJACENT_NEIGHBOR_DIRECTIONS_LIST
from constants import TILE_SIZE
from constants import WORLD_CELL_SIZE
from constants import WORLD_HEIGHT
from constants import WORLD_HEIGHT_RU
from constants import WORLD_WIDTH
from constants import WORLD_WIDTH_RU
from nodes.button import Button
from nodes.button_container import ButtonContainer
from nodes.camera import Camera
from nodes.curtain import Curtain
from nodes.state_machine import StateMachine
from nodes.timer import Timer
from pygame.math import clamp
from pygame.math import Vector2
from typeguard import typechecked

if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class RoomJsonGenerator:
    # Implement Quadtree, fire animation first
    SLOW_FADE_DURATION = 1000.0
    FAST_FADE_DURATION = 250.0

    class State(Enum):
        JUST_ENTERED_SCENE = auto()
        OPENING_SCENE_CURTAIN = auto()
        OPENED_SCENE_CURTAIN = auto()
        ADD_OTHER_SPRITES = auto()
        FILE_NAME_QUERY = auto()
        SPRITE_SHEET_JSON_PATH_QUERY = auto()
        EDIT_ROOM = auto()
        SPRITE_PALETTE = auto()
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
        self._draw_world_grid()
        self._setup_music()
        self._setup_state_machine_update()
        self._setup_state_machine_draw()

        # First selected world cell rect
        self.first_world_selected_tile_rect = pg.FRect(0.0, 0.0, WORLD_CELL_SIZE, WORLD_CELL_SIZE)
        self.second_world_selected_tile_rect = pg.FRect(0.0, 0.0, WORLD_CELL_SIZE, WORLD_CELL_SIZE)
        self.combined_world_selected_tile_rect = pg.FRect(0.0, 0.0, WORLD_CELL_SIZE, WORLD_CELL_SIZE)
        self.screen_combined_world_selected_tile_rect_x = 0.0
        self.screen_combined_world_selected_tile_rect_y = 0.0
        self.combined_world_selected_tile_rect_width_ru = 0
        self.combined_world_selected_tile_rect_height_ru = 0
        self.combined_world_selected_tile_rect_x_ru = 0
        self.combined_world_selected_tile_rect_y_ru = 0
        self.cursor_width: int = TILE_SIZE
        self.cursor_height: int = TILE_SIZE
        self.cursor_width_tu: int = 1
        self.cursor_height_tu: int = 1

        self.is_from_edit_pressed_jump: bool = False
        self.is_from_pallete_pressed_jump: bool = False

        self.button_container: (ButtonContainer | None) = None
        self.selected_sprite_name: str = ""

        # Click button to update key name, used to access the values here
        self.reformat_sprite_sheet_json_metadata: dict = {}

    # Setups
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
        self.curtain.add_event_listener(self.on_curtain_invisible, Curtain.INVISIBLE_END)
        self.curtain.add_event_listener(self.on_curtain_opaque, Curtain.OPAQUE_END)

    def _setup_timers(self) -> None:
        """Setup timers with event listeners."""
        self.entry_delay_timer: Timer = Timer(duration=self.SLOW_FADE_DURATION)
        self.entry_delay_timer.add_event_listener(self.on_entry_delay_timer_end, Timer.END)

        self.exit_delay_timer: Timer = Timer(duration=self.SLOW_FADE_DURATION)
        self.exit_delay_timer.add_event_listener(self.on_exit_delay_timer_end, Timer.END)

    def _setup_texts(self) -> None:
        """Setup text for title and tips."""
        self.prompt_text: str = ""
        self.prompt_rect: pg.Rect = FONT.get_rect(self.prompt_text)

        self.input_text: str = ""
        self.input_rect: pg.Rect = FONT.get_rect(self.input_text)
        self.input_rect.center = NATIVE_RECT.center

    def _setup_user_input_store(self) -> None:
        """Store user inputs"""
        # Room metadata
        self.room_height: int = ROOM_HEIGHT
        self.room_height_tu: int = int(self.room_height // TILE_SIZE)
        self.room_width: int = ROOM_WIDTH
        self.room_width_tu: int = int(self.room_width // TILE_SIZE)
        self.room_topleft_x: int = 0
        self.room_topleft_y: int = 0

        # Sprite sheet surf
        self.sprite_sheet_png_name: (None | str) = None
        self.sprite_sheet_surf: (None | pg.Surface) = None

        # Sprite sheet binded actors and surfs
        self.sprite_sheet_actors_dict: dict = {}
        self.sprite_sheet_animation_jsons: dict[str, str] = {}
        self.sprite_sheet_parallax_background_memory: dict[str, Any] = {}

        # Sprite sheet layers
        # Parallax drawing layer data
        self.parallax_background_instances_list: list = []

        # Static background drawing layer data
        self.static_background_layers: int = 0
        self.static_background_collision_map_list: list[list[Any]] = []

        # Solid drawing layer data
        self.solid_collision_map_list: list = [0 for _ in range(self.room_width_tu * self.room_height_tu)]

        # Foreground drawing layer data
        self.foreground_layers: int = 0
        self.foreground_collision_map_list: list[list[Any]] = []

        # Pre render static background
        self.pre_render_static_background: pg.Surface = pg.Surface((self.room_width, self.room_height))
        self.pre_render_static_background.set_colorkey("red")
        self.pre_render_static_background.fill("red")
        # Pre render solid and foreground
        self.pre_render_solid_foreground: pg.Surface = pg.Surface((self.room_width, self.room_height))
        self.pre_render_solid_foreground.set_colorkey("red")
        self.pre_render_solid_foreground.fill("red")

        # TODO: static actors
        # TODO: actors
        # TODO: player

        # To be saved json
        # file name is room name
        self.file_name: str = ""
        # self.animation_json: dict = {}
        # self.animation_sprites_list: list = []

    def _setup_camera(self) -> None:
        self.camera_anchor_vector: Vector2 = Vector2(0.0, 0.0)
        self.camera: Camera = Camera(
            self.camera_anchor_vector,
            # REMOVE IN BUILD
            self.game.debug_draw,
        )
        self.camera_speed: float = 0.09  # Px / ms

    def _setup_collision_map(self) -> None:
        # World
        self.world_collision_map_list: list[Any] = [0 for _ in range(WORLD_WIDTH_RU * WORLD_HEIGHT_RU)]

    def _setup_surfs(self) -> None:
        # Selected surf marker
        self.selected_surf_marker: pg.Surface = pg.Surface((WORLD_CELL_SIZE, WORLD_CELL_SIZE))
        self.selected_surf_marker.fill("red")

        # Grid world surf
        self.grid_world_horizontal_line_surf: pg.Surface = pg.Surface((WORLD_WIDTH, 1))
        self.grid_world_horizontal_line_surf.fill("black")
        self.grid_world_horizontal_line_surf.set_alpha(21)
        self.grid_world_vertical_line_surf: pg.Surface = pg.Surface((1, WORLD_HEIGHT))
        self.grid_world_vertical_line_surf.fill("black")
        self.grid_world_vertical_line_surf.set_alpha(21)

        # Grid world surf
        self.grid_horizontal_line_surf: pg.Surface = pg.Surface((NATIVE_WIDTH, 1))
        self.grid_horizontal_line_surf.fill("black")
        self.grid_horizontal_line_surf.set_alpha(21)
        self.grid_vertical_line_surf: pg.Surface = pg.Surface((1, NATIVE_HEIGHT))
        self.grid_vertical_line_surf.fill("black")
        self.grid_vertical_line_surf.set_alpha(21)

        # World surf
        self.world_surf: pg.Surface = pg.Surface((WORLD_WIDTH, WORLD_HEIGHT))
        self.world_surf.fill(self.clear_color)

    def _setup_mouse_positions(self) -> None:
        self.world_mouse_x: float = 0.0
        self.world_mouse_y: float = 0.0
        self.world_mouse_tu_x: int = 0
        self.world_mouse_tu_y: int = 0
        self.world_mouse_snapped_x: int = 0
        self.world_mouse_snapped_y: int = 0
        self.screen_mouse_x: float = 0.0
        self.screen_mouse_y: float = 0.0

    def _setup_music(self) -> None:
        # Load editor screen music. Played in my set state
        self.game_music_manager.set_current_music_path(OGGS_PATHS_DICT["xdeviruchi_take_some_rest_and_eat_some_food.ogg"])
        self.game_music_manager.play_music(-1, 0.0, 0)

    def _setup_state_machine_update(self) -> None:
        """
        Create state machine for update.
        """

        self.state_machine_update = StateMachine(
            initial_state=RoomJsonGenerator.State.JUST_ENTERED_SCENE,
            state_handlers={
                RoomJsonGenerator.State.JUST_ENTERED_SCENE: self._JUST_ENTERED_SCENE,
                RoomJsonGenerator.State.OPENING_SCENE_CURTAIN: self._OPENING_SCENE_CURTAIN,
                RoomJsonGenerator.State.OPENED_SCENE_CURTAIN: self._OPENED_SCENE_CURTAIN,
                RoomJsonGenerator.State.ADD_OTHER_SPRITES: self._ADD_OTHER_SPRITES,
                RoomJsonGenerator.State.FILE_NAME_QUERY: self._FILE_NAME_QUERY,
                RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY: self._SPRITE_SHEET_JSON_PATH_QUERY,
                RoomJsonGenerator.State.EDIT_ROOM: self._EDIT_ROOM,
                RoomJsonGenerator.State.SPRITE_PALETTE: self._SPRITE_PALETTE,
                RoomJsonGenerator.State.CLOSING_SCENE_CURTAIN: self._CLOSING_SCENE_CURTAIN,
                RoomJsonGenerator.State.CLOSED_SCENE_CURTAIN: self._CLOSED_SCENE_CURTAIN,
            },
            transition_actions={
                (
                    RoomJsonGenerator.State.JUST_ENTERED_SCENE,
                    RoomJsonGenerator.State.OPENING_SCENE_CURTAIN,
                ): self._JUST_ENTERED_SCENE_to_OPENING_SCENE_CURTAIN,
                (
                    RoomJsonGenerator.State.OPENING_SCENE_CURTAIN,
                    RoomJsonGenerator.State.OPENED_SCENE_CURTAIN,
                ): self._OPENING_SCENE_CURTAIN_to_OPENED_SCENE_CURTAIN,
                (
                    RoomJsonGenerator.State.OPENED_SCENE_CURTAIN,
                    RoomJsonGenerator.State.ADD_OTHER_SPRITES,
                ): self._OPENED_SCENE_CURTAIN_to_ADD_OTHER_SPRITES,
                (
                    RoomJsonGenerator.State.ADD_OTHER_SPRITES,
                    RoomJsonGenerator.State.FILE_NAME_QUERY,
                ): self._ADD_OTHER_SPRITES_to_FILE_NAME_QUERY,
                (
                    RoomJsonGenerator.State.FILE_NAME_QUERY,
                    RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY,
                ): self._FILE_NAME_QUERY_to_SPRITE_SHEET_JSON_PATH_QUERY,
                (
                    RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY,
                    RoomJsonGenerator.State.EDIT_ROOM,
                ): self._SPRITE_SHEET_JSON_PATH_QUERY_to_EDIT_ROOM,
                (
                    RoomJsonGenerator.State.EDIT_ROOM,
                    RoomJsonGenerator.State.SPRITE_PALETTE,
                ): self._EDIT_ROOM_to_SPRITE_PALETTE,
                (
                    RoomJsonGenerator.State.SPRITE_PALETTE,
                    RoomJsonGenerator.State.EDIT_ROOM,
                ): self._SPRITE_PALETTE_to_EDIT_ROOM,
                (
                    RoomJsonGenerator.State.CLOSING_SCENE_CURTAIN,
                    RoomJsonGenerator.State.CLOSED_SCENE_CURTAIN,
                ): self._CLOSING_SCENE_CURTAIN_to_CLOSED_SCENE_CURTAIN,
            },
        )

    def _setup_state_machine_draw(self) -> None:
        """
        Create state machine for draw.
        """

        self.state_machine_draw = StateMachine(
            initial_state=RoomJsonGenerator.State.JUST_ENTERED_SCENE,
            state_handlers={
                RoomJsonGenerator.State.JUST_ENTERED_SCENE: self._NOTHING,
                RoomJsonGenerator.State.OPENING_SCENE_CURTAIN: self._QUERIES,
                RoomJsonGenerator.State.OPENED_SCENE_CURTAIN: self._ADD_ROOM_DRAW,
                RoomJsonGenerator.State.ADD_OTHER_SPRITES: self._ADD_OTHER_SPRITES_DRAW,
                RoomJsonGenerator.State.FILE_NAME_QUERY: self._QUERIES,
                RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY: self._QUERIES,
                RoomJsonGenerator.State.EDIT_ROOM: self._EDIT_ROOM_DRAW,
                RoomJsonGenerator.State.SPRITE_PALETTE: self._SPRITE_PALLETE_DRAW,
                RoomJsonGenerator.State.CLOSING_SCENE_CURTAIN: self._QUERIES,
                RoomJsonGenerator.State.CLOSED_SCENE_CURTAIN: self._NOTHING,
            },
            transition_actions={},
        )

    # State draw logics
    def _NOTHING(self, _dt: int) -> None:
        pass

    def _QUERIES(self, _dt: int) -> None:
        # Clear
        NATIVE_SURF.fill(self.clear_color)
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

    def _ADD_ROOM_DRAW(self, _dt: int) -> None:
        # Clear
        NATIVE_SURF.fill(self.clear_color)

        # Draw world surf
        NATIVE_SURF.blit(self.world_surf, (0, 0))

        # Draw grid
        self._draw_world_grid()

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
            0,
            # Because this will refer to top left of a cell
            # If it is flushed to the right it is out of bound
            WORLD_WIDTH - 1,
        )
        mouse_position_y_tuple_scaled = clamp(
            mouse_position_y_tuple_scaled,
            0,
            # Because this will refer to top left of a cell
            # If it is flushed to the bottom it is out of bound
            WORLD_HEIGHT - 1,
        )
        # Convert positions
        self.world_mouse_x = mouse_position_x_tuple_scaled + self.camera.rect.x
        self.world_mouse_y = mouse_position_y_tuple_scaled + self.camera.rect.y
        self.world_mouse_x = min(
            self.world_mouse_x,
            WORLD_WIDTH - WORLD_CELL_SIZE,
        )
        self.world_mouse_y = min(
            self.world_mouse_y,
            WORLD_HEIGHT - WORLD_CELL_SIZE,
        )
        self.world_mouse_tu_x = int(self.world_mouse_x // WORLD_CELL_SIZE)
        self.world_mouse_tu_y = int(self.world_mouse_y // WORLD_CELL_SIZE)
        self.world_mouse_snapped_x = int(self.world_mouse_tu_x * WORLD_CELL_SIZE)
        self.world_mouse_snapped_y = int(self.world_mouse_tu_y * WORLD_CELL_SIZE)
        self.screen_mouse_x = self.world_mouse_snapped_x - self.camera.rect.x
        self.screen_mouse_y = self.world_mouse_snapped_y - self.camera.rect.y
        # Draw cursor
        pg.draw.rect(
            NATIVE_SURF,
            "green",
            [
                self.screen_mouse_x,
                self.screen_mouse_y,
                WORLD_CELL_SIZE,
                WORLD_CELL_SIZE,
            ],
            1,
        )

        # Curtain
        self.curtain.draw(NATIVE_SURF, 0)

    def _EDIT_ROOM_DRAW(self, _dt: int) -> None:
        # Clear
        NATIVE_SURF.fill(self.clear_color)

        # Draw the parallax background
        for parallax_background in self.parallax_background_instances_list:
            if parallax_background is not None:
                parallax_background.draw()

        # Draw the pre render static background
        NATIVE_SURF.blit(
            self.pre_render_static_background,
            (
                -self.camera.rect.x,
                -self.camera.rect.y,
            ),
        )

        # Draw the pre render solid foreground
        NATIVE_SURF.blit(
            self.pre_render_solid_foreground,
            (
                -self.camera.rect.x,
                -self.camera.rect.y,
            ),
        )

        # Draw grid
        self.draw_grid()

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
        self.world_mouse_x = min(
            self.world_mouse_x,
            self.room_width - self.cursor_width,
        )
        self.world_mouse_y = min(
            self.world_mouse_y,
            self.room_height - self.cursor_height,
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
                self.cursor_width,
                self.cursor_height,
            ],
            1,
        )

        # Curtain
        self.curtain.draw(NATIVE_SURF, 0)

    def _SPRITE_PALLETE_DRAW(self, _dt: int) -> None:
        # Clear
        NATIVE_SURF.fill("black")

        if self.button_container is not None:
            self.button_container.draw(NATIVE_SURF)

        # Curtain
        self.curtain.draw(NATIVE_SURF, 0)

    def _ADD_OTHER_SPRITES_DRAW(self, _dt: int) -> None:
        # Clear
        NATIVE_SURF.fill(self.clear_color)

        # Draw world surf
        NATIVE_SURF.blit(self.world_surf, (0, 0))

        # Draw grid
        self._draw_world_grid()

        # Draw and update cursor position
        # When it is done only, so that it does not mess with saving
        if self.curtain.is_done:
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
            # Clamp this in the max room size instead (hardcoded 2 x 2, no point in increasing, if not too slow)
            mouse_position_x_tuple_scaled = clamp(
                mouse_position_x_tuple_scaled,
                (self.first_world_selected_tile_rect.x - WORLD_CELL_SIZE),
                # Because this will refer to top left of a cell
                # If it is flushed to the right it is out of bound
                (self.first_world_selected_tile_rect.x + 2 * WORLD_CELL_SIZE) - 1,
            )
            mouse_position_y_tuple_scaled = clamp(
                mouse_position_y_tuple_scaled,
                (self.first_world_selected_tile_rect.y - WORLD_CELL_SIZE),
                # Because this will refer to top left of a cell
                # If it is flushed to the bottom it is out of bound
                (self.first_world_selected_tile_rect.y + 2 * WORLD_CELL_SIZE) - 1,
            )
            # Convert positions
            self.world_mouse_x = mouse_position_x_tuple_scaled + self.camera.rect.x
            self.world_mouse_y = mouse_position_y_tuple_scaled + self.camera.rect.y
            self.world_mouse_x = min(
                self.world_mouse_x,
                WORLD_WIDTH - WORLD_CELL_SIZE,
            )
            self.world_mouse_y = min(
                self.world_mouse_y,
                WORLD_HEIGHT - WORLD_CELL_SIZE,
            )
            self.world_mouse_tu_x = int(self.world_mouse_x // WORLD_CELL_SIZE)
            self.world_mouse_tu_y = int(self.world_mouse_y // WORLD_CELL_SIZE)
            self.world_mouse_snapped_x = int(self.world_mouse_tu_x * WORLD_CELL_SIZE)
            self.world_mouse_snapped_y = int(self.world_mouse_tu_y * WORLD_CELL_SIZE)
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

    # State logics
    def _JUST_ENTERED_SCENE(self, dt: int) -> None:
        self.entry_delay_timer.update(dt)

    def _OPENING_SCENE_CURTAIN(self, dt: int) -> None:
        self.curtain.update(dt)

    def _OPENED_SCENE_CURTAIN(self, dt: int) -> None:
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Sprite selection
            # Lmb just pressed
            # TODO: If click on a room, Load the room
            # TODO: So collision store the file name
            # TODO: If click on empty then make new one
            if self.game_event_handler.is_lmb_just_pressed:
                # Get what is clicked
                found_tile_lmb_pressed = self.get_tile_from_world_collision_map_list(
                    self.world_mouse_tu_x,
                    self.world_mouse_tu_y,
                )

                # Clicked occupied? Load the room
                if found_tile_lmb_pressed != 0:
                    pass

                # Clicked on empty? Create new room
                elif found_tile_lmb_pressed == 0:
                    # Remember first selected tile rect
                    self.first_world_selected_tile_rect.x = self.world_mouse_snapped_x
                    self.first_world_selected_tile_rect.y = self.world_mouse_snapped_y
                    # Go to ADD_OTHER_SPRITES
                    self.state_machine_update.change_state(RoomJsonGenerator.State.ADD_OTHER_SPRITES)
                    self.state_machine_draw.change_state(RoomJsonGenerator.State.ADD_OTHER_SPRITES)

    def _ADD_OTHER_SPRITES(self, dt: int) -> None:
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Sprite selection
            # Lmb just pressed
            if self.game_event_handler.is_lmb_just_pressed:
                # Check if selection is all empty cells
                # Iterate size to check all empty
                self.combined_world_selected_tile_rect_width_ru = int(
                    self.combined_world_selected_tile_rect.width // WORLD_CELL_SIZE
                )
                self.combined_world_selected_tile_rect_height_ru = int(
                    self.combined_world_selected_tile_rect.height // WORLD_CELL_SIZE
                )
                self.combined_world_selected_tile_rect_x_ru = int(self.combined_world_selected_tile_rect.x // WORLD_CELL_SIZE)
                self.combined_world_selected_tile_rect_y_ru = int(self.combined_world_selected_tile_rect.y // WORLD_CELL_SIZE)
                found_occupied = False
                for world_mouse_tu_xi in range(self.combined_world_selected_tile_rect_width_ru):
                    if found_occupied:
                        break
                    for world_mouse_tu_yi in range(self.combined_world_selected_tile_rect_height_ru):
                        world_mouse_tu_x = self.combined_world_selected_tile_rect_x_ru + world_mouse_tu_xi
                        world_mouse_tu_y = self.combined_world_selected_tile_rect_y_ru + world_mouse_tu_yi
                        # Get each one in room_collision_map_list
                        found_tile_lmb_pressed = self.get_tile_from_world_collision_map_list(
                            world_mouse_tu_x,
                            world_mouse_tu_y,
                        )
                        # At least 1 of them is occupied? Return
                        if found_tile_lmb_pressed != 0:
                            found_occupied = True
                            break
                # All cells are empty
                if not found_occupied:
                    # Update room metadata dimension
                    self.room_height = self.combined_world_selected_tile_rect_width_ru * ROOM_HEIGHT
                    self.room_height_tu = int(self.room_height // TILE_SIZE)
                    self.room_width = self.combined_world_selected_tile_rect_height_ru * ROOM_WIDTH
                    self.room_width_tu = int(self.room_width // TILE_SIZE)
                    self.room_topleft_x = self.combined_world_selected_tile_rect_x_ru * ROOM_WIDTH
                    self.room_topleft_y = self.combined_world_selected_tile_rect_y_ru * ROOM_HEIGHT
                    # Setup camera limits
                    self.camera.set_rect_limit(
                        float(0),
                        float(self.room_height),
                        float(0),
                        float(self.room_width),
                    )
                    self.curtain.go_to_opaque()

        # Update curtain
        self.curtain.update(dt)

    def _FILE_NAME_QUERY(self, dt: int) -> None:
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.game_event_handler.this_frame_event:
                if self.game_event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept
                    if self.game_event_handler.this_frame_event.key == pg.K_RETURN:
                        if self.input_text != "":
                            # Update room name / file name metadata
                            self.file_name = self.input_text
                            self.curtain.go_to_opaque()
                    # Delete
                    elif self.game_event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        self.game_sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add
                    else:
                        new_value = self.input_text + self.game_event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        self.game_sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_SHEET_JSON_PATH_QUERY(self, dt: int) -> None:
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.game_event_handler.this_frame_event:
                if self.game_event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept
                    if self.game_event_handler.this_frame_event.key == pg.K_RETURN:
                        if exists(self.input_text) and self.input_text.endswith(".json"):
                            # GET from disk, Get the sprite sheet metadata
                            data = self.game.GET_file_from_disk_dynamic_path(self.input_text)

                            # Get sprite sheet name and surf
                            self.sprite_sheet_png_name = data["sprite_sheet_png_name"]
                            if self.sprite_sheet_png_name is not None:
                                self.sprite_sheet_surf = pg.image.load(
                                    PNGS_PATHS_DICT[self.sprite_sheet_png_name]
                                ).convert_alpha()

                                # Get the background and actors with sprite_sheet_png_name key
                                # Animation jsons data and surfs for this sprite sheet
                                self.sprite_sheet_actors_dict = self.game.stage_actors[self.sprite_sheet_png_name]
                                self.sprite_sheet_surf_names = self.game.stage_surf_names[self.sprite_sheet_png_name]
                                self.sprite_sheet_animation_jsons = self.game.stage_animation_jsons[self.sprite_sheet_png_name]
                                self.sprite_sheet_parallax_background_memory = self.game.stage_parallax_background_memory_dict[
                                    self.sprite_sheet_png_name
                                ]

                                # Prepare button list
                                buttons: list[Button] = []

                                # Iterate each sprite metadata
                                for object in data["sprites_list"]:
                                    # Reformat to key sprite names and its data as values
                                    self.reformat_sprite_sheet_json_metadata[object["sprite_name"]] = object

                                    # Populate the pallete button
                                    button: Button = Button(
                                        surf_size_tuple=(264, 19),
                                        topleft=(29, 14),
                                        text=object["sprite_name"],
                                        text_topleft=(53, 2),
                                        description_text=object["sprite_type"],
                                    )
                                    # Create subsurf
                                    subsurf: pg.Surface = self.sprite_sheet_surf.subsurface(
                                        (
                                            object["x"],
                                            object["y"],
                                            object["width"],
                                            object["height"],
                                        )
                                    )
                                    # Create base subsurf
                                    base_subsurf_width: int = 49
                                    base_subsurf_height: int = 19
                                    base_subsurf: pg.Surface = pg.Surface((base_subsurf_width, base_subsurf_height))
                                    base_subsurf.fill(self.clear_color)
                                    scaled_height: float = base_subsurf_width * object["height"] / object["width"]
                                    # Scale so width is 49
                                    subsurf = pg.transform.scale(subsurf, (base_subsurf_width, scaled_height))
                                    y_diff: float = scaled_height - base_subsurf_height
                                    base_subsurf.blit(subsurf, (0, -y_diff / 2))
                                    button.draw_extra_surf_on_surf(base_subsurf, (1, 0))
                                    buttons.append(button)

                                    # Init parallax background
                                    if object["sprite_type"] == "parallax_background":
                                        # Init the instance container
                                        self.parallax_background_instances_list.append(None)

                                    # Init static background
                                    if object["sprite_type"] == "static_background":
                                        # Count static background total layers
                                        if self.static_background_layers < object["sprite_layer"]:
                                            self.static_background_layers = object["sprite_layer"]

                                    # Init foreground
                                    if object["sprite_type"] == "foreground":
                                        # Count foreground total layers
                                        if self.foreground_layers < object["sprite_layer"]:
                                            self.foreground_layers = object["sprite_layer"]

                                # Static background layers total is ready here, populate
                                # Init collision map for each static background layers
                                for _ in range(self.static_background_layers):
                                    self.static_background_collision_map_list.append(
                                        [0 for _ in range(self.room_width_tu * self.room_height_tu)],
                                    )

                                # Init collision map for solid layer
                                self.solid_collision_map_list = [0 for _ in range(self.room_width_tu * self.room_height_tu)]

                                # Foreground layers total is ready here, populate
                                # Init collision map for each foreground layers
                                for _ in range(self.foreground_layers):
                                    self.foreground_collision_map_list.append(
                                        [0 for _ in range(self.room_width_tu * self.room_height_tu)],
                                    )

                                # Init pre render static background
                                self.pre_render_static_background = pg.Surface((self.room_width, self.room_height))
                                self.pre_render_static_background.set_colorkey("red")
                                self.pre_render_static_background.fill("red")
                                # Init pre render solid and foreground
                                self.pre_render_solid_foreground = pg.Surface((self.room_width, self.room_height))
                                self.pre_render_solid_foreground.set_colorkey("red")
                                self.pre_render_solid_foreground.fill("red")

                                # Init button container
                                self.button_container = ButtonContainer(
                                    buttons=buttons,
                                    offset=0,
                                    limit=7,
                                    is_pagination=True,
                                    game_event_handler=self.game_event_handler,
                                    game_sound_manager=self.game.sound_manager,
                                )
                                self.button_container.add_event_listener(self.on_button_selected, ButtonContainer.BUTTON_SELECTED)
                                # Init the selected name
                                self.selected_sprite_name = buttons[0].text
                                # Init the cursor size
                                sprite_sheet_obj = self.reformat_sprite_sheet_json_metadata[self.selected_sprite_name]
                                if sprite_sheet_obj["sprite_tile_type"] == "none":
                                    self.cursor_width = sprite_sheet_obj["width"]
                                    self.cursor_height = sprite_sheet_obj["height"]
                                    self.cursor_width_tu = self.cursor_width // TILE_SIZE
                                    self.cursor_height_tu = self.cursor_height // TILE_SIZE
                                else:
                                    self.cursor_width = TILE_SIZE
                                    self.cursor_height = TILE_SIZE
                                    self.cursor_width_tu = 1
                                    self.cursor_height_tu = 1

                            self.curtain.go_to_opaque()
                        else:
                            self.set_input_text("json path does not exist!")
                    # Delete
                    elif self.game_event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        self.game_sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add
                    else:
                        new_value = self.input_text + self.game_event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        self.game_sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain
        self.curtain.update(dt)

    def _EDIT_ROOM(self, dt: int) -> None:
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Move camera with input
            self._move_camera(dt)

            # TODO: Turn the block to a func and use the name as key

            # Get sprite metadata
            selected_sprite_type: str = self.reformat_sprite_sheet_json_metadata[self.selected_sprite_name]["sprite_type"]
            selected_sprite_layer_index: int = (
                self.reformat_sprite_sheet_json_metadata[self.selected_sprite_name]["sprite_layer"] - 1
            )
            selected_sprite_tile_type: str = self.reformat_sprite_sheet_json_metadata[self.selected_sprite_name][
                "sprite_tile_type"
            ]
            selected_sprite_x: int = self.reformat_sprite_sheet_json_metadata[self.selected_sprite_name]["x"]
            selected_sprite_y: int = self.reformat_sprite_sheet_json_metadata[self.selected_sprite_name]["y"]
            selected_sprite_name: str = self.reformat_sprite_sheet_json_metadata[self.selected_sprite_name]["sprite_name"]

            #############################
            # PARALLAX BACKGROUND STATE #
            #############################

            if selected_sprite_type == "parallax_background":
                # Lmb just pressed
                if self.game_event_handler.is_lmb_just_pressed:
                    # This layer is None?
                    if self.parallax_background_instances_list[selected_sprite_layer_index] is None:
                        # Fill with instance
                        self.parallax_background_instances_list[
                            selected_sprite_layer_index
                        ] = self.sprite_sheet_parallax_background_memory[self.selected_sprite_name](
                            self.sprite_sheet_surf,
                            self.camera,
                        )

                # Rmb just pressed
                if self.game_event_handler.is_rmb_just_pressed:
                    # This layer has instance?
                    if self.parallax_background_instances_list[selected_sprite_layer_index] is not None:
                        # Make it None
                        self.parallax_background_instances_list[selected_sprite_layer_index] = None

            ###########################
            # STATIC BACKGROUND STATE #
            ###########################

            if selected_sprite_type == "static_background":
                # Get static background layer collision map
                selected_static_background_layer_collision_map: list = self.static_background_collision_map_list[
                    selected_sprite_layer_index
                ]

                ####################
                # Lmb just pressed #
                ####################

                if self.game_event_handler.is_lmb_just_pressed:
                    ##################
                    # NONE TILE TYPE #
                    ##################

                    if selected_sprite_tile_type == "none":
                        self._on_lmb_just_pressed_none_tile_type(
                            selected_static_background_layer_collision_map,
                            selected_sprite_x,
                            selected_sprite_y,
                            selected_sprite_name,
                        )

                    ##################
                    # BLOB TILE TYPE #
                    ##################

                    if selected_sprite_tile_type != "none":
                        self._on_lmb_just_pressed_blob_tile_type(
                            selected_static_background_layer_collision_map,
                            selected_sprite_x,
                            selected_sprite_y,
                            selected_sprite_tile_type,
                            selected_sprite_name,
                        )

                ####################
                # Rmb just pressed #
                ####################

                if self.game_event_handler.is_rmb_just_pressed:
                    ##################
                    # NONE TILE TYPE #
                    ##################

                    if selected_sprite_tile_type == "none":
                        self._on_rmb_just_pressed_none_tile_type(
                            selected_static_background_layer_collision_map,
                        )

                    ##################
                    # BLOB TILE TYPE #
                    ##################

                    if selected_sprite_tile_type != "none":
                        self._on_rmb_just_pressed_blob_tile_type(
                            selected_static_background_layer_collision_map,
                        )

            ###############
            # SOLID STATE #
            ###############

            if selected_sprite_type == "solid":
                ####################
                # Lmb just pressed #
                ####################

                if self.game_event_handler.is_lmb_just_pressed:
                    ##################
                    # NONE TILE TYPE #
                    ##################

                    if selected_sprite_tile_type == "none":
                        self._on_lmb_just_pressed_none_tile_type(
                            self.solid_collision_map_list,
                            selected_sprite_x,
                            selected_sprite_y,
                            selected_sprite_name,
                        )

                    ##################
                    # BLOB TILE TYPE #
                    ##################

                    if selected_sprite_tile_type != "none":
                        self._on_lmb_just_pressed_blob_tile_type(
                            self.solid_collision_map_list,
                            selected_sprite_x,
                            selected_sprite_y,
                            selected_sprite_tile_type,
                            selected_sprite_name,
                        )

                ####################
                # Rmb just pressed #
                ####################

                if self.game_event_handler.is_rmb_just_pressed:
                    ##################
                    # NONE TILE TYPE #
                    ##################

                    if selected_sprite_tile_type == "none":
                        self._on_rmb_just_pressed_none_tile_type(
                            self.solid_collision_map_list,
                        )

                    ##################
                    # BLOB TILE TYPE #
                    ##################

                    if selected_sprite_tile_type != "none":
                        self._on_rmb_just_pressed_blob_tile_type(
                            self.solid_collision_map_list,
                        )

            ##############
            # THIN STATE #
            ##############

            if selected_sprite_type == "thin":
                ####################
                # Lmb just pressed #
                ####################

                if self.game_event_handler.is_lmb_just_pressed:
                    ##################
                    # NONE TILE TYPE #
                    ##################

                    if selected_sprite_tile_type == "none":
                        self._on_lmb_just_pressed_none_tile_type(
                            self.solid_collision_map_list,
                            selected_sprite_x,
                            selected_sprite_y,
                            selected_sprite_name,
                        )

                    ##################
                    # BLOB TILE TYPE #
                    ##################

                    if selected_sprite_tile_type != "none":
                        self._on_lmb_just_pressed_blob_tile_type(
                            self.solid_collision_map_list,
                            selected_sprite_x,
                            selected_sprite_y,
                            selected_sprite_tile_type,
                            selected_sprite_name,
                        )

                ####################
                # Rmb just pressed #
                ####################

                if self.game_event_handler.is_rmb_just_pressed:
                    ##################
                    # NONE TILE TYPE #
                    ##################

                    if selected_sprite_tile_type == "none":
                        self._on_rmb_just_pressed_none_tile_type(
                            self.solid_collision_map_list,
                        )

                    ##################
                    # BLOB TILE TYPE #
                    ##################

                    if selected_sprite_tile_type != "none":
                        self._on_rmb_just_pressed_blob_tile_type(
                            self.solid_collision_map_list,
                        )

            ####################
            # FOREGROUND STATE #
            ####################

            if selected_sprite_type == "foreground":
                # Get static background layer collision map
                selected_foreground_layer_collision_map: list = self.foreground_collision_map_list[selected_sprite_layer_index]

                ####################
                # Lmb just pressed #
                ####################

                if self.game_event_handler.is_lmb_just_pressed:
                    ##################
                    # NONE TILE TYPE #
                    ##################

                    if selected_sprite_tile_type == "none":
                        self._on_lmb_just_pressed_none_tile_type(
                            selected_foreground_layer_collision_map,
                            selected_sprite_x,
                            selected_sprite_y,
                            selected_sprite_name,
                        )

                    ##################
                    # BLOB TILE TYPE #
                    ##################

                    if selected_sprite_tile_type != "none":
                        self._on_lmb_just_pressed_blob_tile_type(
                            selected_foreground_layer_collision_map,
                            selected_sprite_x,
                            selected_sprite_y,
                            selected_sprite_tile_type,
                            selected_sprite_name,
                        )

                ####################
                # Rmb just pressed #
                ####################

                if self.game_event_handler.is_rmb_just_pressed:
                    ##################
                    # NONE TILE TYPE #
                    ##################

                    if selected_sprite_tile_type == "none":
                        self._on_rmb_just_pressed_none_tile_type(
                            selected_foreground_layer_collision_map,
                        )

                    ##################
                    # BLOB TILE TYPE #
                    ##################

                    if selected_sprite_tile_type != "none":
                        self._on_rmb_just_pressed_blob_tile_type(
                            selected_foreground_layer_collision_map,
                        )

            # Jump just pressed
            if self.game_event_handler.is_jump_just_pressed:
                self.is_from_edit_pressed_jump = True
                self.curtain.go_to_opaque()

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_PALETTE(self, dt: int) -> None:
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Sprites pallete
            # Jump just pressed
            if self.game_event_handler.is_jump_just_pressed:
                self.is_from_pallete_pressed_jump = True
                if self.button_container is not None:
                    self.button_container.set_is_input_allowed(False)
                self.curtain.go_to_opaque()

        # Even when curtain not done need to fade button
        if self.button_container is not None:
            self.button_container.update(dt)

        # Update curtain
        self.curtain.update(dt)

    def _CLOSING_SCENE_CURTAIN(self, dt: int) -> None:
        self.curtain.update(dt)

    def _CLOSED_SCENE_CURTAIN(self, dt: int) -> None:
        self.exit_delay_timer.update(dt)

    # State transitions
    def _JUST_ENTERED_SCENE_to_OPENING_SCENE_CURTAIN(self) -> None:
        self.curtain.go_to_invisible()

    def _OPENING_SCENE_CURTAIN_to_OPENED_SCENE_CURTAIN(self) -> None:
        # Make curtain faster for in state blink
        self.curtain.set_duration(self.FAST_FADE_DURATION)
        # Read all json room and mark it on grid
        for filename in listdir(JSONS_ROOMS_DIR_PATH):
            if filename.endswith(".json"):
                # Construct the full file path
                file_path = join(JSONS_ROOMS_DIR_PATH, filename)

                # Open and read the JSON file

                # GET from disk
                data = self.game.GET_file_from_disk_dynamic_path(file_path)

                # Draw marks on the world surf
                file_name = data["file_name"]
                room_x_ru = data["room_x_ru"]
                room_y_ru = data["room_y_ru"]
                room_scale_x = data["room_scale_x"]
                room_scale_y = data["room_scale_y"]
                room_x = room_x_ru * WORLD_CELL_SIZE
                room_y = room_y_ru * WORLD_CELL_SIZE
                room_cell_width = room_scale_x * WORLD_CELL_SIZE
                room_cell_height = room_scale_y * WORLD_CELL_SIZE
                sprite_room_map_body_color = data["sprite_room_map_body_color"]
                sprite_room_map_sub_division_color = data["sprite_room_map_sub_division_color"]
                sprite_room_map_border_color = data["sprite_room_map_border_color"]

                # TODO: Add collision and also render the doors
                pg.draw.rect(
                    self.world_surf,
                    sprite_room_map_body_color,
                    (
                        room_x,
                        room_y,
                        room_cell_width,
                        room_cell_height,
                    ),
                )

                for ru_xi in range(room_scale_x):
                    for ru_yi in range(room_scale_y):
                        ru_x: int = room_x_ru + ru_xi
                        ru_y: int = room_y_ru + ru_yi
                        pg.draw.rect(
                            self.world_surf,
                            sprite_room_map_sub_division_color,
                            (
                                ru_x * WORLD_CELL_SIZE,
                                ru_y * WORLD_CELL_SIZE,
                                WORLD_CELL_SIZE,
                                WORLD_CELL_SIZE,
                            ),
                            1,
                        )

                        # Store each one in room_collision_map_list
                        self.set_tile_from_world_collision_map_list(
                            ru_x,
                            ru_y,
                            file_name,
                        )

                pg.draw.rect(
                    self.world_surf,
                    sprite_room_map_border_color,
                    (
                        room_x,
                        room_y,
                        room_cell_width,
                        room_cell_height,
                    ),
                    1,
                )

    def _OPENED_SCENE_CURTAIN_to_ADD_OTHER_SPRITES(self) -> None:
        pass

    def _ADD_OTHER_SPRITES_to_FILE_NAME_QUERY(self) -> None:
        # Reset the input text
        self.set_input_text("")
        # Set my prompt text
        self.set_prompt_text("type the file name to be saved,")

    def _FILE_NAME_QUERY_to_SPRITE_SHEET_JSON_PATH_QUERY(self) -> None:
        # Reset the input text
        self.set_input_text("")
        # Set my prompt text
        self.set_prompt_text("type the json path to be loaded,")

    def _SPRITE_SHEET_JSON_PATH_QUERY_to_EDIT_ROOM(self) -> None:
        pass

    def _EDIT_ROOM_to_SPRITE_PALETTE(self) -> None:
        self.is_from_edit_pressed_jump = False

    def _SPRITE_PALETTE_to_EDIT_ROOM(self) -> None:
        self.is_from_pallete_pressed_jump = False

    def _CLOSING_SCENE_CURTAIN_to_CLOSED_SCENE_CURTAIN(self) -> None:
        NATIVE_SURF.fill("black")

    # Callbacks
    def on_entry_delay_timer_end(self) -> None:
        self.state_machine_update.change_state(RoomJsonGenerator.State.OPENING_SCENE_CURTAIN)
        self.state_machine_draw.change_state(RoomJsonGenerator.State.OPENING_SCENE_CURTAIN)

    def on_exit_delay_timer_end(self) -> None:
        # Load title screen music. Played in my set state
        self.game_music_manager.set_current_music_path(OGGS_PATHS_DICT["xdeviruchi_title_theme.ogg"])
        self.game_music_manager.play_music(-1, 0.0, 0)
        self.game.set_scene("MainMenu")

    def on_curtain_invisible(self) -> None:
        if self.state_machine_update.state == RoomJsonGenerator.State.OPENING_SCENE_CURTAIN:
            self.state_machine_update.change_state(RoomJsonGenerator.State.OPENED_SCENE_CURTAIN)
            self.state_machine_draw.change_state(RoomJsonGenerator.State.OPENED_SCENE_CURTAIN)
        elif self.state_machine_update.state == RoomJsonGenerator.State.SPRITE_PALETTE:
            if self.button_container is not None:
                self.button_container.set_is_input_allowed(True)

    def on_curtain_opaque(self) -> None:
        if self.state_machine_update.state == RoomJsonGenerator.State.ADD_OTHER_SPRITES:
            self.state_machine_update.change_state(RoomJsonGenerator.State.FILE_NAME_QUERY)
            self.state_machine_draw.change_state(RoomJsonGenerator.State.FILE_NAME_QUERY)
            self.curtain.go_to_invisible()
        elif self.state_machine_update.state == RoomJsonGenerator.State.FILE_NAME_QUERY:
            self.state_machine_update.change_state(RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY)
            self.state_machine_draw.change_state(RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY)
            self.curtain.go_to_invisible()
        elif self.state_machine_update.state == RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY:
            self.state_machine_update.change_state(RoomJsonGenerator.State.EDIT_ROOM)
            self.state_machine_draw.change_state(RoomJsonGenerator.State.EDIT_ROOM)
            self.curtain.go_to_invisible()
        elif self.state_machine_update.state == RoomJsonGenerator.State.EDIT_ROOM:
            if self.is_from_edit_pressed_jump:
                self.state_machine_update.change_state(RoomJsonGenerator.State.SPRITE_PALETTE)
                self.state_machine_draw.change_state(RoomJsonGenerator.State.SPRITE_PALETTE)
                self.curtain.go_to_invisible()
        elif self.state_machine_update.state == RoomJsonGenerator.State.SPRITE_PALETTE:
            if self.is_from_pallete_pressed_jump:
                self.state_machine_update.change_state(RoomJsonGenerator.State.EDIT_ROOM)
                self.state_machine_draw.change_state(RoomJsonGenerator.State.EDIT_ROOM)
                self.curtain.go_to_invisible()

    def on_button_selected(self, selected_button: Button) -> None:
        # Update selected name
        self.selected_sprite_name = selected_button.text
        # Update cursor size
        if self.reformat_sprite_sheet_json_metadata[self.selected_sprite_name]["sprite_tile_type"] == "none":
            self.cursor_width = self.reformat_sprite_sheet_json_metadata[self.selected_sprite_name]["width"]
            self.cursor_height = self.reformat_sprite_sheet_json_metadata[self.selected_sprite_name]["height"]
            self.cursor_width_tu = int(self.cursor_width // TILE_SIZE)
            self.cursor_height_tu = int(self.cursor_height // TILE_SIZE)
        else:
            self.cursor_width = TILE_SIZE
            self.cursor_height = TILE_SIZE
            self.cursor_width_tu = int(self.cursor_width // TILE_SIZE)
            self.cursor_height_tu = int(self.cursor_height // TILE_SIZE)
        # On select also counts as quiting pallete
        self.is_from_pallete_pressed_jump = True
        if self.button_container is not None:
            self.button_container.set_is_input_allowed(False)
        self.curtain.go_to_opaque()

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
                "text": (f"sprite sheet json generator " f"state: {self.state_machine_update.state.name}"),
            }
        )

        # All states here can go to options
        if self.game_event_handler.is_pause_just_pressed:
            # Update and draw options menu, stop my update
            self.game.set_is_options_menu_active(True)

        self.state_machine_update.handle(dt)

    # Helpers
    def _update_pre_render(self) -> None:
        # Clear pre render, make new ones so it does not build up data
        # Pre render static background
        self.pre_render_static_background = pg.Surface((self.room_width, self.room_height))
        self.pre_render_static_background.set_colorkey("red")
        self.pre_render_static_background.fill("red")
        # Pre render solid and foreground
        self.pre_render_solid_foreground = pg.Surface((self.room_width, self.room_height))
        self.pre_render_solid_foreground.set_colorkey("red")
        self.pre_render_solid_foreground.fill("red")

        # Iter over each static collision map layer
        for collision_map in self.static_background_collision_map_list:
            # Iter over cells
            for cell in collision_map:
                # Ignore air
                if cell == 0:
                    continue
                # Get metadata
                x = cell["x"]
                y = cell["y"]
                region_x = cell["region_x"]
                region_y = cell["region_y"]
                # Draw each one on pre_render_static_background
                if self.sprite_sheet_surf is not None:
                    self.pre_render_static_background.blit(
                        self.sprite_sheet_surf, (x, y), (region_x, region_y, TILE_SIZE, TILE_SIZE)
                    )

        # Iter over cells
        for cell in self.solid_collision_map_list:
            # Ignore air
            if cell == 0:
                continue
            # Get metadata
            x = cell["x"]
            y = cell["y"]
            region_x = cell["region_x"]
            region_y = cell["region_y"]
            # Draw each one on pre render
            if self.sprite_sheet_surf is not None:
                self.pre_render_solid_foreground.blit(self.sprite_sheet_surf, (x, y), (region_x, region_y, TILE_SIZE, TILE_SIZE))

        # Iter over each foreground collision map layer
        for collision_map in self.foreground_collision_map_list:
            # Iter over cells
            for cell in collision_map:
                # Ignore air
                if cell == 0:
                    continue
                # Get metadata
                x = cell["x"]
                y = cell["y"]
                region_x = cell["region_x"]
                region_y = cell["region_y"]
                # Draw each one on pre render
                if self.sprite_sheet_surf is not None:
                    self.pre_render_solid_foreground.blit(
                        self.sprite_sheet_surf, (x, y), (region_x, region_y, TILE_SIZE, TILE_SIZE)
                    )

    def _on_rmb_just_pressed_none_tile_type(
        self,
        collision_map_list: list[Any],
    ) -> None:
        """
        Click filled tile. Erase and set to 0.
        """
        # Get clicked cell
        found_tile_lmb_pressed = self.get_tile_from_collision_map_list(
            self.world_mouse_tu_x,
            self.world_mouse_tu_y,
            collision_map_list,
        )
        # Cell filled
        if found_tile_lmb_pressed != 0:
            # Fill collision map with 0 in cursor pos
            self.set_tile_from_collision_map_list(
                self.world_mouse_tu_x,
                self.world_mouse_tu_y,
                0,
                collision_map_list,
            )

            # Update pre render
            self._update_pre_render()

    def _on_rmb_just_pressed_blob_tile_type(
        self,
        collision_map_list: list[Any],
    ) -> None:
        """
        Click filled tile. Erase and set to 0.
        Tell neighbor to autotile update draw.
        """
        # Get clicked cell
        found_tile = self.get_tile_from_collision_map_list(
            self.world_mouse_tu_x,
            self.world_mouse_tu_y,
            collision_map_list,
        )
        # Cell is filled
        if found_tile != 0:
            # Fill collision map with 0 in cursor pos
            self.set_tile_from_collision_map_list(
                self.world_mouse_tu_x,
                self.world_mouse_tu_y,
                0,
                collision_map_list,
            )

            # Update pre render
            self._update_pre_render()

            # Get my neighbors
            adjacent_tile_obj_neighbors = self.get_adjacent_tiles(
                self.world_mouse_tu_x,
                self.world_mouse_tu_y,
                collision_map_list,
            )
            # Iterate each neighbors
            for neighbor_obj in adjacent_tile_obj_neighbors:
                # Unpack the neighbor object, get name and coords
                neighbor_tile_name = neighbor_obj["tile"]
                neighbor_world_tu_x = neighbor_obj["world_tu_x"]
                neighbor_world_tu_y = neighbor_obj["world_tu_y"]
                neighbor_world_snapped_x = neighbor_world_tu_x * TILE_SIZE
                neighbor_world_snapped_y = neighbor_world_tu_y * TILE_SIZE

                # Get neighbor sprite metadata
                neighbor_sprite_is_tile_mix = self.reformat_sprite_sheet_json_metadata[neighbor_tile_name]["sprite_is_tile_mix"]
                neighbor_sprite_x = self.reformat_sprite_sheet_json_metadata[neighbor_tile_name]["x"]
                neighbor_sprite_y = self.reformat_sprite_sheet_json_metadata[neighbor_tile_name]["y"]
                neighbor_sprite_tile_type = self.reformat_sprite_sheet_json_metadata[neighbor_tile_name]["sprite_tile_type"]

                # Neighbor not my kind?
                if neighbor_tile_name != self.selected_sprite_name:
                    # Neighbor not mixed?
                    if neighbor_sprite_is_tile_mix == 0:
                        # Skip this neighbor
                        continue

                # Draw autotile on surf with proper offset
                self._draw_autotile_sprite_on_given_pos(
                    neighbor_sprite_tile_type,
                    neighbor_sprite_x,
                    neighbor_sprite_y,
                    neighbor_world_tu_x,
                    neighbor_world_tu_y,
                    collision_map_list,
                    # surf,
                    neighbor_world_snapped_x,
                    neighbor_world_snapped_y,
                    neighbor_tile_name,
                )

    def _on_lmb_just_pressed_none_tile_type(
        self,
        collision_map_list: list[Any],
        selected_sprite_x: int,
        selected_sprite_y: int,
        selected_sprite_name: str,
    ) -> None:
        """
        If cursor region is empty, draw and set collision.
        """
        # All cells in cursor region empty
        if not self._is_cursor_region_collision_map_empty(collision_map_list):
            self._fill_cursor_region_collision_map_with_metadata(
                collision_map_list, selected_sprite_name, selected_sprite_x, selected_sprite_y
            )

            # Update pre render
            self._update_pre_render()

    def _on_lmb_just_pressed_blob_tile_type(
        self,
        collision_map_list: list[Any],
        selected_sprite_x: int,
        selected_sprite_y: int,
        selected_sprite_tile_type: str,
        selected_sprite_name: str,
    ) -> None:
        """
        If cursor region is empty, draw and set collision.
        Draw with correct autotile and tell neighbor to do it too.
        """
        # Get clicked cell
        found_tile = self.get_tile_from_collision_map_list(
            self.world_mouse_tu_x,
            self.world_mouse_tu_y,
            collision_map_list,
        )
        # Cell is empty
        if found_tile == 0:
            # Fill collision map with sprite name in cursor pos
            self.set_tile_from_collision_map_list(
                self.world_mouse_tu_x,
                self.world_mouse_tu_y,
                {
                    "name": selected_sprite_name,
                    "x": self.world_mouse_snapped_x,
                    "y": self.world_mouse_snapped_y,
                    "region_x": selected_sprite_x,
                    "region_y": selected_sprite_y,
                },
                collision_map_list,
            )

            # Draw autotile on surf with proper offset
            self._draw_autotile_sprite_on_given_pos(
                selected_sprite_tile_type,
                selected_sprite_x,
                selected_sprite_y,
                self.world_mouse_tu_x,
                self.world_mouse_tu_y,
                collision_map_list,
                # surf,
                self.world_mouse_snapped_x,
                self.world_mouse_snapped_y,
                selected_sprite_name,
            )

            # Get my neighbors
            adjacent_tile_obj_neighbors = self.get_adjacent_tiles(
                self.world_mouse_tu_x,
                self.world_mouse_tu_y,
                collision_map_list,
            )
            # Iterate each neighbors
            for neighbor_obj in adjacent_tile_obj_neighbors:
                # Unpack the neighbor object, get name and coords
                neighbor_tile_name = neighbor_obj["tile"]
                neighbor_world_tu_x = neighbor_obj["world_tu_x"]
                neighbor_world_tu_y = neighbor_obj["world_tu_y"]
                neighbor_world_snapped_x = neighbor_world_tu_x * TILE_SIZE
                neighbor_world_snapped_y = neighbor_world_tu_y * TILE_SIZE

                # Get neighbor sprite metadata
                neighbor_sprite_is_tile_mix = self.reformat_sprite_sheet_json_metadata[neighbor_tile_name]["sprite_is_tile_mix"]
                neighbor_sprite_x = self.reformat_sprite_sheet_json_metadata[neighbor_tile_name]["x"]
                neighbor_sprite_y = self.reformat_sprite_sheet_json_metadata[neighbor_tile_name]["y"]
                neighbor_sprite_tile_type = self.reformat_sprite_sheet_json_metadata[neighbor_tile_name]["sprite_tile_type"]

                # Neighbor not my kind?
                if neighbor_tile_name != self.selected_sprite_name:
                    # Neighbor not mixed?
                    if neighbor_sprite_is_tile_mix == 0:
                        # Skip this neighbor
                        continue

                # Draw autotile on surf with proper offset
                self._draw_autotile_sprite_on_given_pos(
                    neighbor_sprite_tile_type,
                    neighbor_sprite_x,
                    neighbor_sprite_y,
                    neighbor_world_tu_x,
                    neighbor_world_tu_y,
                    collision_map_list,
                    # surf,
                    neighbor_world_snapped_x,
                    neighbor_world_snapped_y,
                    neighbor_tile_name,
                )

    def _draw_autotile_sprite_on_given_pos(
        self,
        sprite_tile_type: str,
        sprite_x: int,
        sprite_y: int,
        sprite_world_tu_x: int,
        sprite_world_tu_y: int,
        selected_layer_collision_map: list[Any],
        # selected_layer_surf: pg.Surface,
        sprite_snapped_x: int,
        sprite_snapped_y: int,
        sprite_name: str,
    ) -> None:
        # Get the proper binary to offset dict
        binary_to_offset_dict = SPRITE_TILE_TYPE_BINARY_TO_OFFSET_DICT[sprite_tile_type]
        directions = SPRITE_TILE_TYPE_SPRITE_ADJACENT_NEIGHBOR_DIRECTIONS_LIST[sprite_tile_type]

        # Prepare top left with offset
        sprite_x_with_offset = sprite_x
        sprite_y_with_offset = sprite_y

        # Check my neighbours to determine my binary representation
        binary_value = self.get_surrounding_tile_value(
            sprite_world_tu_x,
            sprite_world_tu_y,
            selected_layer_collision_map,
            directions,
        )

        # Is binary available in map?
        if binary_value in binary_to_offset_dict:
            # Turn binary to offset obj
            offset_object = binary_to_offset_dict[binary_value]
            # Apply offset to top left
            sprite_x_with_offset = sprite_x + offset_object["x"]
            sprite_y_with_offset = sprite_y + offset_object["y"]

        # Override this sprite collision with new metadata
        self.set_tile_from_collision_map_list(
            sprite_world_tu_x,
            sprite_world_tu_y,
            {
                "name": sprite_name,
                "x": sprite_snapped_x,
                "y": sprite_snapped_y,
                "region_x": sprite_x_with_offset,
                "region_y": sprite_y_with_offset,
            },
            selected_layer_collision_map,
        )

        # Update pre render
        self._update_pre_render()

    def _fill_cursor_region_collision_map_with_metadata(
        self, collision_map: list, sprite_name: str, region_x: int, region_y: int
    ) -> None:
        # Fill collision map with sprite name in cursor area
        for cursor_tu_x in range(self.cursor_width_tu):
            for cursor_tu_y in range(self.cursor_height_tu):
                tu_x = self.world_mouse_tu_x + cursor_tu_x
                tu_y = self.world_mouse_tu_y + cursor_tu_y
                world_mouse_x_snapped = self.world_mouse_snapped_x + (cursor_tu_x * TILE_SIZE)
                world_mouse_y_snapped = self.world_mouse_snapped_y + (cursor_tu_y * TILE_SIZE)
                region_x_with_offset = region_x + (cursor_tu_x * TILE_SIZE)
                region_y_with_offset = region_y + (cursor_tu_y * TILE_SIZE)
                # TODO: top left of sprite sheet
                # TODO: then fill with region
                self.set_tile_from_collision_map_list(
                    tu_x,
                    tu_y,
                    {
                        "name": sprite_name,
                        "x": world_mouse_x_snapped,
                        "y": world_mouse_y_snapped,
                        "region_x": region_x_with_offset,
                        "region_y": region_y_with_offset,
                    },
                    collision_map,
                )

    def _is_cursor_region_collision_map_empty(self, collision_map: list) -> bool:
        # Iterate cursor area
        found_occupied = False
        for cursor_tu_x in range(self.cursor_width_tu):
            if found_occupied:
                break
            for cursor_tu_y in range(self.cursor_height_tu):
                tu_x = self.world_mouse_tu_x + cursor_tu_x
                tu_y = self.world_mouse_tu_y + cursor_tu_y
                # Get each tile in cursor area
                found_tile = self.get_tile_from_collision_map_list(
                    tu_x,
                    tu_y,
                    collision_map,
                )
                # 1 tile in cursor area is occupied?
                if found_tile != 0:
                    # Break
                    found_occupied = True
                    break

        return found_occupied

    def _move_camera(self, dt: int) -> None:
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

    def _draw_world_grid(self) -> None:
        blit_sequence = []
        for i in range(WORLD_WIDTH_RU):
            vertical_line_x_position: float = (WORLD_CELL_SIZE * i - self.camera.rect.x) % WORLD_WIDTH
            blit_sequence.append(
                (
                    self.grid_world_vertical_line_surf,
                    (vertical_line_x_position, 0.0),
                )
            )
            horizontal_line_y_position: float = (WORLD_CELL_SIZE * i - self.camera.rect.y) % WORLD_HEIGHT
            blit_sequence.append(
                (
                    self.grid_world_horizontal_line_surf,
                    (0.0, horizontal_line_y_position),
                )
            )

        NATIVE_SURF.fblits(blit_sequence)

    def draw_grid(self) -> None:
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

    def get_tile_from_world_collision_map_list(
        self,
        world_ru_x: int,
        world_ru_y: int,
    ) -> Any:
        """
        Returns -1 if out of bounds
        Because camera needs extra 1 and thus may get out of bound.
        """
        if 0 <= world_ru_x < WORLD_WIDTH_RU and 0 <= world_ru_y < WORLD_HEIGHT_RU:
            return self.world_collision_map_list[world_ru_y * WORLD_WIDTH_RU + world_ru_x]
        else:
            return -1

    def set_tile_from_world_collision_map_list(
        self,
        world_ru_x: int,
        world_ru_y: int,
        value: Any,
    ) -> None | int:
        """
        Returns -1 if out of bounds
        Because camera needs extra 1 and thus may get out of bound.
        """
        if 0 <= world_ru_x < WORLD_WIDTH_RU and 0 <= world_ru_y < WORLD_HEIGHT_RU:
            self.world_collision_map_list[world_ru_y * WORLD_WIDTH_RU + world_ru_x] = value
            return None
        else:
            return -1

    def set_input_text(self, value: str) -> None:
        self.input_text = value
        self.input_rect = FONT.get_rect(self.input_text)
        self.input_rect.center = NATIVE_RECT.center

    def set_prompt_text(self, value: str) -> None:
        local_settings_dict_enter = pg.key.name(self.game.get_one_local_settings_dict_value("enter"))
        self.prompt_text = f"{value} " f"hit {local_settings_dict_enter} " "to proceed"
        self.prompt_rect = FONT.get_rect(self.prompt_text)
        self.prompt_rect.center = NATIVE_RECT.center
        self.prompt_rect.y -= FONT_HEIGHT + 1

    def get_tile_from_collision_map_list(
        self,
        world_tu_x: int,
        world_tu_y: int,
        collision_map_list: list,
    ) -> Any:
        """
        Returns -1 if out of bounds
        Because camera needs extra 1 and thus may get out of bound.
        """
        if 0 <= world_tu_x < self.room_width_tu and 0 <= world_tu_y < self.room_height_tu:
            return collision_map_list[world_tu_y * self.room_width_tu + world_tu_x]
        else:
            return -1

    def set_tile_from_collision_map_list(
        self,
        world_tu_x: int,
        world_tu_y: int,
        value: Any,
        collision_map_list: list,
    ) -> None | int:
        """
        Returns -1 if out of bounds
        Because camera needs extra 1 and thus may get out of bound.
        """
        if 0 <= world_tu_x < self.room_width_tu and 0 <= world_tu_y < self.room_height_tu:
            collision_map_list[world_tu_y * self.room_width_tu + world_tu_x] = value
            return None
        else:
            return -1

    def get_surrounding_tile_value(
        self,
        world_tu_x: int,
        world_tu_y: int,
        collision_map_list: list,
        directions: list[tuple[tuple[int, int], int]],
    ) -> int:
        """
        Returns an integer representing the presence of surrounding tiles using 8-bit directional values.
        A corner tile is included only if it has both adjacent neighbors in the cardinal directions.
        """
        # Cardinal directions for checking neighbor presence
        cardinal_directions = {
            (-1, -1): [(-1, 0), (0, -1)],  # North West
            (1, -1): [(1, 0), (0, -1)],  # North East
            (-1, 1): [(-1, 0), (0, 1)],  # South West
            (1, 1): [(1, 0), (0, 1)],  # South East
        }
        # The bit collected value
        tile_value = 0
        # Check my neigbors
        for (dx, dy), value in directions:
            # Check this pos tile
            adjacent_x = world_tu_x + dx
            adjacent_y = world_tu_y + dy
            tile = self.get_tile_from_collision_map_list(
                adjacent_x,
                adjacent_y,
                collision_map_list,
            )
            # Found something
            if tile != -1 and tile != 0:
                # Not my kind and not mixed? Skip this one
                neighbor_tile_name = self.reformat_sprite_sheet_json_metadata[tile["name"]]["sprite_name"]
                just_added_sprite_name = self.reformat_sprite_sheet_json_metadata[self.selected_sprite_name]["sprite_name"]
                if neighbor_tile_name != just_added_sprite_name:
                    neighbor_sprite_is_tile_mix = self.reformat_sprite_sheet_json_metadata[neighbor_tile_name][
                        "sprite_is_tile_mix"
                    ]
                    if not neighbor_sprite_is_tile_mix:
                        continue
                # For corner tiles, check that they have both neighbor in the cardinal directions
                if (dx, dy) in cardinal_directions:
                    has_cardinal_neighbor = True
                    for cdx, cdy in cardinal_directions[(dx, dy)]:
                        cardinal_x = world_tu_x + cdx
                        cardinal_y = world_tu_y + cdy
                        cardinal_tile = self.get_tile_from_collision_map_list(
                            cardinal_x,
                            cardinal_y,
                            collision_map_list,
                        )
                        if cardinal_tile == -1 or cardinal_tile == 0:
                            has_cardinal_neighbor = False
                            break
                    # Corners got cardinals? Collect
                    if has_cardinal_neighbor:
                        tile_value += value
                # Collect
                else:
                    tile_value += value
        # Bit is ready
        return tile_value

    def get_adjacent_tiles(
        self,
        world_tu_x: int,
        world_tu_y: int,
        collision_map_list: list,
    ) -> list:
        """
        Returns a list of 8 adjacent tiles around the specified coordinates.
        Each tile is represented as object with tile value as key and coords as values
        """
        adjacent_tiles = []
        # Directions: top-left, top, top-right, left, right, bottom-left, bottom, bottom-right
        directions = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]

        for dx, dy in directions:
            adjacent_x = world_tu_x + dx
            adjacent_y = world_tu_y + dy

            tile = self.get_tile_from_collision_map_list(
                adjacent_x,
                adjacent_y,
                collision_map_list,
            )

            # Found something
            if tile != -1 and tile != 0:
                adjacent_tiles.append(
                    {
                        "tile": tile["name"],
                        "world_tu_x": adjacent_x,
                        "world_tu_y": adjacent_y,
                    }
                )

        return adjacent_tiles
