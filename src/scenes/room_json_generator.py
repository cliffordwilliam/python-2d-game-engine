from enum import auto
from enum import Enum
from json import load
from os import listdir
from os.path import exists
from os.path import join
from typing import TYPE_CHECKING

from constants import FONT
from constants import FONT_HEIGHT
from constants import JSONS_ROOMS_DIR_PATH
from constants import NATIVE_HEIGHT
from constants import NATIVE_RECT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import OGGS_PATHS_DICT
from constants import pg
from constants import ROOM_HEIGHT
from constants import ROOM_JSON_PROPERTIES
from constants import ROOM_WIDTH
from constants import TILE_SIZE
from constants import WORLD_CELL_SIZE
from constants import WORLD_HEIGHT
from constants import WORLD_HEIGHT_RU
from constants import WORLD_WIDTH
from constants import WORLD_WIDTH_RU
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
    class State(Enum):
        JUST_ENTERED_SCENE = auto()
        OPENING_SCENE_CURTAIN = auto()
        OPENED_SCENE_CURTAIN = auto()
        ADD_OTHER_SPRITES = auto()
        FILE_NAME_QUERY = auto()
        SPRITE_SHEET_PNG_PATH_QUERY = auto()
        SPRITE_SHEET_JSON_PATH_QUERY = auto()
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
        self._draw_world_grid()
        self._setup_music()
        self.state_machine_update = self._create_state_machine_update()
        self.state_machine_draw = self._create_state_machine_draw()

        # First selected world cell rect
        self.first_world_selected_tile_rect = pg.FRect(0.0, 0.0, WORLD_CELL_SIZE, WORLD_CELL_SIZE)
        self.second_world_selected_tile_rect = pg.FRect(0.0, 0.0, WORLD_CELL_SIZE, WORLD_CELL_SIZE)
        self.combined_world_selected_tile_rect = pg.FRect(0.0, 0.0, WORLD_CELL_SIZE, WORLD_CELL_SIZE)
        self.screen_combined_world_selected_tile_rect_x = 0.0
        self.screen_combined_world_selected_tile_rect_y = 0.0
        self.combined_world_selected_tile_rect_width_tu = 0
        self.combined_world_selected_tile_rect_height_tu = 0
        self.combined_world_selected_tile_rect_x_tu = 0
        self.combined_world_selected_tile_rect_y_tu = 0

    # Setups
    def _setup_curtain(self) -> None:
        """Setup curtain with event listeners."""
        self.curtain: Curtain = Curtain(
            duration=1000.0,
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
        self.entry_delay_timer: Timer = Timer(duration=1000.0)
        self.entry_delay_timer.add_event_listener(self.on_entry_delay_timer_end, Timer.END)

        self.exit_delay_timer: Timer = Timer(duration=1000.0)
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
        self.room_name: str = ""
        self.room_topleft_x: int = 0
        self.room_topleft_y: int = 0

        # Sprite sheet surf
        self.sprite_sheet_png_path: (None | str) = None
        self.sprite_sheet_surf: (None | pg.Surface) = None

        # To be saved json
        self.file_name: str = ""
        # self.animation_json: dict = {}
        # self.animation_sprites_list: list = []

    def _setup_camera(self) -> None:
        self.camera_anchor_vector: Vector2 = Vector2(0.0, 0.0)
        self.camera: Camera = Camera(
            self.camera_anchor_vector,
            # REMOVE IN BUILD
            self.game,
        )
        self.camera_speed: float = 0.09  # Px / ms

    def _setup_collision_map(self) -> None:
        # World
        self.world_collision_map_list: list[(int | str)] = [0 for _ in range(WORLD_WIDTH_RU * WORLD_HEIGHT_RU)]

        # Room
        # self.room_collision_map_list: list[int] = []
        # self.room_collision_map_width_tu: int = 0
        # self.room_collision_map_height_tu: int = 0

    def _setup_surfs(self) -> None:
        # Selected surf marker
        self.selected_surf_marker: pg.Surface = pg.Surface((WORLD_CELL_SIZE, WORLD_CELL_SIZE))
        self.selected_surf_marker.fill("red")

        # Grid world surf
        self.grid_world_horizontal_line_surf: pg.Surface = pg.Surface((WORLD_WIDTH, 1))
        self.grid_world_horizontal_line_surf.fill(self.grid_line_color)
        self.grid_world_vertical_line_surf: pg.Surface = pg.Surface((1, WORLD_HEIGHT))
        self.grid_world_vertical_line_surf.fill(self.grid_line_color)

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

    def _create_state_machine_update(self) -> StateMachine:
        """Create state machine for update."""
        return StateMachine(
            initial_state=RoomJsonGenerator.State.JUST_ENTERED_SCENE,
            state_handlers={
                RoomJsonGenerator.State.JUST_ENTERED_SCENE: self._JUST_ENTERED_SCENE,
                RoomJsonGenerator.State.OPENING_SCENE_CURTAIN: self._OPENING_SCENE_CURTAIN,
                RoomJsonGenerator.State.OPENED_SCENE_CURTAIN: self._OPENED_SCENE_CURTAIN,
                RoomJsonGenerator.State.ADD_OTHER_SPRITES: self._ADD_OTHER_SPRITES,
                RoomJsonGenerator.State.FILE_NAME_QUERY: self._FILE_NAME_QUERY,
                RoomJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY: self._SPRITE_SHEET_PNG_PATH_QUERY,
                RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY: self._SPRITE_SHEET_JSON_PATH_QUERY,
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
                    RoomJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY,
                ): self._FILE_NAME_QUERY_to_SPRITE_SHEET_PNG_PATH_QUERY,
                (
                    RoomJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY,
                    RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY,
                ): self._SPRITE_SHEET_PNG_PATH_QUERY_to_SPRITE_SHEET_JSON_PATH_QUERY,
                (
                    RoomJsonGenerator.State.CLOSING_SCENE_CURTAIN,
                    RoomJsonGenerator.State.CLOSED_SCENE_CURTAIN,
                ): self._CLOSING_SCENE_CURTAIN_to_CLOSED_SCENE_CURTAIN,
            },
        )

    def _create_state_machine_draw(self) -> StateMachine:
        """Create state machine for draw."""
        return StateMachine(
            initial_state=RoomJsonGenerator.State.JUST_ENTERED_SCENE,
            state_handlers={
                RoomJsonGenerator.State.JUST_ENTERED_SCENE: self._NOTHING,
                RoomJsonGenerator.State.OPENING_SCENE_CURTAIN: self._QUERIES,
                RoomJsonGenerator.State.OPENED_SCENE_CURTAIN: self._ADD_ROOM_DRAW,
                RoomJsonGenerator.State.ADD_OTHER_SPRITES: self._ADD_OTHER_SPRITES_DRAW,
                RoomJsonGenerator.State.FILE_NAME_QUERY: self._QUERIES,
                RoomJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY: self._QUERIES,
                RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY: self._QUERIES,
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
        # Draw world surf
        NATIVE_SURF.blit(self.world_surf, (0, 0))
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

        # Draw cursor
        # Get mouse position
        mouse_position_tuple: tuple[int, int] = pg.mouse.get_pos()
        mouse_position_x_tuple: int = mouse_position_tuple[0]
        mouse_position_y_tuple: int = mouse_position_tuple[1]
        # Scale mouse position
        mouse_position_x_tuple_scaled: int | float = mouse_position_x_tuple // self.game.local_settings_dict["resolution_scale"]
        mouse_position_y_tuple_scaled: int | float = mouse_position_y_tuple // self.game.local_settings_dict["resolution_scale"]
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

    def _ADD_OTHER_SPRITES_DRAW(self, _dt: int) -> None:
        # Clear
        NATIVE_SURF.fill(self.clear_color)

        # Draw world surf
        NATIVE_SURF.blit(self.world_surf, (0, 0))

        # Draw cursor
        # Get mouse position
        mouse_position_tuple: tuple[int, int] = pg.mouse.get_pos()
        mouse_position_x_tuple: int = mouse_position_tuple[0]
        mouse_position_y_tuple: int = mouse_position_tuple[1]
        # Scale mouse position
        mouse_position_x_tuple_scaled: int | float = mouse_position_x_tuple // self.game.local_settings_dict["resolution_scale"]
        mouse_position_y_tuple_scaled: int | float = mouse_position_y_tuple // self.game.local_settings_dict["resolution_scale"]
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
        self.combined_world_selected_tile_rect = self.first_world_selected_tile_rect.union(self.second_world_selected_tile_rect)
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
                found_tile_lmb_pressed: (int | str) = self.get_tile_from_world_collision_map_list(
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
            is_lmb_just_pressed_occupied: bool = False
            if self.game_event_handler.is_lmb_just_pressed:
                # Check if selection is all empty cells
                # Iterate size to check all empty
                self.combined_world_selected_tile_rect_width_tu = int(
                    self.combined_world_selected_tile_rect.width // WORLD_CELL_SIZE
                )
                self.combined_world_selected_tile_rect_height_tu = int(
                    self.combined_world_selected_tile_rect.height // WORLD_CELL_SIZE
                )
                self.combined_world_selected_tile_rect_x_tu = int(self.combined_world_selected_tile_rect.x // WORLD_CELL_SIZE)
                self.combined_world_selected_tile_rect_y_tu = int(self.combined_world_selected_tile_rect.y // WORLD_CELL_SIZE)
                for world_mouse_tu_xi in range(self.combined_world_selected_tile_rect_width_tu):
                    for world_mouse_tu_yi in range(self.combined_world_selected_tile_rect_height_tu):
                        world_mouse_tu_x: int = self.combined_world_selected_tile_rect_x_tu + world_mouse_tu_xi
                        world_mouse_tu_y: int = self.combined_world_selected_tile_rect_y_tu + world_mouse_tu_yi
                        # Get each one in room_collision_map_list
                        found_tile_lmb_pressed: (int | str) = self.get_tile_from_world_collision_map_list(
                            world_mouse_tu_x,
                            world_mouse_tu_y,
                        )
                        # At least 1 of them is occupied? Return
                        if found_tile_lmb_pressed != 0:
                            is_lmb_just_pressed_occupied = True
                # All cells are empty
                if not is_lmb_just_pressed_occupied:
                    # TODO: setup the new file room for editing from here
                    # No need to fill, fill is done from first time read json rooms
                    pass
                    # Exit to edit state
                    # self.curtain.go_to_opaque()

        # Update curtain
        self.curtain.update(dt)

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

    def _SPRITE_SHEET_PNG_PATH_QUERY(self, dt: int) -> None:
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.game_event_handler.this_frame_event:
                if self.game_event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept
                    if self.game_event_handler.this_frame_event.key == pg.K_RETURN:
                        if exists(self.input_text) and self.input_text.endswith(".png"):
                            # Setup the sprite sheet surf
                            self.sprite_sheet_png_path = self.input_text
                            self.sprite_sheet_surf = pg.image.load(self.sprite_sheet_png_path).convert_alpha()
                            self.curtain.go_to_opaque()
                        else:
                            self.set_input_text("png path does not exist!")
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
                            # Setup the sprite sheet surf
                            print(self.input_text)
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

    def _CLOSING_SCENE_CURTAIN(self, dt: int) -> None:
        self.curtain.update(dt)

    def _CLOSED_SCENE_CURTAIN(self, dt: int) -> None:
        self.exit_delay_timer.update(dt)

    # State transitions
    def _JUST_ENTERED_SCENE_to_OPENING_SCENE_CURTAIN(self) -> None:
        self.curtain.go_to_invisible()

    def _OPENING_SCENE_CURTAIN_to_OPENED_SCENE_CURTAIN(self) -> None:
        # Read all json room and mark it on grid
        for filename in listdir(JSONS_ROOMS_DIR_PATH):
            if filename.endswith(".json"):
                # Construct the full file path
                file_path = join(JSONS_ROOMS_DIR_PATH, filename)

                # Open and read the JSON file
                with open(file_path, "r") as file:
                    data = load(file)

                    # Extract and print the desired properties
                    extracted_data = {prop: data.get(prop) for prop in ROOM_JSON_PROPERTIES}
                    # Draw marks on the world surf
                    file_name = extracted_data["file_name"]
                    room_x_ru = extracted_data["room_x_ru"]
                    room_y_ru = extracted_data["room_y_ru"]
                    room_scale_x = extracted_data["room_scale_x"]
                    room_scale_y = extracted_data["room_scale_y"]
                    room_x = room_x_ru * WORLD_CELL_SIZE
                    room_y = room_y_ru * WORLD_CELL_SIZE
                    room_cell_width = room_scale_x * WORLD_CELL_SIZE
                    room_cell_height = room_scale_y * WORLD_CELL_SIZE
                    sprite_room_map_body_color = extracted_data["sprite_room_map_body_color"]
                    sprite_room_map_sub_division_color = extracted_data["sprite_room_map_sub_division_color"]
                    sprite_room_map_border_color = extracted_data["sprite_room_map_border_color"]

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

    def _FILE_NAME_QUERY_to_SPRITE_SHEET_PNG_PATH_QUERY(self) -> None:
        # Reset the input text
        self.set_input_text("")
        # Set my prompt text
        self.set_prompt_text("type the png path to be loaded,")

    def _SPRITE_SHEET_PNG_PATH_QUERY_to_SPRITE_SHEET_JSON_PATH_QUERY(self) -> None:
        # Reset the input text
        self.set_input_text("")
        # Set my prompt text
        self.set_prompt_text("type the json path to be loaded,")

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

    def on_curtain_opaque(self) -> None:
        if self.state_machine_update.state == RoomJsonGenerator.State.OPENED_SCENE_CURTAIN:
            self.state_machine_update.change_state(RoomJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY)
            self.state_machine_draw.change_state(RoomJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY)
            self.curtain.go_to_invisible()
        elif self.state_machine_update.state == RoomJsonGenerator.State.ADD_OTHER_SPRITES:
            self.state_machine_update.change_state(RoomJsonGenerator.State.FILE_NAME_QUERY)
            self.state_machine_draw.change_state(RoomJsonGenerator.State.FILE_NAME_QUERY)
            self.curtain.go_to_invisible()
        elif self.state_machine_update.state == RoomJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY:
            self.state_machine_update.change_state(RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY)
            self.state_machine_draw.change_state(RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY)
            self.curtain.go_to_invisible()
        elif self.state_machine_update.state == RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY:
            pass

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
                "text": (f"sprite sheet json generator " f"state: {self.state_machine_update.state.name}"),
            }
        )

        # All states here can go to options
        if self.game_event_handler.is_pause_just_pressed:
            # Update and draw options menu, stop my update
            self.game.set_is_options_menu_active(True)

        self.state_machine_update.handle(dt)

    # Helpers
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

        self.world_surf.fblits(blit_sequence)

    def get_tile_from_world_collision_map_list(
        self,
        world_ru_x: int,
        world_ru_y: int,
    ) -> int | str:
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
        value: int | str,
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
        self.prompt_text = f"{value} " f"hit {pg.key.name(self.game.local_settings_dict['enter'])} " "to proceed"
        self.prompt_rect = FONT.get_rect(self.prompt_text)
        self.prompt_rect.center = NATIVE_RECT.center
        self.prompt_rect.y -= FONT_HEIGHT + 1
