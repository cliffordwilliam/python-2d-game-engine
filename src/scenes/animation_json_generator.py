from json import dump
from os.path import exists
from os.path import join  # for OS agnostic paths.
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import TYPE_CHECKING

from constants import FONT
from constants import FONT_HEIGHT
from constants import JSONS_DIR_PATH
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
from nodes.timer import Timer
from pygame.math import clamp
from pygame.math import Vector2
from typeguard import typechecked

if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class AnimationJsonGenerator:
    """
    Prefix the file name to be saved.
    With the sprite sheet name.
    Because for performance sake 1 json is for 1 sprite sheet.
    Asks for file name to be saved to JSONS_DIR_PATH.
    Careful for overriding data.

    States:
    - JUST_ENTERED_SCENE.
    - OPENING_SCENE_CURTAIN.
    - OPENED_SCENE_CURTAIN.
    - CLOSING_SCENE_CURTAIN.
    - CLOSED_SCENE_CURTAIN.
    - SPRITE_SHEET_PNG_PATH_QUERY.
    - SPRITE_SIZE_QUERY.
    - ANIMATION_NAME_QUERY.
    - LOOP_QUERY.
    - NEXT_ANIMATION_QUERY.
    - DURATION_QUERY.
    - ADD_SPRITES.
    - SAVE_QUIT_REDO_QUERY.

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
    OPENED_SCENE_CURTAIN: int = 2
    SPRITE_SHEET_PNG_PATH_QUERY: int = 3
    SPRITE_SIZE_QUERY: int = 4
    ANIMATION_NAME_QUERY: int = 5
    LOOP_QUERY: int = 6
    NEXT_ANIMATION_QUERY: int = 7
    DURATION_QUERY: int = 8
    ADD_SPRITES: int = 9
    SAVE_QUIT_REDO_QUERY: int = 10
    CLOSING_SCENE_CURTAIN: int = 11
    CLOSED_SCENE_CURTAIN: int = 12

    # REMOVE IN BUILD
    state_names: List = [
        "JUST_ENTERED_SCENE",
        "OPENING_SCENE_CURTAIN",
        "OPENED_SCENE_CURTAIN",
        "SPRITE_SHEET_PNG_PATH_QUERY",
        "SPRITE_SIZE_QUERY",
        "ANIMATION_NAME_QUERY",
        "LOOP_QUERY",
        "NEXT_ANIMATION_QUERY",
        "DURATION_QUERY",
        "ADD_SPRITES",
        "SAVE_QUIT_REDO_QUERY",
        "CLOSING_SCENE_CURTAIN",
        "CLOSED_SCENE_CURTAIN",
    ]

    def __init__(self, game: "Game"):
        # - Set scene.
        # - Debug draw.
        self.game = game
        self.event_handler = self.game.event_handler

        # Colors.
        self.native_clear_color: str = "#7f7f7f"
        self.grid_line_color: str = "#999999"
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

        # Texts.
        # Prompt.
        self.prompt_text: str = ""
        self.prompt_rect: pg.Rect = FONT.get_rect(self.prompt_text)
        # Input.
        self.input_text: str = ""
        self.input_rect: pg.Rect = FONT.get_rect(self.input_text)
        self.input_rect.center = NATIVE_RECT.center

        # Store user inputs.
        self.file_name: str = ""
        self.animation_sprite_size: int = TILE_SIZE
        self.sprite_size_tu: int = int(self.animation_sprite_size // TILE_SIZE)
        self.animation_name: str = ""
        self.animation_is_loop: int = 0
        self.next_animation_name: str = ""
        self.animation_duration: int = 0
        # Sprite sheet surf.
        self.sprite_sheet_png_path: Any = None
        self.sprite_sheet_surf: Any = None
        self.sprite_sheet_rect: Any = None

        # Camera.
        self.camera_anchor_vector: Vector2 = Vector2(0.0, 0.0)
        self.camera: Camera = Camera(
            self.camera_anchor_vector,
            # REMOVE IN BUILD.
            self.game,
        )
        # Px / ms.
        self.camera_speed: float = 0.09

        # Mouse positions.
        self.world_mouse_x: float = 0.0
        self.world_mouse_y: float = 0.0
        self.world_mouse_tu_x: int = 0
        self.world_mouse_tu_y: int = 0
        self.world_mouse_snapped_x: int = 0
        self.world_mouse_snapped_y: int = 0
        self.screen_mouse_x: float = 0.0
        self.screen_mouse_y: float = 0.0

        # Collision map.
        self.room_collision_map_list: List[int] = []
        self.room_collision_map_width_tu: int = 0
        self.room_collision_map_height_tu: int = 0

        # To be saved json.
        self.animation_json: Dict = {}
        self.animation_sprites_list: List = []

        # Selected surf marker.
        self.selected_surf_marker: pg.Surface = pg.Surface((TILE_SIZE, TILE_SIZE))
        self.selected_surf_marker.fill("red")

        # Grid surf.
        self.grid_vertical_line_surf: pg.Surface = pg.Surface((NATIVE_HEIGHT, 1))
        self.grid_vertical_line_surf.fill(self.grid_line_color)
        self.grid_horizontal_line_surf: pg.Surface = pg.Surface((1, NATIVE_HEIGHT))
        self.grid_horizontal_line_surf.fill(self.grid_line_color)

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
            self.sprite_sheet_png_path_query_state,
            self.sprite_size_query_state,
            self.animation_name_query_state,
            self.loop_query_state,
            self.next_animation_query_state,
            self.duration_query_state,
            self.add_sprites_state,
            self.save_quit_redo_query_state,
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
        - Get user input for file name.
        - Updates curtain alpha.
        """
        # Wait for curtain to be fully invisible.
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.event_handler.this_frame_event:
                if self.event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept.
                    if self.event_handler.this_frame_event.key == pg.K_RETURN:
                        if self.input_text != "":
                            self.file_name = self.input_text
                            # Close curtain.
                            # Exit to SPRITE_SHEET_PNG_PATH_QUERY.
                            self.curtain.go_to_opaque()
                    # Delete.
                    elif self.event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add.
                    else:
                        new_value = self.input_text + self.event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain.
        self.curtain.update(dt)

    def sprite_sheet_png_path_query_state(self, dt: int) -> None:
        """
        - Get user input for png path.
        - Updates curtain alpha.
        """
        # Wait for curtain to be fully invisible.
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.event_handler.this_frame_event:
                if self.event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept.
                    if self.event_handler.this_frame_event.key == pg.K_RETURN:
                        if exists(self.input_text) and self.input_text.endswith(".png"):
                            # Setup the sprite sheet data.
                            self.sprite_sheet_png_path = self.input_text
                            self.sprite_sheet_surf = pg.image.load(self.sprite_sheet_png_path).convert_alpha()
                            self.sprite_sheet_rect = self.sprite_sheet_surf.get_rect()
                            # Setup camera limits.
                            self.camera.set_rect_limit(
                                float(self.sprite_sheet_rect.top),
                                float(self.sprite_sheet_rect.bottom),
                                float(self.sprite_sheet_rect.left),
                                float(self.sprite_sheet_rect.right),
                            )
                            # Init room collision map list.
                            sprite_sheet_width_tu: int = self.sprite_sheet_rect.width // TILE_SIZE
                            sprite_sheet_height_tu: int = self.sprite_sheet_rect.height // TILE_SIZE
                            self.init_room_collision_map_list(
                                sprite_sheet_width_tu,
                                sprite_sheet_height_tu,
                            )
                            # Exit to SPRITE_SIZE_QUERY.
                            # Close curtain to exit to SPRITE_SIZE_QUERY.
                            self.curtain.go_to_opaque()
                        else:
                            self.set_input_text("png path does not exist!")
                    # Delete.
                    elif self.event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add.
                    else:
                        new_value = self.input_text + self.event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain.
        self.curtain.update(dt)

    def sprite_size_query_state(self, dt: int) -> None:
        """
        - Get user input for sprite size.
        - Updates curtain alpha.
        """
        # Wait for curtain to be fully invisible.
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.event_handler.this_frame_event:
                if self.event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept.
                    if self.event_handler.this_frame_event.key == pg.K_RETURN:
                        if self.input_text.isdigit():
                            # Setup the sprite_size.
                            self.animation_sprite_size = max(int(self.input_text) * TILE_SIZE, 0)
                            self.sprite_size_tu = int(self.animation_sprite_size // TILE_SIZE)
                            # Exit to ADD_SPRITES.
                            # Close curtain to exit to ADD_SPRITES.
                            self.curtain.go_to_opaque()
                        else:
                            self.set_input_text("type int only please!")
                    # Delete.
                    elif self.event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add.
                    else:
                        new_value = self.input_text + self.event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain.
        self.curtain.update(dt)

    def animation_name_query_state(self, dt: int) -> None:
        """
        - Get user input for sprite size.
        - Updates curtain alpha.
        """
        # Wait for curtain to be fully invisible.
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.event_handler.this_frame_event:
                if self.event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept.
                    if self.event_handler.this_frame_event.key == pg.K_RETURN:
                        # TODO: Trim white space.
                        if self.input_text != "":
                            self.animation_name = self.input_text
                            # Close curtain.
                            # Exit to SPRITE_SHEET_PNG_PATH_QUERY.
                            self.curtain.go_to_opaque()
                    # Delete.
                    elif self.event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add.
                    else:
                        new_value = self.input_text + self.event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain.
        self.curtain.update(dt)

    def loop_query_state(self, dt: int) -> None:
        """
        - Get user input for sprite size.
        - Updates curtain alpha.
        """
        # Wait for curtain to be fully invisible.
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.event_handler.this_frame_event:
                if self.event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept.
                    if self.event_handler.this_frame_event.key == pg.K_RETURN:
                        if self.input_text in ["y", "n"]:
                            if self.input_text == "y":
                                self.animation_is_loop = 1
                            elif self.input_text == "n":
                                self.animation_is_loop = 0
                            # Close curtain.
                            # Exit to SPRITE_SHEET_PNG_PATH_QUERY.
                            self.curtain.go_to_opaque()
                        else:
                            self.set_input_text("type y or n only please!")
                    # Delete.
                    elif self.event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add.
                    else:
                        new_value = self.input_text + self.event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain.
        self.curtain.update(dt)

    def next_animation_query_state(self, dt: int) -> None:
        """
        - Get user input for sprite size.
        - Updates curtain alpha.
        """
        # Wait for curtain to be fully invisible.
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.event_handler.this_frame_event:
                if self.event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept.
                    if self.event_handler.this_frame_event.key == pg.K_RETURN:
                        # TODO: Trim white space.
                        if self.input_text != "":
                            self.next_animation_name = self.input_text
                            # Close curtain.
                            # Exit to SPRITE_SHEET_PNG_PATH_QUERY.
                            self.curtain.go_to_opaque()
                    # Delete.
                    elif self.event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add.
                    else:
                        new_value = self.input_text + self.event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain.
        self.curtain.update(dt)

    def duration_query_state(self, dt: int) -> None:
        """
        - Get user input for sprite size.
        - Updates curtain alpha.
        """
        # Wait for curtain to be fully invisible.
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.event_handler.this_frame_event:
                if self.event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept.
                    if self.event_handler.this_frame_event.key == pg.K_RETURN:
                        if self.input_text.isdigit():
                            # Setup the sprite_size.
                            self.animation_duration = int(self.input_text)
                            # Exit to ADD_SPRITES.
                            # Close curtain to exit to ADD_SPRITES.
                            self.curtain.go_to_opaque()
                        else:
                            self.set_input_text("type int only please!")
                    # Delete.
                    elif self.event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add.
                    else:
                        new_value = self.input_text + self.event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain.
        self.curtain.update(dt)

    def add_sprites_state(self, dt: int) -> None:
        """
        - Move camera and add frames to be saved.
        - Updates curtain alpha.
        """
        # Wait for curtain to be fully invisible.
        if self.curtain.is_done:
            # Camera movement.
            # Get direction_horizontal.
            direction_horizontal: int = self.event_handler.is_right_pressed - self.event_handler.is_left_pressed
            # Update camera anchor position with direction and speed.
            self.camera_anchor_vector.x += direction_horizontal * self.camera_speed * dt
            # Get direction_vertical.
            direction_vertical: int = self.event_handler.is_down_pressed - self.event_handler.is_up_pressed
            # Update camera anchor position with direction and speed.
            self.camera_anchor_vector.y += direction_vertical * self.camera_speed * dt
            # Lerp camera position to target camera anchor.
            self.camera.update(dt)

            # Sprite selection.
            # Lmb just pressed.
            is_lmb_just_pressed_occupied: bool = False
            if self.event_handler.is_lmb_just_pressed:
                # Check if selection is all empty cells.
                # Iterate size to check all empty.
                for world_mouse_tu_xi in range(self.sprite_size_tu):
                    for world_mouse_tu_yi in range(self.sprite_size_tu):
                        world_mouse_tu_x: int = self.world_mouse_tu_x + world_mouse_tu_xi
                        world_mouse_tu_y: int = self.world_mouse_tu_y + world_mouse_tu_yi
                        # Get each one in room_collision_map_list.
                        found_tile_lmb_pressed: int = self.get_tile_from_room_collision_map_list(
                            world_mouse_tu_x,
                            world_mouse_tu_y,
                        )
                        # At least 1 of them is occupied? Return.
                        if found_tile_lmb_pressed == 1:
                            is_lmb_just_pressed_occupied = True
                # All cells are empty.
                if not is_lmb_just_pressed_occupied:
                    # Fill it.
                    # Iterate size to set 1.
                    for world_mouse_tu_xi2 in range(self.sprite_size_tu):
                        for world_mouse_tu_yi2 in range(self.sprite_size_tu):
                            world_mouse_tu_x2: int = self.world_mouse_tu_x + world_mouse_tu_xi2
                            world_mouse_tu_y2: int = self.world_mouse_tu_y + world_mouse_tu_yi2
                            # Store each one in room_collision_map_list.
                            self.set_tile_from_room_collision_map_list(
                                world_mouse_tu_x2,
                                world_mouse_tu_y2,
                                1,
                            )
                            # Draw marker on sprite sheet.
                            self.sprite_sheet_surf.blit(
                                self.selected_surf_marker,
                                (
                                    world_mouse_tu_x2 * TILE_SIZE,
                                    world_mouse_tu_y2 * TILE_SIZE,
                                ),
                            )
                    # Add to list.
                    self.animation_sprites_list.append(
                        {
                            "x": self.world_mouse_snapped_x,
                            "y": self.world_mouse_snapped_y,
                        }
                    )

            # Enter just pressed.
            if self.event_handler.is_enter_just_pressed:
                # Exit to ask save quit, save again, redo.
                self.curtain.go_to_opaque()

        # Update curtain.
        self.curtain.update(dt)

    def save_quit_redo_query_state(self, dt: int) -> None:
        """
        - Get user input for save quit, save again, redo.
        - Updates curtain alpha.
        """
        # Wait for curtain to be fully invisible.
        if self.curtain.is_done:
            # Caught 1 key event this frame?
            if self.event_handler.this_frame_event:
                if self.event_handler.this_frame_event.type == pg.KEYDOWN:
                    # Accept.
                    if self.event_handler.this_frame_event.key == pg.K_RETURN:
                        if self.input_text in [
                            str(self.save_and_quit_choice_after_add_sprites_state),
                            str(self.save_and_redo_choice_after_add_sprites_state),
                            str(self.redo_choice_after_add_sprites_state),
                            str(self.quit_choice_after_add_sprites_state),
                        ]:
                            # 1 = Save and quit.
                            if self.input_text == str(self.save_and_quit_choice_after_add_sprites_state):
                                self.selected_choice_after_add_sprites_state = (
                                    self.save_and_quit_choice_after_add_sprites_state
                                )
                                # Save this animation to local.
                                self.animation_json[self.animation_name] = {
                                    "animation_is_loop": self.animation_is_loop,
                                    "next_animation_name": self.next_animation_name,
                                    "animation_duration": self.animation_duration,
                                    "animation_sprite_size": self.animation_sprite_size,
                                    "animation_sprites_list": self.animation_sprites_list,
                                }
                                # Write to json.
                                with open(
                                    join(JSONS_DIR_PATH, f"{self.file_name}.json"),
                                    "w",
                                ) as animation_json:
                                    dump(self.animation_json, animation_json)
                                # Close curtain.
                                # Exit to main menu.
                                self.game.music_manager.fade_out_music(int(self.curtain_duration))
                                self.curtain.go_to_opaque()
                            # 2 = Save and redo.
                            elif self.input_text == str(self.save_and_redo_choice_after_add_sprites_state):
                                self.selected_choice_after_add_sprites_state = (
                                    self.save_and_redo_choice_after_add_sprites_state
                                )
                                # Save this animation to local.
                                self.animation_json[self.animation_name] = {
                                    "animation_is_loop": self.animation_is_loop,
                                    "next_animation_name": self.next_animation_name,
                                    "animation_duration": self.animation_duration,
                                    "animation_sprite_size": self.animation_sprite_size,
                                    "animation_sprites_list": self.animation_sprites_list,
                                }
                                # Get fresh selected sprite sheet again.
                                self.sprite_sheet_surf = pg.image.load(self.sprite_sheet_png_path).convert_alpha()
                                # Empty the selected sprites list.
                                self.animation_sprites_list = []
                                # Empty collision map.
                                self.init_room_collision_map_list(
                                    self.room_collision_map_width_tu,
                                    self.room_collision_map_height_tu,
                                )
                                # Close curtain.
                                # Exit to SPRITE_SIZE_QUERY.
                                self.curtain.go_to_opaque()
                            # 3 = Redo.
                            elif self.input_text == str(self.redo_choice_after_add_sprites_state):
                                self.selected_choice_after_add_sprites_state = self.redo_choice_after_add_sprites_state
                                # Get fresh selected sprite sheet again.
                                self.sprite_sheet_surf = pg.image.load(self.sprite_sheet_png_path).convert_alpha()
                                # Empty the selected sprites list.
                                self.animation_sprites_list = []
                                # Empty collision map.
                                self.init_room_collision_map_list(
                                    self.room_collision_map_width_tu,
                                    self.room_collision_map_height_tu,
                                )
                                # Close curtain.
                                # Exit to ADD_SPRITES.
                                self.curtain.go_to_opaque()
                            # 4 = Quit.
                            elif self.input_text == str(self.quit_choice_after_add_sprites_state):
                                self.selected_choice_after_add_sprites_state = self.quit_choice_after_add_sprites_state
                                # Close curtain.
                                # Exit to main menu.
                                self.game.music_manager.fade_out_music(int(self.curtain_duration))
                                self.curtain.go_to_opaque()
                        else:
                            self.set_input_text("type 1, 2, 3 or 4 only please!")
                    # Delete.
                    elif self.event_handler.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.input_text[:-1]
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("029_decline_09.ogg", 0, 0, 0)
                    # Add.
                    else:
                        new_value = self.input_text + self.event_handler.this_frame_event.unicode
                        self.set_input_text(new_value)
                        # Play text.
                        self.game.sound_manager.play_sound("text_1.ogg", 0, 0, 0)

        # Update curtain.
        self.curtain.update(dt)

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
        if self.state == self.OPENING_SCENE_CURTAIN:
            self.set_state(self.OPENED_SCENE_CURTAIN)
            return

    def on_curtain_opaque(self) -> None:
        if self.state == self.OPENED_SCENE_CURTAIN:
            self.set_state(self.SPRITE_SHEET_PNG_PATH_QUERY)
            self.curtain.go_to_invisible()
            return
        elif self.state == self.SPRITE_SHEET_PNG_PATH_QUERY:
            self.set_state(self.SPRITE_SIZE_QUERY)
            self.curtain.go_to_invisible()
            return
        elif self.state == self.SPRITE_SIZE_QUERY:
            self.set_state(self.ANIMATION_NAME_QUERY)
            self.curtain.go_to_invisible()
            return
        elif self.state == self.ANIMATION_NAME_QUERY:
            self.set_state(self.LOOP_QUERY)
            self.curtain.go_to_invisible()
            return
        elif self.state == self.LOOP_QUERY:
            self.set_state(self.NEXT_ANIMATION_QUERY)
            self.curtain.go_to_invisible()
            return
        elif self.state == self.NEXT_ANIMATION_QUERY:
            self.set_state(self.DURATION_QUERY)
            self.curtain.go_to_invisible()
            return
        elif self.state == self.DURATION_QUERY:
            self.set_state(self.ADD_SPRITES)
            self.curtain.go_to_invisible()
            return
        elif self.state == self.ADD_SPRITES:
            self.set_state(self.SAVE_QUIT_REDO_QUERY)
            self.curtain.go_to_invisible()
            return
        elif self.state == self.SAVE_QUIT_REDO_QUERY:
            if self.selected_choice_after_add_sprites_state == (self.save_and_redo_choice_after_add_sprites_state):
                self.set_state(self.ANIMATION_NAME_QUERY)
                self.curtain.go_to_invisible()
                return
            elif self.selected_choice_after_add_sprites_state == (self.redo_choice_after_add_sprites_state):
                self.set_state(self.ADD_SPRITES)
                self.curtain.go_to_invisible()
                return
            elif self.selected_choice_after_add_sprites_state == (self.save_and_quit_choice_after_add_sprites_state):
                self.set_state(self.CLOSED_SCENE_CURTAIN)
                return
            elif self.selected_choice_after_add_sprites_state == (self.quit_choice_after_add_sprites_state):
                self.set_state(self.CLOSED_SCENE_CURTAIN)
                return
        elif self.state == self.CLOSING_SCENE_CURTAIN:
            self.set_state(self.CLOSED_SCENE_CURTAIN)

    # Helpers.
    def draw_grid(self) -> None:
        for i in range(NATIVE_WIDTH_TU):
            offset: int = TILE_SIZE * i
            vertical_line_x_position: float = (offset - self.camera.rect.x) % NATIVE_WIDTH
            horizontal_line_y_position: float = (offset - self.camera.rect.y) % NATIVE_HEIGHT
            NATIVE_SURF.blit(
                self.grid_vertical_line_surf,
                (vertical_line_x_position, 0),
            )
            NATIVE_SURF.blit(
                self.grid_horizontal_line_surf,
                (0, horizontal_line_y_position),
            )
            pg.draw.line(
                NATIVE_SURF,
                self.grid_line_color,
                (vertical_line_x_position, 0),
                (vertical_line_x_position, NATIVE_HEIGHT),
            )
            pg.draw.line(
                NATIVE_SURF,
                self.grid_line_color,
                (0, horizontal_line_y_position),
                (NATIVE_WIDTH, horizontal_line_y_position),
            )

    def get_tile_from_room_collision_map_list(
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

    def set_tile_from_room_collision_map_list(
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

    def draw(self) -> None:
        """
        - clear NATIVE_SURF.
        - file_text.
        - tips_text.
        - curtain.
        """

        # Clear.
        NATIVE_SURF.fill(self.native_clear_color)

        if self.state in [
            self.OPENING_SCENE_CURTAIN,
            self.OPENED_SCENE_CURTAIN,
            self.SPRITE_SHEET_PNG_PATH_QUERY,
            self.SPRITE_SIZE_QUERY,
            self.ANIMATION_NAME_QUERY,
            self.LOOP_QUERY,
            self.NEXT_ANIMATION_QUERY,
            self.DURATION_QUERY,
            self.SAVE_QUIT_REDO_QUERY,
        ]:
            # Draw grid with camera offset.
            self.draw_grid()
            # Draw promt and input.
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

        elif self.state == self.ADD_SPRITES:
            self.draw_grid()

            # Draw selected sprite sheet with camera offset.
            NATIVE_SURF.blit(
                self.sprite_sheet_surf,
                (
                    -self.camera.rect.x,
                    -self.camera.rect.y,
                ),
            )

            # Draw cursor.
            # Get mouse position.
            mouse_position_tuple: Tuple[int, int] = pg.mouse.get_pos()
            mouse_position_x_tuple: int = mouse_position_tuple[0]
            # Set top left to be -y_offset instead of 0.
            mouse_position_y_tuple: int = mouse_position_tuple[1] - self.game.native_y_offset
            # Scale mouse position.
            mouse_position_x_tuple_scaled: int | float = (
                mouse_position_x_tuple // self.game.local_settings_dict["resolution_scale"]
            )
            mouse_position_y_tuple_scaled: int | float = (
                mouse_position_y_tuple // self.game.local_settings_dict["resolution_scale"]
            )
            # Keep mouse inside scaled NATIVE_RECT.
            mouse_position_x_tuple_scaled = clamp(
                mouse_position_x_tuple_scaled,
                NATIVE_RECT.left,
                # Because this will refer to top left of a cell.
                # If it is flushed to the right it is out of bound.
                NATIVE_RECT.right - 1,
            )
            mouse_position_y_tuple_scaled = clamp(
                mouse_position_y_tuple_scaled,
                NATIVE_RECT.top,
                # Because this will refer to top left of a cell.
                # If it is flushed to the bottom it is out of bound.
                NATIVE_RECT.bottom - 1,
            )
            # Convert positions.
            self.world_mouse_x = mouse_position_x_tuple_scaled + self.camera.rect.x
            self.world_mouse_y = mouse_position_y_tuple_scaled + self.camera.rect.y
            self.world_mouse_x = min(
                self.world_mouse_x,
                self.sprite_sheet_rect.right - self.animation_sprite_size,
            )
            self.world_mouse_y = min(
                self.world_mouse_y,
                self.sprite_sheet_rect.bottom - self.animation_sprite_size,
            )
            self.world_mouse_tu_x = int(self.world_mouse_x // TILE_SIZE)
            self.world_mouse_tu_y = int(self.world_mouse_y // TILE_SIZE)
            self.world_mouse_snapped_x = int(self.world_mouse_tu_x * TILE_SIZE)
            self.world_mouse_snapped_y = int(self.world_mouse_tu_y * TILE_SIZE)
            self.screen_mouse_x = self.world_mouse_snapped_x - self.camera.rect.x
            self.screen_mouse_y = self.world_mouse_snapped_y - self.camera.rect.y
            pg.draw.rect(
                NATIVE_SURF,
                "green",
                [
                    self.screen_mouse_x,
                    self.screen_mouse_y,
                    self.animation_sprite_size,
                    self.animation_sprite_size,
                ],
                1,
            )

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
        if self.event_handler.is_pause_just_pressed:
            # Update and draw options menu, stop my update
            self.game.set_is_options_menu_active(True)

        self.state_logics[self.state](dt)

    def set_state(self, value: int) -> None:
        old_state: int = self.state
        self.state = value

        # From JUST_ENTERED_SCENE.
        if old_state == self.JUST_ENTERED_SCENE:
            # To OPENING_SCENE_CURTAIN.
            if self.state == self.OPENING_SCENE_CURTAIN:
                self.curtain.go_to_invisible()

        # From OPENING_SCENE_CURTAIN.
        elif old_state == self.OPENING_SCENE_CURTAIN:
            # To OPENED_SCENE_CURTAIN.
            if self.state == self.OPENED_SCENE_CURTAIN:
                # Reset the input text.
                self.set_input_text("")
                # Set my prompt text:
                self.set_prompt_text("type the file name to be saved,")

        # From OPENED_SCENE_CURTAIN.
        elif old_state == self.OPENED_SCENE_CURTAIN:
            # To SPRITE_SHEET_PNG_PATH_QUERY.
            if self.state == self.SPRITE_SHEET_PNG_PATH_QUERY:
                # Reset the input text.
                self.set_input_text("")
                # Set my prompt text:
                self.set_prompt_text("type the png path to be loaded,")

        # From SPRITE_SHEET_PNG_PATH_QUERY.
        elif old_state == self.SPRITE_SHEET_PNG_PATH_QUERY:
            # To SPRITE_SIZE_QUERY.
            if self.state == self.SPRITE_SIZE_QUERY:
                # Reset the input text.
                self.set_input_text("")
                # Set my prompt text:
                self.set_prompt_text("type the sprite size in tile units to be used,")

        # From SPRITE_SIZE_QUERY.
        elif old_state == self.SPRITE_SIZE_QUERY:
            # To ANIMATION_NAME_QUERY.
            if self.state == self.ANIMATION_NAME_QUERY:
                # Reset the input text.
                self.set_input_text("")
                # Set my prompt text:
                self.set_prompt_text("type the animation name,")

        # From ANIMATION_NAME_QUERY.
        elif old_state == self.ANIMATION_NAME_QUERY:
            # To LOOP_QUERY.
            if self.state == self.LOOP_QUERY:
                # Reset the input text.
                self.set_input_text("")
                # Set my prompt text:
                self.set_prompt_text("does the animation loops (y/n)?")

        # From LOOP_QUERY.
        elif old_state == self.LOOP_QUERY:
            # To NEXT_ANIMATION_QUERY.
            if self.state == self.NEXT_ANIMATION_QUERY:
                # Reset the input text.
                self.set_input_text("")
                # Set my prompt text:
                self.set_prompt_text("type the next animation name (optional),")

        # From NEXT_ANIMATION_QUERY.
        elif old_state == self.NEXT_ANIMATION_QUERY:
            # To DURATION_QUERY.
            if self.state == self.DURATION_QUERY:
                # Reset the input text.
                self.set_input_text("")
                # Set my prompt text:
                self.set_prompt_text("type the animation duration (ms),")

        # From DURATION_QUERY.
        elif old_state == self.DURATION_QUERY:
            # To ADD_SPRITES.
            if self.state == self.ADD_SPRITES:
                pass

        # From ADD_SPRITES.
        elif old_state == self.ADD_SPRITES:
            # To SAVE_QUIT_REDO_QUERY.
            if self.state == self.SAVE_QUIT_REDO_QUERY:
                # Reset the input text.
                self.set_input_text("")
                # Set my prompt text:
                self.set_prompt_text("save and quit, save and redo, redo, quit (1/2/3/4)?")

        # From SAVE_QUIT_REDO_QUERY.
        elif old_state == self.SAVE_QUIT_REDO_QUERY:
            # To ANIMATION_NAME_QUERY.
            if self.state == self.ANIMATION_NAME_QUERY:
                # Reset the input text.
                self.set_input_text("")
                # Set my prompt text:
                self.set_prompt_text("type the animation name,")
            # To ADD_SPRITES.
            elif self.state == self.ADD_SPRITES:
                pass

        # From CLOSING_SCENE_CURTAIN.
        elif old_state == self.CLOSING_SCENE_CURTAIN:
            # To CLOSED_SCENE_CURTAIN.
            if self.state == self.CLOSED_SCENE_CURTAIN:
                NATIVE_SURF.fill("black")
