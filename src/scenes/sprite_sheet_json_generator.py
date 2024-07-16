from enum import auto
from enum import Enum
from os.path import exists
from typing import Any
from typing import TYPE_CHECKING

from constants import FONT
from constants import FONT_HEIGHT
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
from typeguard import typechecked

if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class SpriteSheetJsonGenerator:
    class State(Enum):
        JUST_ENTERED_SCENE = auto()
        OPENING_SCENE_CURTAIN = auto()
        OPENED_SCENE_CURTAIN = auto()
        SPRITE_SHEET_PNG_PATH_QUERY = auto()
        SPRITE_NAME_QUERY = auto()
        SPRITE_LAYER_QUERY = auto()
        SPRITE_TYPE_QUERY = auto()
        SPRITE_TILE_TYPE_QUERY = auto()
        SPRITE_TILE_MIX_QUERY = auto()
        ADD_SPRITES = auto()
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
        self._setup_loop_options()
        self._setup_music()
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
        self.file_name: str = ""
        self.sprite_name: str = ""
        self.sprite_layer: int = 0
        self.sprite_type: str = ""
        self.sprite_tile_type: str = ""
        self.sprite_is_tile_mix: int = 0

        # Sprite sheet surf
        self.sprite_sheet_png_path: Any = None
        self.sprite_sheet_surf: Any = None
        self.sprite_sheet_rect: Any = None

        # To be saved json
        self.sprite_json: dict = {}
        self.sprite_region: dict = {}

    def _setup_camera(self) -> None:
        self.camera_anchor_vector: Vector2 = Vector2(0.0, 0.0)
        self.camera: Camera = Camera(
            self.camera_anchor_vector,
            # REMOVE IN BUILD
            self.game,
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
        self.grid_horizontal_line_surf.fill(self.grid_line_color)
        self.grid_vertical_line_surf: pg.Surface = pg.Surface((1, NATIVE_HEIGHT))
        self.grid_vertical_line_surf.fill(self.grid_line_color)

    def _setup_loop_options(self) -> None:
        self.selected_choice_after_add_sprites_state: int = 0
        self.save_and_quit_choice_after_add_sprites_state: int = 1
        self.save_and_redo_choice_after_add_sprites_state: int = 2
        self.redo_choice_after_add_sprites_state: int = 3
        self.quit_choice_after_add_sprites_state: int = 4

    def _setup_music(self) -> None:
        # Load editor screen music. Played in my set state
        self.game_music_manager.set_current_music_path(
            OGGS_PATHS_DICT["xdeviruchi_take_some_rest_and_eat_some_food.ogg"]
        )
        self.game_music_manager.play_music(-1, 0.0, 0)

    def _create_state_machine_update(self) -> StateMachine:
        """Create state machine for update."""
        return StateMachine(
            initial_state=SpriteSheetJsonGenerator.State.JUST_ENTERED_SCENE,
            state_handlers={
                SpriteSheetJsonGenerator.State.JUST_ENTERED_SCENE: self._JUST_ENTERED_SCENE,
                SpriteSheetJsonGenerator.State.OPENING_SCENE_CURTAIN: self._OPENING_SCENE_CURTAIN,
                SpriteSheetJsonGenerator.State.OPENED_SCENE_CURTAIN: self._OPENED_SCENE_CURTAIN,
                SpriteSheetJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY: self._SPRITE_SHEET_PNG_PATH_QUERY,
                SpriteSheetJsonGenerator.State.SPRITE_NAME_QUERY: self._SPRITE_NAME_QUERY,
                SpriteSheetJsonGenerator.State.SPRITE_LAYER_QUERY: self._SPRITE_LAYER_QUERY,
                SpriteSheetJsonGenerator.State.SPRITE_TYPE_QUERY: self._SPRITE_TYPE_QUERY,
                SpriteSheetJsonGenerator.State.SPRITE_TILE_TYPE_QUERY: self._SPRITE_TILE_TYPE_QUERY,
                SpriteSheetJsonGenerator.State.SPRITE_TILE_MIX_QUERY: self._SPRITE_TILE_MIX_QUERY,
                SpriteSheetJsonGenerator.State.ADD_SPRITES: self._ADD_SPRITES,
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
                    SpriteSheetJsonGenerator.State.SPRITE_NAME_QUERY,
                ): self._SPRITE_SHEET_PNG_PATH_QUERY_to_SPRITE_NAME_QUERY,
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
            },
        )

    def _create_state_machine_draw(self) -> StateMachine:
        """Create state machine for draw."""
        return StateMachine(
            initial_state=SpriteSheetJsonGenerator.State.JUST_ENTERED_SCENE,
            state_handlers={
                SpriteSheetJsonGenerator.State.JUST_ENTERED_SCENE: self._NOTHING,
                SpriteSheetJsonGenerator.State.OPENING_SCENE_CURTAIN: self._QUERIES,
                SpriteSheetJsonGenerator.State.OPENED_SCENE_CURTAIN: self._QUERIES,
                SpriteSheetJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.SPRITE_NAME_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.SPRITE_LAYER_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.SPRITE_TYPE_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.SPRITE_TILE_TYPE_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.SPRITE_TILE_MIX_QUERY: self._QUERIES,
                SpriteSheetJsonGenerator.State.ADD_SPRITES: self._ADD_SPRITES_DRAW,
            },
            transition_actions={},
        )

    # State draw logics
    def _NOTHING(self, _dt: int) -> None:
        pass

    def _QUERIES(self, _dt: int) -> None:
        # Clear
        NATIVE_SURF.fill(self.clear_color)
        # Draw grid with camera offset
        self.draw_grid()
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

        # Draw grid
        self.draw_grid()

        # Draw selected sprite sheet with camera offset
        NATIVE_SURF.blit(
            self.sprite_sheet_surf,
            (
                -self.camera.rect.x,
                -self.camera.rect.y,
            ),
        )

        # Draw cursor
        # Get mouse position
        mouse_position_tuple: tuple[int, int] = pg.mouse.get_pos()
        mouse_position_x_tuple: int = mouse_position_tuple[0]
        mouse_position_y_tuple: int = mouse_position_tuple[1]
        # Scale mouse position
        mouse_position_x_tuple_scaled: int | float = (
            mouse_position_x_tuple // self.game.local_settings_dict["resolution_scale"]
        )
        mouse_position_y_tuple_scaled: int | float = (
            mouse_position_y_tuple // self.game.local_settings_dict["resolution_scale"]
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

    # State logics
    def _JUST_ENTERED_SCENE(self, dt: int) -> None:
        self.entry_delay_timer.update(dt)

    def _OPENING_SCENE_CURTAIN(self, dt: int) -> None:
        self.curtain.update(dt)

    def _OPENED_SCENE_CURTAIN(self, dt: int) -> None:
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.game_event_handler.this_frame_event:
                if self.game_event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept
                    if self.game_event_handler.this_frame_event.key == pg.K_RETURN:
                        if self.input_text != "":
                            self.file_name = self.input_text
                            # Close curtain
                            # Exit to SPRITE_SHEET_PNG_PATH_QUERY
                            self.curtain.go_to_opaque()
                    # Delete
                    elif self.game_event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        # Play text
                        self.game_sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add
                    else:
                        new_value = self.input_text + self.game_event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        # Play text
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
                            # Setup the sprite sheet data
                            self.sprite_sheet_png_path = self.input_text
                            self.sprite_sheet_surf = pg.image.load(self.sprite_sheet_png_path).convert_alpha()
                            self.sprite_sheet_rect = self.sprite_sheet_surf.get_rect()
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
                            self.init_room_collision_map_list(
                                sprite_sheet_width_tu,
                                sprite_sheet_height_tu,
                            )
                            # Exit to SPRITE_SIZE_QUERY
                            # Close curtain to exit to SPRITE_SIZE_QUERY
                            self.curtain.go_to_opaque()
                        else:
                            self.set_input_text("png path does not exist!")
                    # Delete
                    elif self.game_event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        # Play text
                        self.game_sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add
                    else:
                        new_value = self.input_text + self.game_event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        # Play text
                        self.game_sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_NAME_QUERY(self, dt: int) -> None:
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.game_event_handler.this_frame_event:
                if self.game_event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept
                    if self.game_event_handler.this_frame_event.key == pg.K_RETURN:
                        if self.input_text != "":
                            self.sprite_name = self.input_text
                            # Close curtain
                            # Exit to SPRITE_SHEET_PNG_PATH_QUERY
                            self.curtain.go_to_opaque()
                    # Delete
                    elif self.game_event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        # Play text
                        self.game_sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add
                    else:
                        new_value = self.input_text + self.game_event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        # Play text
                        self.game_sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_LAYER_QUERY(self, dt: int) -> None:
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.game_event_handler.this_frame_event:
                if self.game_event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept
                    if self.game_event_handler.this_frame_event.key == pg.K_RETURN:
                        if self.input_text.isdigit():
                            # Setup the sprite_size
                            self.sprite_layer = max(int(self.input_text), 0)
                            # Exit to ADD_SPRITES
                            # Close curtain to exit to ADD_SPRITES
                            self.curtain.go_to_opaque()
                        else:
                            self.set_input_text("type int only please!")
                    # Delete
                    elif self.game_event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        # Play text
                        self.game_sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add
                    else:
                        new_value = self.input_text + self.game_event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        # Play text
                        self.game_sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_TYPE_QUERY(self, dt: int) -> None:
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.game_event_handler.this_frame_event:
                if self.game_event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept
                    if self.game_event_handler.this_frame_event.key == pg.K_RETURN:
                        if self.input_text != "":
                            self.sprite_type = self.input_text
                            # Close curtain
                            # Exit to SPRITE_SHEET_PNG_PATH_QUERY
                            self.curtain.go_to_opaque()
                    # Delete
                    elif self.game_event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        # Play text
                        self.game_sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add
                    else:
                        new_value = self.input_text + self.game_event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        # Play text
                        self.game_sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_TILE_TYPE_QUERY(self, dt: int) -> None:
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.game_event_handler.this_frame_event:
                if self.game_event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept
                    if self.game_event_handler.this_frame_event.key == pg.K_RETURN:
                        if self.input_text != "":
                            self.sprite_tile_type = self.input_text
                            # Close curtain
                            # Exit to SPRITE_SHEET_PNG_PATH_QUERY
                            self.curtain.go_to_opaque()
                    # Delete
                    elif self.game_event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        # Play text
                        self.game_sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add
                    else:
                        new_value = self.input_text + self.game_event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        # Play text
                        self.game_sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_TILE_MIX_QUERY(self, dt: int) -> None:
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.game_event_handler.this_frame_event:
                if self.game_event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept
                    if self.game_event_handler.this_frame_event.key == pg.K_RETURN:
                        if self.input_text in ["y", "n"]:
                            if self.input_text == "y":
                                self.sprite_is_tile_mix = 1
                            elif self.input_text == "n":
                                self.sprite_is_tile_mix = 0
                            # Close curtain
                            # Exit to SPRITE_SHEET_PNG_PATH_QUERY
                            self.curtain.go_to_opaque()
                        else:
                            self.set_input_text("type y or n only please!")
                    # Delete
                    elif self.game_event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        # Play text
                        self.game_sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add
                    else:
                        new_value = self.input_text + self.game_event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        # Play text
                        self.game_sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain
        self.curtain.update(dt)

    def _ADD_SPRITES(self, dt: int) -> None:
        """
        - Move camera and add frames to be saved.
        - Updates curtain alpha.
        """
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Camera movement
            # Get direction_horizontal
            direction_horizontal: int = (
                self.game_event_handler.is_right_pressed - self.game_event_handler.is_left_pressed
            )
            # Update camera anchor position with direction and speed
            self.camera_anchor_vector.x += direction_horizontal * self.camera_speed * dt
            # Get direction_vertical
            direction_vertical: int = self.game_event_handler.is_down_pressed - self.game_event_handler.is_up_pressed
            # Update camera anchor position with direction and speed
            self.camera_anchor_vector.y += direction_vertical * self.camera_speed * dt
            # Lerp camera position to target camera anchor
            self.camera.update(dt)

        # Update curtain
        self.curtain.update(dt)

    # State transitions
    def _JUST_ENTERED_SCENE_to_OPENING_SCENE_CURTAIN(self) -> None:
        self.curtain.go_to_invisible()

    def _OPENING_SCENE_CURTAIN_to_OPENED_SCENE_CURTAIN(self) -> None:
        # Reset the input text
        self.set_input_text("")
        # Set my prompt text
        self.set_prompt_text("type the file name to be saved,")

    def _OPENED_SCENE_CURTAIN_to_SPRITE_SHEET_PNG_PATH_QUERY(self) -> None:
        # Reset the input text
        self.set_input_text("")
        # Set my prompt text
        self.set_prompt_text("type the png path to be loaded,")

    def _SPRITE_SHEET_PNG_PATH_QUERY_to_SPRITE_NAME_QUERY(self) -> None:
        # Reset the input text
        self.set_input_text("")
        # Set my prompt text
        self.set_prompt_text("type the sprite name,")

    def _SPRITE_NAME_QUERY_to_SPRITE_LAYER_QUERY(self) -> None:
        # Reset the input text
        self.set_input_text("")
        # Set my prompt text
        self.set_prompt_text("type the sprite layer,")

    def _SPRITE_LAYER_QUERY_to_SPRITE_TYPE_QUERY(self) -> None:
        # Reset the input text
        self.set_input_text("")
        # Set my prompt text
        self.set_prompt_text("type the sprite type,")

    def _SPRITE_TYPE_QUERY_to_SPRITE_TILE_TYPE_QUERY(self) -> None:
        # Reset the input text
        self.set_input_text("")
        # Set my prompt text
        self.set_prompt_text("type the sprite tile type,")

    def _SPRITE_TILE_TYPE_QUERY_to_SPRITE_TILE_MIX_QUERY(self) -> None:
        # Reset the input text
        self.set_input_text("")
        # Set my prompt text
        self.set_prompt_text("does the tile mix (y/n)?")

    def _SPRITE_TILE_MIX_QUERY_to_ADD_SPRITES(self) -> None:
        pass

    # Callbacks
    def on_entry_delay_timer_end(self) -> None:
        self.state_machine_update.change_state(SpriteSheetJsonGenerator.State.OPENING_SCENE_CURTAIN)
        self.state_machine_draw.change_state(SpriteSheetJsonGenerator.State.OPENING_SCENE_CURTAIN)

    def on_exit_delay_timer_end(self) -> None:
        # Load title screen music. Played in my set state
        self.game_music_manager.set_current_music_path(OGGS_PATHS_DICT["xdeviruchi_title_theme.ogg"])
        self.game_music_manager.play_music(-1, 0.0, 0)
        self.game.set_scene("MainMenu")

    def on_curtain_invisible(self) -> None:
        if self.state_machine_update.state == SpriteSheetJsonGenerator.State.OPENING_SCENE_CURTAIN:
            self.state_machine_update.change_state(SpriteSheetJsonGenerator.State.OPENED_SCENE_CURTAIN)
            self.state_machine_draw.change_state(SpriteSheetJsonGenerator.State.OPENED_SCENE_CURTAIN)

    def on_curtain_opaque(self) -> None:
        if self.state_machine_update.state == SpriteSheetJsonGenerator.State.OPENED_SCENE_CURTAIN:
            self.state_machine_update.change_state(SpriteSheetJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY)
            self.state_machine_draw.change_state(SpriteSheetJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY)
            self.curtain.go_to_invisible()
        elif self.state_machine_update.state == SpriteSheetJsonGenerator.State.SPRITE_SHEET_PNG_PATH_QUERY:
            self.state_machine_update.change_state(SpriteSheetJsonGenerator.State.SPRITE_NAME_QUERY)
            self.state_machine_draw.change_state(SpriteSheetJsonGenerator.State.SPRITE_NAME_QUERY)
            self.curtain.go_to_invisible()
        elif self.state_machine_update.state == SpriteSheetJsonGenerator.State.SPRITE_NAME_QUERY:
            self.state_machine_update.change_state(SpriteSheetJsonGenerator.State.SPRITE_LAYER_QUERY)
            self.state_machine_draw.change_state(SpriteSheetJsonGenerator.State.SPRITE_LAYER_QUERY)
            self.curtain.go_to_invisible()
        elif self.state_machine_update.state == SpriteSheetJsonGenerator.State.SPRITE_LAYER_QUERY:
            self.state_machine_update.change_state(SpriteSheetJsonGenerator.State.SPRITE_TYPE_QUERY)
            self.state_machine_draw.change_state(SpriteSheetJsonGenerator.State.SPRITE_TYPE_QUERY)
            self.curtain.go_to_invisible()
        elif self.state_machine_update.state == SpriteSheetJsonGenerator.State.SPRITE_TYPE_QUERY:
            self.state_machine_update.change_state(SpriteSheetJsonGenerator.State.SPRITE_TILE_TYPE_QUERY)
            self.state_machine_draw.change_state(SpriteSheetJsonGenerator.State.SPRITE_TILE_TYPE_QUERY)
            self.curtain.go_to_invisible()
        elif self.state_machine_update.state == SpriteSheetJsonGenerator.State.SPRITE_TILE_TYPE_QUERY:
            self.state_machine_update.change_state(SpriteSheetJsonGenerator.State.SPRITE_TILE_MIX_QUERY)
            self.state_machine_draw.change_state(SpriteSheetJsonGenerator.State.SPRITE_TILE_MIX_QUERY)
            self.curtain.go_to_invisible()
        elif self.state_machine_update.state == SpriteSheetJsonGenerator.State.SPRITE_TILE_MIX_QUERY:
            self.state_machine_update.change_state(SpriteSheetJsonGenerator.State.ADD_SPRITES)
            self.state_machine_draw.change_state(SpriteSheetJsonGenerator.State.ADD_SPRITES)
            self.curtain.go_to_invisible()

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

    def init_room_collision_map_list(
        self,
        room_width_tu: int,
        room_height_tu: int,
    ) -> None:
        self.room_collision_map_width_tu = room_width_tu
        self.room_collision_map_height_tu = room_height_tu
        self.room_collision_map_list = [
            0 for _ in range(self.room_collision_map_width_tu * self.room_collision_map_height_tu)
        ]

    def set_input_text(self, value: str) -> None:
        self.input_text = value
        self.input_rect = FONT.get_rect(self.input_text)
        self.input_rect.center = NATIVE_RECT.center

    def set_prompt_text(self, value: str) -> None:
        self.prompt_text = f"{value} " f"hit {pg.key.name(self.game.local_settings_dict['enter'])} " "to proceed"
        self.prompt_rect = FONT.get_rect(self.prompt_text)
        self.prompt_rect.center = NATIVE_RECT.center
        self.prompt_rect.y -= FONT_HEIGHT + 1
