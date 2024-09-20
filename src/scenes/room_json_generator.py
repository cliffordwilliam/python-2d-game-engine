from enum import auto
from enum import Enum
from os import listdir
from os.path import exists
from os.path import join
from typing import Any
from typing import Callable
from typing import TYPE_CHECKING

from actors.parallax_background import ParallaxBackground
from actors.player import Player
from actors.static_actor import StaticActor
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
from schemas import AdjacentTileMetadata
from schemas import AnimationMetadata
from schemas import instance_adjacent_tile_metadata
from schemas import instance_none_or_blob_sprite_metadata
from schemas import instance_sprite_metadata
from schemas import instance_sprite_sheet_metadata
from schemas import NoneOrBlobSpriteMetadata
from schemas import SpriteMetadata
from typeguard import typechecked
from utils import get_one_target_dict_value
from utils import set_one_target_dict_value

if TYPE_CHECKING:
    from nodes.game import Game
    from nodes.event_handler import EventHandler
    from nodes.sound_manager import SoundManager
    from nodes.music_manager import MusicManager

    # REMOVE IN BUILD
    from nodes.debug_draw import DebugDraw


@typechecked
class RoomJsonGenerator:
    # TODO: Do better algo for the flood fill and rect combined fill, do the auto tile update at the very end after all POST
    # Add plyaer to collide to room limits first, spawn it like a tree, enter toggle edit to test mode
    # TODO: Add Enemies, when go back to edit, reset to their initial position
    # TODO: Save and load room, then that is it for now
    # TODO: Add twin goddess and door here too, twin goddess are just like goblins, instead attack allow save
    # Make door have 2 states later, open and close, when it closes it uses the gate sprite
    # so add the sprite sheet like thin fire mapped to stage, map gate to all stages
    # TODO: Add door to minimap too
    # TODO: Later need to be able to place down things that is remembered (appear once only) like items, boss, cutscenes
    # So since cutscenes are binded to each room, name them with numbers, when player finished a cutscene += 1 to their
    # animation seen counter, each animation based on their name has a condition if they should appear or not
    # based on the player cutscene counter that was saved
    # TODO: Implement Quadtree, goblin, twin goddess first
    # TODO: Write the controls in the grid background
    # TODO: Have a clear canvas function where it clears off everything
    # TODO: So I have 4 possible room sizes, for each size, that determine extra door buttons, if 1 x 1 room, thats 4 door buttons
    # TODO: If 2 x 1 then got 6 door. Each door is on room section sides. On saved will be just key name to room path json value
    # TODO: So when you hover on a button, you can type, what you type appears on the button surf, on enter, it validates if path exists
    # TODO: Then it just closes the editor with the last selected sprite, because when you select, door limit is drawn at edge automatically
    # TODO: So if player hits any room edge, use top left, see where it falls, then grab path to load next room, and player offset
    # TODO: Create the player state machine here
    # TODO: Create popup to let user know writing data setting first time

    SLOW_FADE_DURATION: float = 1000.0
    FAST_FADE_DURATION: float = 250.0

    class State(Enum):
        JUST_ENTERED_SCENE: int = auto()
        OPENING_SCENE_CURTAIN: int = auto()
        OPENED_SCENE_CURTAIN: int = auto()
        ADD_OTHER_ROOM: int = auto()
        FILE_NAME_QUERY: int = auto()
        SPRITE_SHEET_JSON_PATH_QUERY: int = auto()
        EDIT_ROOM: int = auto()
        SPRITE_PALETTE: int = auto()
        CLOSING_SCENE_CURTAIN: int = auto()
        CLOSED_SCENE_CURTAIN: int = auto()

    def __init__(self, game: "Game"):
        # Initialize game dependencies
        self.game: "Game" = game
        self.game_event_handler: "EventHandler" = game.event_handler
        self.game_sound_manager: "SoundManager" = game.sound_manager
        self.game_music_manager: "MusicManager" = game.music_manager
        # REMOVE IN BUILD
        self.game_debug_draw: "DebugDraw" = game.debug_draw

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
        self._setup_second_rect_region_feature_world()
        self._setup_cursor()
        self._setup_pallete()
        self._setup_reformat_sprite_sheet_json_metadata()
        self._setup_second_rect_region_feature_room()
        self._setup_player()

    ##########
    # SETUPS #
    ##########
    def _setup_player(self) -> None:
        """
        | Instance player.
        | Editor mode / play test mode flag.
        """

        # Instance player
        self.player: Player = Player(
            camera=self.camera,
            game_event_handler=self.game_event_handler,
            solid_collision_map_list=self.solid_collision_map_list,
            room_width_tu=self.room_width_tu,
            room_height_tu=self.room_height_tu,
            # REMOVE IN BUILD
            game_debug_draw=self.game_debug_draw,
        )

        # Editor mode / play test mode flag
        self.is_play_test_mode: bool = False

    def _setup_reformat_sprite_sheet_json_metadata(self) -> None:
        """
        | Sprite name : SpriteMetadata.
        | Used for selected button state.
        """

        # Sprite name : SpriteMetadata. Used for selected button state
        self.sprite_name_to_sprite_metadata: dict[str, SpriteMetadata] = {}

    def _setup_pallete(self) -> None:
        """
        | To tell opaque curtain where to go next (to pallete or to edit mode).
        | Button container.
        | Currently selected sprite name.
        """

        # To tell opaque curtain where to go next (to pallete or to edit mode)
        self.is_from_edit_pressed_jump: bool = False
        self.is_from_pallete_pressed_jump: bool = False

        # Button container
        self.button_container: (ButtonContainer | None) = None

        # Currently selected sprite name
        self.selected_sprite_name: str = ""
        # Dummy so that I do not have to check if None each time
        self.sprite_metadata_instance: SpriteMetadata = instance_sprite_metadata(
            {
                "sprite_name": "",
                "sprite_layer": 1,
                "sprite_tile_type": "",
                "sprite_type": "",
                "sprite_is_tile_mix": 1,
                "width": 1,
                "height": 1,
                "x": 1,
                "y": 1,
            }
        )

    def _setup_cursor(self) -> None:
        """
        | Setup room cursor.
        """

        # Setup room cursor
        self.cursor_width: int = TILE_SIZE
        self.cursor_height: int = TILE_SIZE
        self.cursor_width_tu: int = 1
        self.cursor_height_tu: int = 1

    def _setup_second_rect_region_feature_room(self) -> None:
        """
        | Setup room combined cursor.
        | Second rect combine state flag, no state here use flag.
        """

        # Setup room combined cursor
        self.first_room_selected_tile_rect: pg.FRect = pg.FRect(0.0, 0.0, TILE_SIZE, TILE_SIZE)
        self.second_room_selected_tile_rect: pg.FRect = pg.FRect(0.0, 0.0, TILE_SIZE, TILE_SIZE)
        self.combined_room_selected_tile_rect: pg.FRect = pg.FRect(0.0, 0.0, TILE_SIZE, TILE_SIZE)
        self.screen_combined_room_selected_tile_rect_x: float = 0.0
        self.screen_combined_room_selected_tile_rect_y: float = 0.0
        self.combined_room_selected_tile_rect_width_ru: int = 0
        self.combined_room_selected_tile_rect_height_ru: int = 0
        self.combined_room_selected_tile_rect_x_ru: int = 0
        self.combined_room_selected_tile_rect_y_ru: int = 0

        # Second rect combine state flag, no state here use flag
        self.is_lmb_was_just_pressed: bool = False

    def _setup_second_rect_region_feature_world(self) -> None:
        """
        | Setup world combined cursor.
        """

        # Setup world combined cursor
        self.first_world_selected_tile_rect: pg.FRect = pg.FRect(0.0, 0.0, WORLD_CELL_SIZE, WORLD_CELL_SIZE)
        self.second_world_selected_tile_rect: pg.FRect = pg.FRect(0.0, 0.0, WORLD_CELL_SIZE, WORLD_CELL_SIZE)
        self.combined_world_selected_tile_rect: pg.FRect = pg.FRect(0.0, 0.0, WORLD_CELL_SIZE, WORLD_CELL_SIZE)
        self.screen_combined_world_selected_tile_rect_x: float = 0.0
        self.screen_combined_world_selected_tile_rect_y: float = 0.0
        self.combined_world_selected_tile_rect_width_ru: int = 0
        self.combined_world_selected_tile_rect_height_ru: int = 0
        self.combined_world_selected_tile_rect_x_ru: int = 0
        self.combined_world_selected_tile_rect_y_ru: int = 0

    def _setup_curtain(self) -> None:
        """
        | Setup curtain with event listener.
        """

        # Setup curtain with event listener
        self.curtain: Curtain = Curtain(
            duration=self.SLOW_FADE_DURATION,
            start_state=Curtain.OPAQUE,
            max_alpha=255,
            surf_size_tuple=(NATIVE_WIDTH, NATIVE_HEIGHT),
            is_invisible=False,
            color="black",
        )
        self.curtain.add_event_listener(
            callback=self._on_curtain_invisible,
            event=Curtain.INVISIBLE_END,
        )
        self.curtain.add_event_listener(
            callback=self._on_curtain_opaque,
            event=Curtain.OPAQUE_END,
        )

    def _setup_timers(self) -> None:
        """
        | Entry delay timer with event listener.
        | Exit delay timer with event listener.
        """

        # Entry delay timer with event listener
        self.entry_delay_timer: Timer = Timer(duration=self.SLOW_FADE_DURATION)
        self.entry_delay_timer.add_event_listener(
            callback=self._on_entry_delay_timer_end,
            event=Timer.END,
        )

        # Exit delay timer with event listener
        self.exit_delay_timer: Timer = Timer(duration=self.SLOW_FADE_DURATION)
        self.exit_delay_timer.add_event_listener(
            callback=self._on_exit_delay_timer_end,
            event=Timer.END,
        )

    def _setup_texts(self) -> None:
        """
        | Prompt question.
        | Input answer.
        """

        # Prompt question
        self.prompt_text: str = ""
        self.prompt_rect: pg.Rect = FONT.get_rect(text=self.prompt_text)

        # Input answer
        self.input_text: str = ""
        self.input_rect: pg.Rect = FONT.get_rect(text=self.input_text)
        self.input_rect.center = NATIVE_RECT.center

    def _setup_user_input_store(self) -> None:
        """
        | Room metadata size and position.
        | Sprite sheet name and surf.
        | Sprite sheet binded things.
        | Layers.
        | Pre renders.
        | Flag indicator to update pre render surf when collision map is PATCHED.
        | File name is room name to be saved JSON.
        """

        # Room metadata size and position
        self.room_height: int = ROOM_HEIGHT
        self.room_height_tu: int = self.room_height // TILE_SIZE
        self.room_width: int = ROOM_WIDTH
        self.room_width_tu: int = self.room_width // TILE_SIZE
        self.room_topleft_x: int = 0
        self.room_topleft_y: int = 0

        # Sprite sheet name and surf
        self.sprite_sheet_png_name: str = ""
        self.sprite_sheet_surf: (None | pg.Surface) = None

        # Sprite sheet binded things
        self.sprite_sheet_static_actor_surfs_dict: dict[
            # {Static actor name : static actor surf}
            str,
            pg.Surface,
        ] = {}
        self.sprite_sheet_static_actor_jsons_dict: dict[
            # {Static actor name : {animation name : animation metadata}}
            str,
            dict[str, AnimationMetadata],
        ] = {}
        self.sprite_sheet_static_actor_instance_dict: dict[
            # {Static actor name : static actor instance}
            str,
            StaticActor,
        ] = {}
        self.sprite_sheet_parallax_background_mems_dict: dict[
            # {Parallax name : parallax instance}
            str,
            ParallaxBackground,
        ] = {}

        # Parallax layer
        self.parallax_background_instances_list: list[None | ParallaxBackground] = []
        # Background layer
        self.background_total_layers: int = 0
        self.background_collision_map_list: list[list[int | NoneOrBlobSpriteMetadata]] = []
        # Static actor layer
        self.static_actor_total_layers: int = 0
        self.static_actor_collision_map_list: list[list[int]] = []
        # TODO: item actors layer (things that player interact with like twin goddess, item drop, door, teleported etc)
        # TODO: dynamic actors layer (anything that moves under the player like goblins, bullets)
        # TODO: player layer
        # TODO: explosions effects are like static actors but they do not need collision or stored in map, just add them in gameplay list
        # Solid
        self.solid_collision_map_list: list[int | NoneOrBlobSpriteMetadata] = [
            0 for _ in range(self.room_width_tu * self.room_height_tu)
        ]
        # Foreground
        self.foreground_total_layers: int = 0
        self.foreground_collision_map_list: list[list[int | NoneOrBlobSpriteMetadata]] = []

        # Pre render background surf
        self.pre_render_background_surf: pg.Surface = pg.Surface((self.room_width, self.room_height))
        self.pre_render_background_surf.set_colorkey("red")
        self.pre_render_background_surf.fill("red")
        # Pre render foreground surf
        self.pre_render_foreground_surf: pg.Surface = pg.Surface((self.room_width, self.room_height))
        self.pre_render_foreground_surf.set_colorkey("red")
        self.pre_render_foreground_surf.fill("red")

        # Flag indicator to update pre render surf when collision map is PATCHED
        self.is_pre_render_collision_map_list_mutated: bool = False

        # File name is room name to be saved JSON
        self.file_name: str = ""

    def _setup_camera(self) -> None:
        """
        | Editor camera anchor vector.
        | Camera instance.
        | Editor camera anchor vector speed.
        """

        # Editor camera anchor vector
        self.camera_anchor_vector: Vector2 = Vector2(0.0, 0.0)

        # Offset drawn things based on where this is
        self.camera: Camera = Camera(
            self.camera_anchor_vector,
            # REMOVE IN BUILD
            self.game_debug_draw,
        )

        # The "player" speed in editing mode
        self.camera_speed: float = 0.09  # Px / ms

    def _setup_collision_map(self) -> None:
        """
        | The whole world size is fixed, this is a constnat.
        """

        # World
        # TODO: When saving feature is done, type safe this
        self.world_collision_map_list: list[Any] = [0 for _ in range(WORLD_WIDTH_RU * WORLD_HEIGHT_RU)]

    def _setup_surfs(self) -> None:
        """
        | Grid world line surfs.
        | Grid room line surfs.
        | World surf.
        """

        # Grid world line surfs
        self.grid_world_horizontal_line_surf: pg.Surface = pg.Surface((WORLD_WIDTH, 1))
        self.grid_world_horizontal_line_surf.fill("black")
        self.grid_world_horizontal_line_surf.set_alpha(21)
        self.grid_world_vertical_line_surf: pg.Surface = pg.Surface((1, WORLD_HEIGHT))
        self.grid_world_vertical_line_surf.fill("black")
        self.grid_world_vertical_line_surf.set_alpha(21)

        # Grid room line surfs
        self.grid_room_horizontal_line_surf: pg.Surface = pg.Surface((NATIVE_WIDTH, 1))
        self.grid_room_horizontal_line_surf.fill("black")
        self.grid_room_horizontal_line_surf.set_alpha(21)
        self.grid_room_vertical_line_surf: pg.Surface = pg.Surface((1, NATIVE_HEIGHT))
        self.grid_room_vertical_line_surf.fill("black")
        self.grid_room_vertical_line_surf.set_alpha(21)

        # World surf
        self.world_surf: pg.Surface = pg.Surface((WORLD_WIDTH, WORLD_HEIGHT))
        self.world_surf.fill(self.clear_color)

    def _setup_mouse_positions(self) -> None:
        """
        | Mouse positions, world and screen version.
        """

        self.world_mouse_x: float = 0.0
        self.world_mouse_y: float = 0.0
        self.world_mouse_tu_x: int = 0
        self.world_mouse_tu_y: int = 0
        self.world_mouse_snapped_x: int = 0
        self.world_mouse_snapped_y: int = 0
        self.screen_mouse_x: float = 0.0
        self.screen_mouse_y: float = 0.0

    def _setup_music(self) -> None:
        """
        | Load editor screen music. Played in my set state.
        """

        self.game_music_manager.set_current_music_path(OGGS_PATHS_DICT["xdeviruchi_take_some_rest_and_eat_some_food.ogg"])
        self.game_music_manager.play_music(-1, 0.0, 0)

    def _setup_state_machine_update(self) -> None:
        """
        | Create state machine for update.
        """

        self.state_machine_update = StateMachine(
            initial_state=RoomJsonGenerator.State.JUST_ENTERED_SCENE,
            state_handlers={
                RoomJsonGenerator.State.JUST_ENTERED_SCENE: self._JUST_ENTERED_SCENE,
                RoomJsonGenerator.State.OPENING_SCENE_CURTAIN: self._OPENING_SCENE_CURTAIN,
                RoomJsonGenerator.State.OPENED_SCENE_CURTAIN: self._OPENED_SCENE_CURTAIN,
                RoomJsonGenerator.State.ADD_OTHER_ROOM: self._ADD_OTHER_SPRITES,
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
                    RoomJsonGenerator.State.ADD_OTHER_ROOM,
                ): self._OPENED_SCENE_CURTAIN_to_ADD_OTHER_SPRITES,
                (
                    RoomJsonGenerator.State.ADD_OTHER_ROOM,
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
        | Create state machine for draw.
        """

        self.state_machine_draw = StateMachine(
            initial_state=RoomJsonGenerator.State.JUST_ENTERED_SCENE,
            state_handlers={
                RoomJsonGenerator.State.JUST_ENTERED_SCENE: self._NOTHING,
                RoomJsonGenerator.State.OPENING_SCENE_CURTAIN: self._QUERIES,
                RoomJsonGenerator.State.OPENED_SCENE_CURTAIN: self._ADD_ROOM_DRAW,
                RoomJsonGenerator.State.ADD_OTHER_ROOM: self._ADD_OTHER_ROOM_DRAW,
                RoomJsonGenerator.State.FILE_NAME_QUERY: self._QUERIES,
                RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY: self._QUERIES,
                RoomJsonGenerator.State.EDIT_ROOM: self._EDIT_ROOM_DRAW,
                RoomJsonGenerator.State.SPRITE_PALETTE: self._SPRITE_PALLETE_DRAW,
                RoomJsonGenerator.State.CLOSING_SCENE_CURTAIN: self._QUERIES,
                RoomJsonGenerator.State.CLOSED_SCENE_CURTAIN: self._NOTHING,
            },
            transition_actions={},
        )

    #####################
    # STATE DRAW LOGICS #
    #####################
    def _NOTHING(self, _dt: int) -> None:
        """
        | When there is nothing to draw.
        """

        pass

    def _QUERIES(self, _dt: int) -> None:
        """
        | Clear.
        | Draw prompt question.
        | Draw input answer.
        | Draw curtain.
        """

        # Clear
        NATIVE_SURF.fill(self.clear_color)

        # Draw prompt question
        FONT.render_to(
            NATIVE_SURF,
            self.prompt_rect,
            self.prompt_text,
            self.font_color,
        )

        # Draw input answer
        FONT.render_to(
            NATIVE_SURF,
            self.input_rect,
            self.input_text,
            self.font_color,
        )

        # Draw curtain
        self.curtain.draw(NATIVE_SURF, 0)

    def _ADD_ROOM_DRAW(self, _dt: int) -> None:
        """
        | Clear.
        | Draw world surf.
        | Draw world grid.
        | Draw cursor.
        | Draw curtain.
        """

        # Clear
        NATIVE_SURF.fill(self.clear_color)

        # Draw world surf
        NATIVE_SURF.blit(self.world_surf, (0, 0))

        # Draw world grid
        self._draw_world_grid()

        # Draw cursor
        self._draw_cursor(
            mouse_position_x_tuple_scaled_min=0,
            mouse_position_x_tuple_scaled_max=WORLD_WIDTH,
            mouse_position_y_tuple_scaled_min=0,
            mouse_position_y_tuple_scaled_max=WORLD_HEIGHT,
            room_width=WORLD_WIDTH,
            room_height=WORLD_HEIGHT,
            cursor_width=WORLD_CELL_SIZE,
            cursor_height=WORLD_CELL_SIZE,
            cell_size=WORLD_CELL_SIZE,
            is_world=True,
        )

        # Curtain
        self.curtain.draw(NATIVE_SURF, 0)

    def _ADD_OTHER_ROOM_DRAW(self, _dt: int) -> None:
        """
        | Clear.
        | Draw world surf.
        | Draw world grid.
        | Draw cursor for second room rect.
        | Draw curtain.
        """

        # Clear
        NATIVE_SURF.fill(self.clear_color)

        # Draw world surf
        NATIVE_SURF.blit(self.world_surf, (0, 0))

        # Draw world grid
        self._draw_world_grid()

        # When it is done only, so that it does not mess with combined cursor size
        if self.curtain.is_done:
            # Draw cursor
            updated_data = self._process_mouse_cursor(
                self.first_world_selected_tile_rect,
                self.second_world_selected_tile_rect,
                self.combined_world_selected_tile_rect,
                self.screen_combined_world_selected_tile_rect_x,
                self.screen_combined_world_selected_tile_rect_y,
                WORLD_WIDTH,
                WORLD_HEIGHT,
                WORLD_CELL_SIZE,
                True,
            )
            # Update the data after cursor
            self.first_world_selected_tile_rect = updated_data["first_rect"]
            self.second_world_selected_tile_rect = updated_data["second_rect"]
            self.combined_world_selected_tile_rect = updated_data["combined_rect"]
            self.screen_combined_world_selected_tile_rect_x = updated_data["screen_combined_rect_x"]
            self.screen_combined_world_selected_tile_rect_y = updated_data["screen_combined_rect_y"]

        # Curtain
        self.curtain.draw(NATIVE_SURF, 0)

    def _EDIT_ROOM_DRAW(self, _dt: int) -> None:
        """
        | Clear.
        | Draw parallax backgrounds.
        | Draw pre render backgrounds.
        | Draw static actors.
        | Draw player.
        | Draw pre render foregrounds.
        | Draw editor grid.
        | Draw editor cursor.
        | Draw curtain.
        """

        # Clear
        NATIVE_SURF.fill(self.clear_color)

        # Store surfs to be drawn with fblits for performance
        blit_sequence: list[
            # List of tuples = (surf, coord)
            tuple[pg.Surface, tuple[float, float]]
        ] = []

        # Collect parallax background surf
        for parallax_background in self.parallax_background_instances_list:
            # If it is not None, it is a parallax background instance
            if parallax_background is not None:
                blit_sequence = parallax_background.draw(blit_sequence)

        # Collect pre render background surf
        blit_sequence.append(
            (
                self.pre_render_background_surf,
                (
                    -self.camera.rect.x,
                    -self.camera.rect.y,
                ),
            )
        )

        # Collect static actor pre renders
        for static_actor_instance in self.sprite_sheet_static_actor_instance_dict.values():
            static_actor_instance.draw(blit_sequence)

        # Draw parallax background and pre render background collection
        NATIVE_SURF.fblits(blit_sequence)

        # TODO: Draw enemies first?

        # Draw player
        self.player.draw()

        # Draw the pre render foreground
        NATIVE_SURF.blit(
            self.pre_render_foreground_surf,
            (
                -self.camera.rect.x,
                -self.camera.rect.y,
            ),
        )

        # In editing mode?
        if not self.is_play_test_mode:
            # Draw grid
            self._draw_grid()

            # Filter only some sprite types

            # Combine rect fill (only some can turn this to true).
            if self.is_lmb_was_just_pressed:
                #################
                # Second select #
                #################
                # Draw combined cursor
                updated_data = self._process_mouse_cursor(
                    self.first_room_selected_tile_rect,
                    self.second_room_selected_tile_rect,
                    self.combined_room_selected_tile_rect,
                    self.screen_combined_room_selected_tile_rect_x,
                    self.screen_combined_room_selected_tile_rect_y,
                    self.room_width,
                    self.room_height,
                    TILE_SIZE,
                    False,
                )
                # Update the data after cursor
                self.first_room_selected_tile_rect = updated_data["first_rect"]
                self.second_room_selected_tile_rect = updated_data["second_rect"]
                self.combined_room_selected_tile_rect = updated_data["combined_rect"]
                self.screen_combined_room_selected_tile_rect_x = updated_data["screen_combined_rect_x"]
                self.screen_combined_room_selected_tile_rect_y = updated_data["screen_combined_rect_y"]
            # Normal paint, erase and flood fill
            else:
                # Draw cursor
                self._draw_cursor(
                    mouse_position_x_tuple_scaled_min=NATIVE_RECT.left,
                    mouse_position_x_tuple_scaled_max=NATIVE_RECT.right,
                    mouse_position_y_tuple_scaled_min=NATIVE_RECT.top,
                    mouse_position_y_tuple_scaled_max=NATIVE_RECT.bottom,
                    room_width=self.room_width,
                    room_height=self.room_height,
                    cursor_width=self.cursor_width,
                    cursor_height=self.cursor_height,
                    cell_size=TILE_SIZE,
                    is_world=False,
                )

        # Curtain
        self.curtain.draw(NATIVE_SURF, 0)

    def _SPRITE_PALLETE_DRAW(self, _dt: int) -> None:
        """
        | Clear.
        | Draw button container.
        | Draw curtain.
        """

        # Clear
        NATIVE_SURF.fill("black")

        # Draw button container
        if self.button_container is not None:
            self.button_container.draw(NATIVE_SURF)

        # Curtain
        self.curtain.draw(NATIVE_SURF, 0)

    #######################
    # STATE UPDATE LOGICS #
    #######################
    def _JUST_ENTERED_SCENE(self, dt: int) -> None:
        """
        | Counts up entry delay time.
        """

        self.entry_delay_timer.update(dt)

    def _OPENING_SCENE_CURTAIN(self, dt: int) -> None:
        """
        | Updates curtain alpha.
        """

        self.curtain.update(dt)

    def _OPENED_SCENE_CURTAIN(self, dt: int) -> None:
        """
        | First select room rect.
        """

        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # TODO: If click on a room, Load the room
            # TODO: So collision store the file name
            # TODO: If click on empty then make new one
            # TODO: Make schema later
            # Sprite selection
            if self.game_event_handler.is_lmb_just_pressed:
                # Get what is clicked
                found_tile_lmb_pressed = self._get_tile_from_world_collision_map_list(
                    self.world_mouse_tu_x,
                    self.world_mouse_tu_y,
                )
                # Clicked on empty? Create new room
                if found_tile_lmb_pressed == 0:
                    # Remember first selected tile rect
                    self.first_world_selected_tile_rect.x = self.world_mouse_snapped_x
                    self.first_world_selected_tile_rect.y = self.world_mouse_snapped_y
                    # Exit state
                    self.state_machine_update.change_state(RoomJsonGenerator.State.ADD_OTHER_ROOM)
                    self.state_machine_draw.change_state(RoomJsonGenerator.State.ADD_OTHER_ROOM)

    def _ADD_OTHER_SPRITES(self, dt: int) -> None:
        """
        | Second select room rect.
        """

        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Lmb just pressed
            if self.game_event_handler.is_lmb_just_pressed:
                # Check if selection is all empty cells, iterate size to check all empty
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
                        found_tile_lmb_pressed = self._get_tile_from_world_collision_map_list(
                            world_mouse_tu_x,
                            world_mouse_tu_y,
                        )
                        # At least 1 of them is occupied? Exit nested loop, set found occupied true
                        if found_tile_lmb_pressed != 0 and found_tile_lmb_pressed != -1:
                            found_occupied = True
                            break
                # All cells are empty?
                if not found_occupied:
                    # Update room metadata dimension and position
                    self.room_height = self.combined_world_selected_tile_rect_width_ru * ROOM_HEIGHT
                    self.room_height_tu = self.room_height // TILE_SIZE
                    self.room_width = self.combined_world_selected_tile_rect_height_ru * ROOM_WIDTH
                    self.room_width_tu = self.room_width // TILE_SIZE
                    self.room_topleft_x = self.combined_world_selected_tile_rect_x_ru * ROOM_WIDTH
                    self.room_topleft_y = self.combined_world_selected_tile_rect_y_ru * ROOM_HEIGHT
                    # Setup camera limits
                    self.camera.set_rect_limit(
                        float(0),
                        float(self.room_height),
                        float(0),
                        float(self.room_width),
                    )
                    # Update dynamic actors room size tu (for solid collisions)
                    self.player.set_room_height_tu(self.room_height_tu)
                    self.player.set_room_width_tu(self.room_width_tu)
                    # Close curtain
                    self.curtain.go_to_opaque()

        # Update curtain
        self.curtain.update(dt)

    def _FILE_NAME_QUERY(self, dt: int) -> None:
        """
        | Get file name user input
        """

        # Accept logic
        def _accept_callback() -> None:
            # Input not blank?
            if self.input_text != "":
                # Update room name / file name metadata
                self.file_name = self.input_text
                # Close curtain
                self.curtain.go_to_opaque()

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_SHEET_JSON_PATH_QUERY(self, dt: int) -> None:
        """
        | Get sprite sheet json user input
        """

        # Accept logic
        def _accept_callback() -> None:
            # Input JSON path exists?
            if exists(self.input_text) and self.input_text.endswith(".json"):
                # GET sprite_sheet_json_dict_from_disk from disk
                sprite_sheet_json_dict_from_disk: dict = self.game.GET_file_from_disk_dynamic_path(self.input_text)
                # Turn sprite_sheet_json_dict_from_disk to sprite_sheet_metadata_instance
                sprite_sheet_metadata_instance = instance_sprite_sheet_metadata(sprite_sheet_json_dict_from_disk)

                # Get sprite_sheet_png_name
                self.sprite_sheet_png_name = sprite_sheet_metadata_instance.sprite_sheet_png_name

                # Turn sprite_sheet_png_name to sprite_sheet_png_path
                sprite_sheet_png_path: str = get_one_target_dict_value(
                    key=self.sprite_sheet_png_name,
                    target_dict=PNGS_PATHS_DICT,
                    target_dict_name="PNGS_PATHS_DICT",
                )
                # Turn sprite_sheet_png_path to sprite_sheet_surf
                self.sprite_sheet_surf = pg.image.load(sprite_sheet_png_path).convert_alpha()

                # Get stage binded data with sprite_sheet_png_name
                self.sprite_sheet_static_actor_surfs_dict = self.game.get_sprite_sheet_static_actor_surfs_dict(
                    self.sprite_sheet_png_name
                )
                self.sprite_sheet_static_actor_jsons_dict = self.game.get_sprite_sheet_static_actor_jsons_dict(
                    self.sprite_sheet_png_name
                )
                self.sprite_sheet_parallax_background_mems_dict = self.game.get_sprite_sheet_parallax_mems_dict(
                    self.sprite_sheet_png_name
                )

                # Prepare button list to feed button container
                buttons: list[Button] = []

                # Iterate SpriteSheetMetadata members in sprite_sheet_metadata_instance
                for sprite_metadata_instance in sprite_sheet_metadata_instance.sprites_list:
                    # Collect {sprite_name : sprite_metadata_instance} in self.sprite_name_to_sprite_metadata
                    set_one_target_dict_value(
                        key=sprite_metadata_instance.sprite_name,
                        key_type=str,
                        val=sprite_metadata_instance,
                        val_type=SpriteMetadata,
                        target_dict=self.sprite_name_to_sprite_metadata,
                        target_dict_name="self.sprite_name_to_sprite_metadata",
                    )

                    # Create button for this SpriteMetadata
                    button: Button = Button(
                        surf_size_tuple=(264, 19),
                        topleft=(29, 14),
                        text=sprite_metadata_instance.sprite_name,
                        text_topleft=(53, 2),
                        description_text=sprite_metadata_instance.sprite_type,
                    )
                    # Create button icon from SpriteSheetMetadata surf with this SpriteMetadata region
                    subsurf: pg.Surface = self.sprite_sheet_surf.subsurface(
                        (
                            sprite_metadata_instance.x,
                            sprite_metadata_instance.y,
                            sprite_metadata_instance.width,
                            sprite_metadata_instance.height,
                        )
                    )
                    button = self._create_button_icons(
                        subsurf,
                        sprite_metadata_instance.width,
                        sprite_metadata_instance.height,
                        button,
                    )
                    # Collect button
                    buttons.append(button)

                    # This SpriteMetadata is a parallax background?
                    if sprite_metadata_instance.sprite_type == "parallax_background":
                        # Parallax not in binded?
                        if sprite_metadata_instance.sprite_name not in self.sprite_sheet_parallax_background_mems_dict:
                            # Raise exception
                            raise ValueError(
                                f"{sprite_metadata_instance.sprite_name} is not in sprite_sheet_parallax_background_mems_dict"
                            )
                        # Fill parallax layer with None for every parallax background found
                        self.parallax_background_instances_list.append(None)
                    # This SpriteMetadata is a background?
                    elif sprite_metadata_instance.sprite_type == "background":
                        # Count total background layers
                        if self.background_total_layers < sprite_metadata_instance.sprite_layer:
                            self.background_total_layers = sprite_metadata_instance.sprite_layer
                    # This SpriteMetadata is a foreground?
                    elif sprite_metadata_instance.sprite_type == "foreground":
                        # Count total foreground layers
                        if self.foreground_total_layers < sprite_metadata_instance.sprite_layer:
                            self.foreground_total_layers = sprite_metadata_instance.sprite_layer
                    # This SpriteMetadata is a static_actor?
                    elif sprite_metadata_instance.sprite_type == "static_actor":
                        # Static actor surf not in binded?
                        if sprite_metadata_instance.sprite_name not in self.sprite_sheet_static_actor_surfs_dict:
                            # Raise exception
                            raise ValueError(
                                f"{sprite_metadata_instance.sprite_name} is not in sprite_sheet_static_actor_surfs_dict"
                            )
                        # Static actor json not in binded?
                        if sprite_metadata_instance.sprite_name not in self.sprite_sheet_static_actor_jsons_dict:
                            # Raise exception
                            raise ValueError(
                                f"{sprite_metadata_instance.sprite_name} is not in sprite_sheet_static_actor_jsons_dict"
                            )

                        # Count total static_actor layers
                        if self.static_actor_total_layers < sprite_metadata_instance.sprite_layer:
                            self.static_actor_total_layers = sprite_metadata_instance.sprite_layer

                        # Get this static actor surf
                        static_actor_surf: pg.Surface = get_one_target_dict_value(
                            sprite_metadata_instance.sprite_name,
                            self.sprite_sheet_static_actor_surfs_dict,
                            "self.sprite_sheet_static_actor_surfs_dict",
                        )
                        # Get this static actor json dict {anim name: anim metadata instance}
                        static_actor_animation_metadata_instance: dict[str, AnimationMetadata] = get_one_target_dict_value(
                            sprite_metadata_instance.sprite_name,
                            self.sprite_sheet_static_actor_jsons_dict,
                            "self.sprite_sheet_static_actor_jsons_dict",
                        )
                        # Instance this new static actor
                        new_static_actor_instance = StaticActor(
                            static_actor_surf,
                            self.camera,
                            static_actor_animation_metadata_instance,
                            self.room_width,
                            self.room_height,
                            self.room_width_tu,
                            self.room_height_tu,
                        )
                        # Add this new static actor to dict (static actor name : static actor instance)
                        set_one_target_dict_value(
                            sprite_metadata_instance.sprite_name,
                            str,
                            new_static_actor_instance,
                            StaticActor,
                            self.sprite_sheet_static_actor_instance_dict,
                            "self.sprite_sheet_static_actor_instance_dict",
                        )

                # Init background layers collision map
                for _ in range(self.background_total_layers):
                    self.background_collision_map_list.append(
                        [0 for _ in range(self.room_width_tu * self.room_height_tu)],
                    )
                # Init static actor layers collision map
                for _ in range(self.static_actor_total_layers):
                    self.static_actor_collision_map_list.append(
                        [0 for _ in range(self.room_width_tu * self.room_height_tu)],
                    )
                # Init solids collision map (1 layer only for ceramic floor, cave floor, ...)
                self.solid_collision_map_list = [0 for _ in range(self.room_width_tu * self.room_height_tu)]
                # Init foreground layers collision map
                for _ in range(self.foreground_total_layers):
                    self.foreground_collision_map_list.append(
                        [0 for _ in range(self.room_width_tu * self.room_height_tu)],
                    )

                # Update dynamic actors's solid collision map list (dynamic needs ref to solids)
                self.player.set_solid_collision_map_list(self.solid_collision_map_list)

                # Init pre render background surf
                self.pre_render_background_surf = pg.Surface((self.room_width, self.room_height))
                self.pre_render_background_surf.set_colorkey("red")
                self.pre_render_background_surf.fill("red")
                # Init pre render foreground surf
                self.pre_render_foreground_surf = pg.Surface((self.room_width, self.room_height))
                self.pre_render_foreground_surf.set_colorkey("red")
                self.pre_render_foreground_surf.fill("red")

                # Init player
                # Construct sprite metadata
                player_name = "player"
                new_sprite_metadata_dict = {
                    "sprite_name": player_name,
                    "sprite_layer": 1,
                    "sprite_tile_type": "none",
                    "sprite_type": "dynamic_actor",
                    "sprite_is_tile_mix": 0,
                    # TODO: Update this with player sprite sheet data
                    "width": 6,
                    "height": 31,
                    "x": 0,
                    "y": 0,
                }
                # Turn into sprite metadata instance
                sprite_metadata_instance = instance_sprite_metadata(new_sprite_metadata_dict)

                # Add this new static actor to dict (static actor name : static actor instance)
                set_one_target_dict_value(
                    key=player_name,
                    key_type=str,
                    val=sprite_metadata_instance,
                    val_type=SpriteMetadata,
                    target_dict=self.sprite_name_to_sprite_metadata,
                    target_dict_name="self.sprite_name_to_sprite_metadata",
                )

                # Create button
                button = Button(
                    surf_size_tuple=(264, 19),
                    topleft=(29, 14),
                    text=player_name,
                    text_topleft=(53, 2),
                    description_text="dynamic_actor",
                )
                # Collect button
                buttons.append(button)

                # Init button container
                self.button_container = ButtonContainer(
                    buttons=buttons,
                    offset=0,
                    limit=7,
                    is_pagination=True,
                    game_event_handler=self.game_event_handler,
                    game_sound_manager=self.game.sound_manager,
                )
                self.button_container.add_event_listener(self._on_button_selected, ButtonContainer.BUTTON_SELECTED)
                # Init the first selected name
                self.selected_sprite_name = buttons[0].text
                # Get the value for the key, init the cursor size
                self.sprite_metadata_instance = get_one_target_dict_value(
                    key=self.selected_sprite_name,
                    target_dict=self.sprite_name_to_sprite_metadata,
                    target_dict_name="self.sprite_name_to_sprite_metadata",
                )
                # None has cursor size
                if sprite_metadata_instance.sprite_tile_type == "none":
                    self.cursor_width = sprite_metadata_instance.width
                    self.cursor_height = sprite_metadata_instance.height
                    self.cursor_width_tu = self.cursor_width // TILE_SIZE
                    self.cursor_height_tu = self.cursor_height // TILE_SIZE
                # Blob cursor size is 1 tile
                else:
                    self.cursor_width = TILE_SIZE
                    self.cursor_height = TILE_SIZE
                    self.cursor_width_tu = 1
                    self.cursor_height_tu = 1
                # Override the above, if it is parallax set to 1 by 1 too
                if sprite_metadata_instance.sprite_type == "parallax_background":
                    self.cursor_width = TILE_SIZE
                    self.cursor_height = TILE_SIZE
                    self.cursor_width_tu = 1
                    self.cursor_height_tu = 1
                # Exit
                self.curtain.go_to_opaque()
            else:
                self._set_input_text("JSON path does not exist!")

        # Typing logic
        self._handle_query_input(_accept_callback)

        # Update curtain
        self.curtain.update(dt)

    def _EDIT_ROOM(self, dt: int) -> None:
        # Reset flag to updte pre render
        self.is_pre_render_collision_map_list_mutated = False

        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Update static actors
            for static_actor_instance in self.sprite_sheet_static_actor_instance_dict.values():
                static_actor_instance.update(dt)

            # Editor mode
            if not self.is_play_test_mode:
                # Move camera with input
                self._move_camera_anchor_vector(dt)
                # Lerp camera position to target camera anchor
                self.camera.update(dt)

                # TODO: Turn the block to a func and use the name as key

                # Get sprite metadata from reformat with selected sprite name
                selected_sprite_type: str = self.sprite_metadata_instance.sprite_type
                selected_sprite_layer_index: int = self.sprite_metadata_instance.sprite_layer - 1
                selected_sprite_tile_type: str = self.sprite_metadata_instance.sprite_tile_type
                selected_sprite_x: int = self.sprite_metadata_instance.x
                selected_sprite_y: int = self.sprite_metadata_instance.y
                selected_sprite_name: str = self.sprite_metadata_instance.sprite_name

                #######################
                # DYNAMIC ACTOR STATE #
                #######################

                if selected_sprite_type == "dynamic_actor":
                    ###############
                    # Lmb pressed #
                    ###############
                    if self.game_event_handler.is_lmb_pressed:
                        # Get top left tile click position
                        world_mouse_x: int = self.world_mouse_tu_x * TILE_SIZE
                        world_mouse_y: int = self.world_mouse_tu_y * TILE_SIZE
                        # Turn it into tile mid bottom instead
                        world_mouse_bottom_left_x: int = world_mouse_x
                        world_mouse_bottom_left_y: int = world_mouse_y + TILE_SIZE
                        # Place player mid bottom, to the clicked cell bottom left
                        self.player.collider_rect.left = float(world_mouse_bottom_left_x - self.player.collider_rect.width / 2)
                        self.player.collider_rect.bottom = float(world_mouse_bottom_left_y)

                ######################
                # STATIC ACTOR STATE #
                ######################

                if selected_sprite_type == "static_actor":
                    # Get static_actor collision map LAYER
                    selected_static_actor_layer_collision_map: list[int] = self.static_actor_collision_map_list[
                        selected_sprite_layer_index
                    ]
                    # Get the selected static actor
                    selected_static_actor_instance: StaticActor = get_one_target_dict_value(
                        selected_sprite_name,
                        self.sprite_sheet_static_actor_instance_dict,
                        "self.sprite_sheet_static_actor_instance_dict",
                    )
                    ###############
                    # Lmb pressed #
                    ###############
                    if self.game_event_handler.is_lmb_pressed:
                        self._on_static_actor_lmb_pressed(
                            selected_static_actor_instance=selected_static_actor_instance,
                            world_mouse_tu_x=self.world_mouse_tu_x,
                            world_mouse_tu_y=self.world_mouse_tu_y,
                            collision_map_list=selected_static_actor_layer_collision_map,
                        )

                    ###############
                    # Rmb pressed #
                    ###############
                    if self.game_event_handler.is_rmb_pressed:
                        # Get clicked cell, static actor collision map list stores int only
                        found_tile = self._get_tile_from_collision_map_list(
                            self.world_mouse_tu_x,
                            self.world_mouse_tu_y,
                            selected_static_actor_layer_collision_map,
                        )

                        # Make sure value is int, NOT a NoneOrBlobSpriteMetadata
                        if isinstance(found_tile, NoneOrBlobSpriteMetadata):
                            raise ValueError("static_actor_collision_map_list cannot contain NoneOrBlobSpriteMetadata")

                        # Cell is occupied
                        if found_tile == 1:
                            # Turn it to zero
                            self._set_tile_from_collision_map_list(
                                world_tu_x=self.world_mouse_tu_x,
                                world_tu_y=self.world_mouse_tu_y,
                                value=0,
                                collision_map_list=selected_static_actor_layer_collision_map,
                            )
                            # Update pre render frame surfs based on collision map
                            selected_static_actor_instance.update_pre_render_frame_surfs(
                                collision_map_list=selected_static_actor_layer_collision_map,
                            )

                #############################
                # PARALLAX BACKGROUND STATE #
                #############################

                if selected_sprite_type == "parallax_background":
                    ####################
                    # Lmb just pressed #
                    ####################
                    if self.game_event_handler.is_lmb_just_pressed:
                        # This layer is None?
                        if self.parallax_background_instances_list[selected_sprite_layer_index] is None:
                            # Get binded mem with name
                            parallax_background_mem = get_one_target_dict_value(
                                self.selected_sprite_name,
                                self.sprite_sheet_parallax_background_mems_dict,
                                "self.sprite_sheet_parallax_background_mems_dict",
                            )
                            # Create new parallax background instance
                            new_parallax_background_instance = parallax_background_mem(
                                self.sprite_sheet_surf,
                                self.camera,
                                selected_sprite_name,
                                self.sprite_metadata_instance.width,
                                self.sprite_metadata_instance.height,
                                selected_sprite_x,
                                selected_sprite_y,
                            )
                            # Fill with new parallax background instance
                            self.parallax_background_instances_list[
                                selected_sprite_layer_index
                            ] = new_parallax_background_instance

                    ####################
                    # Rmb just pressed #
                    ####################
                    if self.game_event_handler.is_rmb_just_pressed:
                        # This layer has instance?
                        if self.parallax_background_instances_list[selected_sprite_layer_index] is not None:
                            # Make it None
                            self.parallax_background_instances_list[selected_sprite_layer_index] = None

                ####################
                # BACKGROUND STATE #
                ####################

                elif selected_sprite_type == "background":
                    # Get background collision map LAYER
                    selected_background_layer_collision_map: list[
                        int | NoneOrBlobSpriteMetadata
                    ] = self.background_collision_map_list[selected_sprite_layer_index]

                    #############################
                    # Combined rect paint state #
                    #############################

                    # TODO: Make a func for this, also make this works for the other sprite types too
                    # By design should not work with sprite that is bigger than 1 tile size
                    is_1_tile_size: bool = self.cursor_height == TILE_SIZE and self.cursor_width == TILE_SIZE
                    if self.game_event_handler.is_attack_pressed and is_1_tile_size:
                        ################
                        # First select #
                        ################
                        if not self.is_lmb_was_just_pressed:
                            # Lmb just pressed
                            if self.game_event_handler.is_lmb_just_pressed:
                                # Get what is clicked
                                found_tile_lmb_pressed = self._get_tile_from_collision_map_list(
                                    self.world_mouse_tu_x,
                                    self.world_mouse_tu_y,
                                    selected_background_layer_collision_map,
                                )
                                # Clicked on empty? Valid first selection
                                if found_tile_lmb_pressed == 0:
                                    # Remember first selected tile rect
                                    self.first_room_selected_tile_rect.x = self.world_mouse_snapped_x
                                    self.first_room_selected_tile_rect.y = self.world_mouse_snapped_y
                                    # Exit
                                    self.is_lmb_was_just_pressed = True
                        #################
                        # Second select #
                        #################
                        elif self.is_lmb_was_just_pressed:
                            # Lmb just pressed
                            if self.game_event_handler.is_lmb_just_released:
                                # TODO: Make a func for this
                                # Iterate size to check all empty
                                self.combined_room_selected_tile_rect_width_ru = int(
                                    self.combined_room_selected_tile_rect.width // TILE_SIZE
                                )
                                self.combined_room_selected_tile_rect_height_ru = int(
                                    self.combined_room_selected_tile_rect.height // TILE_SIZE
                                )
                                self.combined_room_selected_tile_rect_x_ru = int(
                                    self.combined_room_selected_tile_rect.x // TILE_SIZE
                                )
                                self.combined_room_selected_tile_rect_y_ru = int(
                                    self.combined_room_selected_tile_rect.y // TILE_SIZE
                                )
                                for world_tu_xi in range(self.combined_room_selected_tile_rect_width_ru):
                                    for world_tu_yi in range(self.combined_room_selected_tile_rect_height_ru):
                                        world_tu_x = self.combined_room_selected_tile_rect_x_ru + world_tu_xi
                                        world_tu_y = self.combined_room_selected_tile_rect_y_ru + world_tu_yi
                                        # Get each one in room_collision_map_list
                                        found_tile = self._get_tile_from_collision_map_list(
                                            world_tu_x,
                                            world_tu_y,
                                            selected_background_layer_collision_map,
                                        )
                                        # Find empty cell in combined here
                                        if found_tile == 0:
                                            ##################
                                            # NONE TILE TYPE #
                                            ##################

                                            if selected_sprite_tile_type == "none":
                                                self._on_lmb_just_pressed_none_tile_type(
                                                    # The selected collision map
                                                    selected_background_layer_collision_map,
                                                    # Other dynamic data this needs
                                                    selected_sprite_x,
                                                    selected_sprite_y,
                                                    selected_sprite_name,
                                                    # Then subsequent callbacks are from neighbor pos
                                                    world_tu_x=world_tu_x,
                                                    world_tu_y=world_tu_y,
                                                )

                                            ##################
                                            # BLOB TILE TYPE #
                                            ##################
                                            # Really slow but it works
                                            elif selected_sprite_tile_type != "none":
                                                self._on_lmb_just_pressed_blob_tile_type(
                                                    # The selected collision map
                                                    selected_background_layer_collision_map,
                                                    # Other dynamic data this needs
                                                    selected_sprite_x,
                                                    selected_sprite_y,
                                                    selected_sprite_tile_type,
                                                    selected_sprite_name,
                                                    # Then subsequent callbacks are from neighbor pos
                                                    world_tu_x=world_tu_x,
                                                    world_tu_y=world_tu_y,
                                                )
                                # Cleanup exit to enter first state again
                                # Reset flag
                                self.is_lmb_was_just_pressed = False
                    ######################
                    # Normal paint state #
                    ######################
                    else:
                        ####################
                        # Mmb just pressed #
                        ####################

                        if self.game_event_handler.is_mmb_just_pressed:
                            ##################
                            # NONE TILE TYPE #
                            ##################

                            if selected_sprite_tile_type == "none":

                                def _flood_fill_callback(world_tu_x: int, world_tu_y: int, collision_map_list: list) -> None:
                                    self._on_lmb_just_pressed_none_tile_type(
                                        # The selected collision map
                                        collision_map_list,
                                        # Other dynamic data this needs
                                        selected_sprite_x,
                                        selected_sprite_y,
                                        selected_sprite_name,
                                        # Then subsequent callbacks are from neighbor pos
                                        world_tu_x=world_tu_x,
                                        world_tu_y=world_tu_y,
                                    )

                                self._on_mmb_pressed(
                                    # Initiate with world mouse position
                                    world_tu_x=self.world_mouse_tu_x,
                                    world_tu_y=self.world_mouse_tu_y,
                                    # Set this selected collision map
                                    collision_map_list=selected_background_layer_collision_map,
                                    # The recursive callback
                                    callback=_flood_fill_callback,
                                )

                            ##################
                            # BLOB TILE TYPE #
                            ##################

                            if selected_sprite_tile_type != "none":

                                def _flood_fill_callback(world_tu_x: int, world_tu_y: int, collision_map_list: list) -> None:
                                    self._on_lmb_just_pressed_blob_tile_type(
                                        # The selected collision map
                                        collision_map_list,
                                        # Other dynamic data this needs
                                        selected_sprite_x,
                                        selected_sprite_y,
                                        selected_sprite_tile_type,
                                        selected_sprite_name,
                                        # Then subsequent callbacks are from neighbor pos
                                        world_tu_x=world_tu_x,
                                        world_tu_y=world_tu_y,
                                    )

                                self._on_mmb_pressed(
                                    # Initiate with world mouse position
                                    world_tu_x=self.world_mouse_tu_x,
                                    world_tu_y=self.world_mouse_tu_y,
                                    # Set this selected collision map
                                    collision_map_list=selected_background_layer_collision_map,
                                    # The recursive callback
                                    callback=_flood_fill_callback,
                                )

                        ###############
                        # Lmb pressed #
                        ###############

                        if self.game_event_handler.is_lmb_pressed:
                            ##################
                            # NONE TILE TYPE #
                            ##################

                            if selected_sprite_tile_type == "none":
                                self._on_lmb_just_pressed_none_tile_type(
                                    selected_background_layer_collision_map,
                                    selected_sprite_x,
                                    selected_sprite_y,
                                    selected_sprite_name,
                                    world_tu_x=self.world_mouse_tu_x,
                                    world_tu_y=self.world_mouse_tu_y,
                                )

                            ##################
                            # BLOB TILE TYPE #
                            ##################

                            if selected_sprite_tile_type != "none":
                                self._on_lmb_just_pressed_blob_tile_type(
                                    selected_background_layer_collision_map,
                                    selected_sprite_x,
                                    selected_sprite_y,
                                    selected_sprite_tile_type,
                                    selected_sprite_name,
                                    world_tu_x=self.world_mouse_tu_x,
                                    world_tu_y=self.world_mouse_tu_y,
                                )

                        ###############
                        # Rmb pressed #
                        ###############

                        if self.game_event_handler.is_rmb_pressed:
                            ##################
                            # NONE TILE TYPE #
                            ##################

                            if selected_sprite_tile_type == "none":
                                self._on_rmb_just_pressed_none_tile_type(
                                    selected_background_layer_collision_map,
                                )

                            ##################
                            # BLOB TILE TYPE #
                            ##################

                            if selected_sprite_tile_type != "none":
                                self._on_rmb_just_pressed_blob_tile_type(
                                    selected_background_layer_collision_map,
                                )

                ###############
                # SOLID STATE #
                ###############

                elif selected_sprite_type == "solid":
                    ####################
                    # Mmb just pressed #
                    ####################

                    if self.game_event_handler.is_mmb_just_pressed:
                        ##################
                        # NONE TILE TYPE #
                        ##################

                        if selected_sprite_tile_type == "none":

                            def _flood_fill_callback(world_tu_x: int, world_tu_y: int, collision_map_list: list) -> None:
                                self._on_lmb_just_pressed_none_tile_type(
                                    # The selected collision map
                                    collision_map_list,
                                    # Other dynamic data this needs
                                    selected_sprite_x,
                                    selected_sprite_y,
                                    selected_sprite_name,
                                    # Then subsequent callbacks are from neighbor pos
                                    world_tu_x=world_tu_x,
                                    world_tu_y=world_tu_y,
                                )

                            self._on_mmb_pressed(
                                # Initiate with world mouse position
                                world_tu_x=self.world_mouse_tu_x,
                                world_tu_y=self.world_mouse_tu_y,
                                # Set this selected collision map
                                collision_map_list=self.solid_collision_map_list,
                                # The recursive callback
                                callback=_flood_fill_callback,
                            )
                            # Update dynamic actors solid collision map list
                            self.player.set_solid_collision_map_list(self.solid_collision_map_list)

                        ##################
                        # BLOB TILE TYPE #
                        ##################

                        if selected_sprite_tile_type != "none":

                            def _flood_fill_callback(world_tu_x: int, world_tu_y: int, collision_map_list: list) -> None:
                                # Really slow but it works
                                self._on_lmb_just_pressed_blob_tile_type(
                                    # The selected collision map
                                    collision_map_list,
                                    # Other dynamic data this needs
                                    selected_sprite_x,
                                    selected_sprite_y,
                                    selected_sprite_tile_type,
                                    selected_sprite_name,
                                    # Then subsequent callbacks are from neighbor pos
                                    world_tu_x=world_tu_x,
                                    world_tu_y=world_tu_y,
                                )

                            self._on_mmb_pressed(
                                # Initiate with world mouse position
                                world_tu_x=self.world_mouse_tu_x,
                                world_tu_y=self.world_mouse_tu_y,
                                # Set this selected collision map
                                collision_map_list=self.solid_collision_map_list,
                                # The recursive callback
                                callback=_flood_fill_callback,
                            )
                            # Update dynamic actors solid collision map list
                            self.player.set_solid_collision_map_list(self.solid_collision_map_list)

                    ###############
                    # Lmb pressed #
                    ###############

                    if self.game_event_handler.is_lmb_pressed:
                        ##################
                        # NONE TILE TYPE #
                        ##################

                        if selected_sprite_tile_type == "none":
                            self._on_lmb_just_pressed_none_tile_type(
                                self.solid_collision_map_list,
                                selected_sprite_x,
                                selected_sprite_y,
                                selected_sprite_name,
                                world_tu_x=self.world_mouse_tu_x,
                                world_tu_y=self.world_mouse_tu_y,
                            )
                            # Update dynamic actors solid collision map list
                            self.player.set_solid_collision_map_list(self.solid_collision_map_list)

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
                                world_tu_x=self.world_mouse_tu_x,
                                world_tu_y=self.world_mouse_tu_y,
                            )
                            # Update dynamic actors solid collision map list
                            self.player.set_solid_collision_map_list(self.solid_collision_map_list)

                    ###############
                    # Rmb pressed #
                    ###############

                    if self.game_event_handler.is_rmb_pressed:
                        ##################
                        # NONE TILE TYPE #
                        ##################

                        if selected_sprite_tile_type == "none":
                            self._on_rmb_just_pressed_none_tile_type(
                                self.solid_collision_map_list,
                            )
                            # Update dynamic actors solid collision map list
                            self.player.set_solid_collision_map_list(self.solid_collision_map_list)

                        ##################
                        # BLOB TILE TYPE #
                        ##################

                        if selected_sprite_tile_type != "none":
                            self._on_rmb_just_pressed_blob_tile_type(
                                self.solid_collision_map_list,
                            )
                            # Update dynamic actors solid collision map list
                            self.player.set_solid_collision_map_list(self.solid_collision_map_list)

                ##############
                # THIN STATE #
                ##############

                elif selected_sprite_type == "thin":
                    ####################
                    # Mmb just pressed #
                    ####################

                    if self.game_event_handler.is_mmb_just_pressed:
                        ##################
                        # NONE TILE TYPE #
                        ##################

                        if selected_sprite_tile_type == "none":

                            def _flood_fill_callback(world_tu_x: int, world_tu_y: int, collision_map_list: list) -> None:
                                self._on_lmb_just_pressed_none_tile_type(
                                    # The selected collision map
                                    collision_map_list,
                                    # Other dynamic data this needs
                                    selected_sprite_x,
                                    selected_sprite_y,
                                    selected_sprite_name,
                                    # Then subsequent callbacks are from neighbor pos
                                    world_tu_x=world_tu_x,
                                    world_tu_y=world_tu_y,
                                )

                            self._on_mmb_pressed(
                                # Initiate with world mouse position
                                world_tu_x=self.world_mouse_tu_x,
                                world_tu_y=self.world_mouse_tu_y,
                                # Set this selected collision map
                                collision_map_list=self.solid_collision_map_list,
                                # The recursive callback
                                callback=_flood_fill_callback,
                            )
                            # Update dynamic actors solid collision map list
                            self.player.set_solid_collision_map_list(self.solid_collision_map_list)

                        ##################
                        # BLOB TILE TYPE #
                        ##################

                        if selected_sprite_tile_type != "none":

                            def _flood_fill_callback(world_tu_x: int, world_tu_y: int, collision_map_list: list) -> None:
                                # Really slow but it works
                                self._on_lmb_just_pressed_blob_tile_type(
                                    # The selected collision map
                                    collision_map_list,
                                    # Other dynamic data this needs
                                    selected_sprite_x,
                                    selected_sprite_y,
                                    selected_sprite_tile_type,
                                    selected_sprite_name,
                                    # Then subsequent callbacks are from neighbor pos
                                    world_tu_x=world_tu_x,
                                    world_tu_y=world_tu_y,
                                )

                            self._on_mmb_pressed(
                                # Initiate with world mouse position
                                world_tu_x=self.world_mouse_tu_x,
                                world_tu_y=self.world_mouse_tu_y,
                                # Set this selected collision map
                                collision_map_list=self.solid_collision_map_list,
                                # The recursive callback
                                callback=_flood_fill_callback,
                            )
                            # Update dynamic actors solid collision map list
                            self.player.set_solid_collision_map_list(self.solid_collision_map_list)

                    ###############
                    # Lmb pressed #
                    ###############

                    if self.game_event_handler.is_lmb_pressed:
                        ##################
                        # NONE TILE TYPE #
                        ##################

                        if selected_sprite_tile_type == "none":
                            self._on_lmb_just_pressed_none_tile_type(
                                self.solid_collision_map_list,
                                selected_sprite_x,
                                selected_sprite_y,
                                selected_sprite_name,
                                world_tu_x=self.world_mouse_tu_x,
                                world_tu_y=self.world_mouse_tu_y,
                            )
                            # Update dynamic actors solid collision map list
                            self.player.set_solid_collision_map_list(self.solid_collision_map_list)

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
                                world_tu_x=self.world_mouse_tu_x,
                                world_tu_y=self.world_mouse_tu_y,
                            )
                            # Update dynamic actors solid collision map list
                            self.player.set_solid_collision_map_list(self.solid_collision_map_list)

                    ###############
                    # Rmb pressed #
                    ###############

                    if self.game_event_handler.is_rmb_pressed:
                        ##################
                        # NONE TILE TYPE #
                        ##################

                        if selected_sprite_tile_type == "none":
                            self._on_rmb_just_pressed_none_tile_type(
                                self.solid_collision_map_list,
                            )
                            # Update dynamic actors solid collision map list
                            self.player.set_solid_collision_map_list(self.solid_collision_map_list)

                        ##################
                        # BLOB TILE TYPE #
                        ##################

                        if selected_sprite_tile_type != "none":
                            self._on_rmb_just_pressed_blob_tile_type(
                                self.solid_collision_map_list,
                            )
                            # Update dynamic actors solid collision map list
                            self.player.set_solid_collision_map_list(self.solid_collision_map_list)

                ####################
                # FOREGROUND STATE #
                ####################
                # TODO: Bind the selected_sprite_type as key to selected_foreground_layer_collision_map
                elif selected_sprite_type == "foreground":
                    # Get background layer collision map
                    selected_foreground_layer_collision_map: list[
                        int | NoneOrBlobSpriteMetadata
                    ] = self.foreground_collision_map_list[selected_sprite_layer_index]

                    ####################
                    # Mmb just pressed #
                    ####################

                    if self.game_event_handler.is_mmb_just_pressed:
                        ##################
                        # NONE TILE TYPE #
                        ##################

                        if selected_sprite_tile_type == "none":

                            def _flood_fill_callback(world_tu_x: int, world_tu_y: int, collision_map_list: list) -> None:
                                self._on_lmb_just_pressed_none_tile_type(
                                    # The selected collision map
                                    collision_map_list,
                                    # Other dynamic data this needs
                                    selected_sprite_x,
                                    selected_sprite_y,
                                    selected_sprite_name,
                                    # Then subsequent callbacks are from neighbor pos
                                    world_tu_x=world_tu_x,
                                    world_tu_y=world_tu_y,
                                )

                            self._on_mmb_pressed(
                                # Initiate with world mouse position
                                world_tu_x=self.world_mouse_tu_x,
                                world_tu_y=self.world_mouse_tu_y,
                                # Set this selected collision map
                                collision_map_list=selected_foreground_layer_collision_map,
                                # The recursive callback
                                callback=_flood_fill_callback,
                            )

                        ##################
                        # BLOB TILE TYPE #
                        ##################

                        if selected_sprite_tile_type != "none":

                            def _flood_fill_callback(world_tu_x: int, world_tu_y: int, collision_map_list: list) -> None:
                                # Really slow but it works
                                self._on_lmb_just_pressed_blob_tile_type(
                                    # The selected collision map
                                    collision_map_list,
                                    # Other dynamic data this needs
                                    selected_sprite_x,
                                    selected_sprite_y,
                                    selected_sprite_tile_type,
                                    selected_sprite_name,
                                    # Then subsequent callbacks are from neighbor pos
                                    world_tu_x=world_tu_x,
                                    world_tu_y=world_tu_y,
                                )

                            self._on_mmb_pressed(
                                # Initiate with world mouse position
                                world_tu_x=self.world_mouse_tu_x,
                                world_tu_y=self.world_mouse_tu_y,
                                # Set this selected collision map
                                collision_map_list=selected_foreground_layer_collision_map,
                                # The recursive callback
                                callback=_flood_fill_callback,
                            )

                    ###############
                    # Lmb pressed #
                    ###############

                    if self.game_event_handler.is_lmb_pressed:
                        ##################
                        # NONE TILE TYPE #
                        ##################

                        if selected_sprite_tile_type == "none":
                            self._on_lmb_just_pressed_none_tile_type(
                                selected_foreground_layer_collision_map,
                                selected_sprite_x,
                                selected_sprite_y,
                                selected_sprite_name,
                                world_tu_x=self.world_mouse_tu_x,
                                world_tu_y=self.world_mouse_tu_y,
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
                                world_tu_x=self.world_mouse_tu_x,
                                world_tu_y=self.world_mouse_tu_y,
                            )

                    ###############
                    # Rmb pressed #
                    ###############

                    if self.game_event_handler.is_rmb_pressed:
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

                # Update pre render
                if self.is_pre_render_collision_map_list_mutated:
                    self._update_pre_render()

                # Jump just pressed, go to pallete
                if self.game_event_handler.is_jump_just_pressed:
                    self.is_from_edit_pressed_jump = True
                    self.curtain.go_to_opaque()

            elif self.is_play_test_mode:
                # Move player with input
                self.player.update(dt)
                # Lerp camera position to target camera anchor
                self.camera.update(dt)
                # Move my camera anchor to where player is for convenience
                self.camera_anchor_vector.x = self.player.collider_rect.x
                self.camera_anchor_vector.y = self.player.collider_rect.y

            # Enter just pressed, go to play test state
            if self.game_event_handler.is_enter_just_pressed:
                # TODO: Enter a save or test mode later
                self.is_play_test_mode = not self.is_play_test_mode
                if self.is_play_test_mode:
                    self.camera.set_target_vector(self.player.camera_anchor_vector)
                else:
                    self.camera.set_target_vector(self.camera_anchor_vector)

        # Update curtain
        self.curtain.update(dt)

    def _SPRITE_PALETTE(self, dt: int) -> None:
        # Wait for curtain to be fully invisible
        if self.curtain.is_done:
            # Sprites pallete
            # Jump just pressed, go back to edit
            if self.game_event_handler.is_jump_just_pressed:
                self.is_from_pallete_pressed_jump = True
                if self.button_container is not None:
                    self.button_container.set_is_input_allowed(False)
                self.curtain.go_to_opaque()
                return

        # Even when curtain not done need to fade button
        if self.button_container is not None:
            self.button_container.update(dt)

        # Update curtain
        self.curtain.update(dt)

    def _CLOSING_SCENE_CURTAIN(self, dt: int) -> None:
        self.curtain.update(dt)

    def _CLOSED_SCENE_CURTAIN(self, dt: int) -> None:
        self.exit_delay_timer.update(dt)

    #####################
    # STATE TRANSITIONS #
    #####################
    def _JUST_ENTERED_SCENE_to_OPENING_SCENE_CURTAIN(self) -> None:
        self.curtain.go_to_invisible()

    def _OPENING_SCENE_CURTAIN_to_OPENED_SCENE_CURTAIN(self) -> None:
        # Make curtain faster for in state blink
        self.curtain.set_duration(self.FAST_FADE_DURATION)
        # Read all JSON room and mark it on grid
        for filename in listdir(JSONS_ROOMS_DIR_PATH):
            if filename.endswith(".json"):
                # Construct the full file path
                file_path = join(JSONS_ROOMS_DIR_PATH, filename)

                # Open and read the JSON file

                # GET from disk
                data = self.game.GET_file_from_disk_dynamic_path(file_path)

                # TODO: When save feature is done. Validate data or raise exception

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

                # TODO: render the doors
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

                        # Store each one in room_collision_map_list with file name
                        self._set_tile_from_world_collision_map_list(
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
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the file name to be saved,")

    def _FILE_NAME_QUERY_to_SPRITE_SHEET_JSON_PATH_QUERY(self) -> None:
        # Reset the input text
        self._set_input_text("")
        # Set my prompt text
        self._set_prompt_text("type the json path to be loaded,")

    def _SPRITE_SHEET_JSON_PATH_QUERY_to_EDIT_ROOM(self) -> None:
        pass

    def _EDIT_ROOM_to_SPRITE_PALETTE(self) -> None:
        self.is_from_edit_pressed_jump = False

    def _SPRITE_PALETTE_to_EDIT_ROOM(self) -> None:
        self.is_from_pallete_pressed_jump = False

    def _CLOSING_SCENE_CURTAIN_to_CLOSED_SCENE_CURTAIN(self) -> None:
        NATIVE_SURF.fill("black")

    #############
    # CALLBACKS #
    #############
    def _on_entry_delay_timer_end(self) -> None:
        self._change_update_and_draw_state_machine(RoomJsonGenerator.State.OPENING_SCENE_CURTAIN)

    def _on_exit_delay_timer_end(self) -> None:
        # Load title screen music. Played in my set state
        # TODO: Ask should this be schemaed or get set or what? Ask chatgpt
        self.game_music_manager.set_current_music_path(OGGS_PATHS_DICT["xdeviruchi_title_theme.ogg"])
        self.game_music_manager.play_music(-1, 0.0, 0)
        # TODO: Ask should this be schemaed or get set or what? Ask chatgpt
        self.game.set_scene("MainMenu")

    def _on_curtain_invisible(self) -> None:
        if self.state_machine_update.state == RoomJsonGenerator.State.OPENING_SCENE_CURTAIN:
            self._change_update_and_draw_state_machine(RoomJsonGenerator.State.OPENED_SCENE_CURTAIN)
        elif self.state_machine_update.state == RoomJsonGenerator.State.SPRITE_PALETTE:
            if self.button_container is not None:
                self.button_container.set_is_input_allowed(True)

    def _on_curtain_opaque(self) -> None:
        if self.state_machine_update.state == RoomJsonGenerator.State.ADD_OTHER_ROOM:
            self._change_update_and_draw_state_machine(RoomJsonGenerator.State.FILE_NAME_QUERY)
            self.curtain.go_to_invisible()
        elif self.state_machine_update.state == RoomJsonGenerator.State.FILE_NAME_QUERY:
            self._change_update_and_draw_state_machine(RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY)
            self.curtain.go_to_invisible()
        elif self.state_machine_update.state == RoomJsonGenerator.State.SPRITE_SHEET_JSON_PATH_QUERY:
            self._change_update_and_draw_state_machine(RoomJsonGenerator.State.EDIT_ROOM)
            self.curtain.go_to_invisible()
        elif self.state_machine_update.state == RoomJsonGenerator.State.EDIT_ROOM:
            if self.is_from_edit_pressed_jump:
                self._change_update_and_draw_state_machine(RoomJsonGenerator.State.SPRITE_PALETTE)
                self.curtain.go_to_invisible()
        elif self.state_machine_update.state == RoomJsonGenerator.State.SPRITE_PALETTE:
            if self.is_from_pallete_pressed_jump:
                self._change_update_and_draw_state_machine(RoomJsonGenerator.State.EDIT_ROOM)
                self.curtain.go_to_invisible()

    def _on_button_selected(self, selected_button: Button) -> None:
        # Update selected name
        self.selected_sprite_name = selected_button.text
        # Update cursor size
        self.sprite_metadata_instance = get_one_target_dict_value(
            key=self.selected_sprite_name,
            target_dict=self.sprite_name_to_sprite_metadata,
            target_dict_name="self.sprite_name_to_sprite_metadata",
        )
        # None has cursor size
        if self.sprite_metadata_instance.sprite_tile_type == "none":
            self.cursor_width = self.sprite_metadata_instance.width
            self.cursor_height = self.sprite_metadata_instance.height
            self.cursor_width_tu = self.cursor_width // TILE_SIZE
            self.cursor_height_tu = self.cursor_height // TILE_SIZE
        # Blob cursor size is 1 tile
        else:
            self.cursor_width = TILE_SIZE
            self.cursor_height = TILE_SIZE
            self.cursor_width_tu = 1
            self.cursor_height_tu = 1
        # Override the above, if it is parallax set to 1 by 1 too
        if self.sprite_metadata_instance.sprite_type == "parallax_background":
            self.cursor_width = TILE_SIZE
            self.cursor_height = TILE_SIZE
            self.cursor_width_tu = 1
            self.cursor_height_tu = 1
        # On select also counts as quiting pallete, you can only select button in pallete
        self.is_from_pallete_pressed_jump = True
        if self.button_container is not None:
            self.button_container.set_is_input_allowed(False)
        self.curtain.go_to_opaque()

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
        self.game_debug_draw.add(
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

    ###########
    # HELPERS #
    ###########
    def _on_mmb_pressed(self, world_tu_x: int, world_tu_y: int, collision_map_list: list, callback: Callable) -> None:
        if self.cursor_height > TILE_SIZE or self.cursor_width > TILE_SIZE:
            return

        stack = [(world_tu_x, world_tu_y)]
        processed = set()

        while stack:
            current_x, current_y = stack.pop()

            if (current_x, current_y) in processed:
                continue

            processed.add((current_x, current_y))

            callback(
                world_tu_x=current_x,
                world_tu_y=current_y,
                collision_map_list=collision_map_list,
            )

            adjacent_empty_tiles_list = self._get_adjacent_tiles_no_corners(
                world_tu_x=current_x,
                world_tu_y=current_y,
                collision_map_list=collision_map_list,
            )

            for adjacent_empty_tile in adjacent_empty_tiles_list:
                tu_x = adjacent_empty_tile[0]
                tu_y = adjacent_empty_tile[1]
                if (tu_x, tu_y) not in processed:
                    stack.append((tu_x, tu_y))

    def _on_static_actor_lmb_pressed(
        self,
        selected_static_actor_instance: StaticActor,
        world_mouse_tu_x: int,
        world_mouse_tu_y: int,
        collision_map_list: list,
    ) -> None:
        # Get clicked cell, static actor collision map list stores int only
        found_tile = self._get_tile_from_collision_map_list(
            world_mouse_tu_x,
            world_mouse_tu_y,
            collision_map_list,
        )

        # Make sure value is int, NOT a NoneOrBlobSpriteMetadata
        if isinstance(found_tile, NoneOrBlobSpriteMetadata):
            raise ValueError("static_actor_collision_map_list cannot contain NoneOrBlobSpriteMetadata")

        # Cell is empty
        if found_tile == 0:
            # Fill collision map with 1 in cursor pos
            self._set_tile_from_collision_map_list(
                world_tu_x=world_mouse_tu_x,
                world_tu_y=world_mouse_tu_y,
                value=1,
                collision_map_list=collision_map_list,
            )
            # Update pre render frame surfs based on collision map
            selected_static_actor_instance.update_pre_render_frame_surfs(
                collision_map_list,
            )

    def _change_update_and_draw_state_machine(self, value: Enum) -> None:
        """
        Update and change are the same, so use this to change both.
        """
        self.state_machine_update.change_state(value)
        self.state_machine_draw.change_state(value)

    def _draw_cursor(
        self,
        mouse_position_x_tuple_scaled_min: int,
        mouse_position_x_tuple_scaled_max: int,
        mouse_position_y_tuple_scaled_min: int,
        mouse_position_y_tuple_scaled_max: int,
        room_width: int,
        room_height: int,
        cursor_width: int,
        cursor_height: int,
        cell_size: int,
        is_world: bool,
    ) -> None:
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
            mouse_position_x_tuple_scaled_min,
            # Because this will refer to top left of a cell
            # If it is flushed to the right it is out of bound
            mouse_position_x_tuple_scaled_max - 1,
        )
        mouse_position_y_tuple_scaled = clamp(
            mouse_position_y_tuple_scaled,
            mouse_position_y_tuple_scaled_min,
            # Because this will refer to top left of a cell
            # If it is flushed to the bottom it is out of bound
            mouse_position_y_tuple_scaled_max - 1,
        )
        # Convert positions
        self.world_mouse_x = mouse_position_x_tuple_scaled + self.camera.rect.x
        self.world_mouse_y = mouse_position_y_tuple_scaled + self.camera.rect.y
        self.world_mouse_x = min(
            self.world_mouse_x,
            room_width - cursor_width,
        )
        self.world_mouse_y = min(
            self.world_mouse_y,
            room_height - cursor_height,
        )
        self.world_mouse_tu_x = int(self.world_mouse_x // cell_size)
        self.world_mouse_tu_y = int(self.world_mouse_y // cell_size)
        self.world_mouse_snapped_x = self.world_mouse_tu_x * cell_size
        self.world_mouse_snapped_y = self.world_mouse_tu_y * cell_size
        self.screen_mouse_x = self.world_mouse_snapped_x - self.camera.rect.x
        self.screen_mouse_y = self.world_mouse_snapped_y - self.camera.rect.y
        # If this is dynamic actor, add offset
        mid_bottom_offset_x = 0
        mid_bottom_offset_y = 0
        # Only have actors in room edit not world
        if not is_world:
            selected_sprite_type: str = self.sprite_metadata_instance.sprite_type
            # Handle dynamic_actor offset
            if selected_sprite_type == "dynamic_actor":
                mid_bottom_offset_x = cursor_width // 2
                mid_bottom_offset_y = cursor_height - TILE_SIZE
        # Draw cursor
        pg.draw.rect(
            NATIVE_SURF,
            "green",
            [
                self.screen_mouse_x - mid_bottom_offset_x,
                self.screen_mouse_y - mid_bottom_offset_y,
                cursor_width,
                cursor_height,
            ],
            1,
        )

    def _create_button_icons(self, subsurf: pg.Surface, width: int, height: int, button: Button) -> Button:
        """
        Pass a subsurf, original height and width, and the button to draw the icon on.
        On draw completion the button is returned.
        """
        # Create button icon from sprite sheet surf with metadata region
        base_subsurf_width = 49
        base_subsurf_height = 19
        base_subsurf = pg.Surface((base_subsurf_width, base_subsurf_height))
        base_subsurf.fill(self.clear_color)
        scaled_height = base_subsurf_width * height / width
        subsurf = pg.transform.scale(subsurf, (base_subsurf_width, scaled_height))
        y_diff = scaled_height - base_subsurf_height
        base_subsurf.blit(subsurf, (0, -y_diff / 2))
        button.draw_extra_surf_on_surf(base_subsurf, (1, 0))
        return button

    def _update_pre_render(self) -> None:
        """
        Get new surfs for pre renders.
        Iter the collision map to draw on it.
        """
        # Clear pre render, make new ones so it does not build up data
        # Pre render background
        self.pre_render_background_surf = pg.Surface((self.room_width, self.room_height))
        self.pre_render_background_surf.set_colorkey("red")
        self.pre_render_background_surf.fill("red")
        # Pre render foreground
        self.pre_render_foreground_surf = pg.Surface((self.room_width, self.room_height))
        self.pre_render_foreground_surf.set_colorkey("red")
        self.pre_render_foreground_surf.fill("red")

        # Iter over each background collision map layer
        for collision_map in self.background_collision_map_list:
            # Iter over cells
            for cell in collision_map:
                # Ignore air, if it is not 0, its NoneOrBlobSpriteMetadata
                if cell == 0:
                    continue

                # Make sure value is a NoneOrBlobSpriteMetadata
                if not isinstance(cell, NoneOrBlobSpriteMetadata):
                    raise ValueError("background_collision_map_list can only hold int or NoneOrBlobSpriteMetadata")

                # Unpack NoneOrBlobSpriteMetadata
                x = cell.x
                y = cell.y
                region_x = cell.region_x
                region_y = cell.region_y
                # Draw each one on pre_render_background
                if self.sprite_sheet_surf is not None:
                    # Cannot use fblits because this has regions
                    self.pre_render_background_surf.blit(
                        self.sprite_sheet_surf, (x, y), (region_x, region_y, TILE_SIZE, TILE_SIZE)
                    )

        # Iter over cells
        for cell in self.solid_collision_map_list:
            # Ignore air, if it is not 0, its NoneOrBlobSpriteMetadata
            if cell == 0:
                continue

            # Make sure value is a NoneOrBlobSpriteMetadata
            if not isinstance(cell, NoneOrBlobSpriteMetadata):
                raise ValueError("foreground_collision_map_list can only hold int or NoneOrBlobSpriteMetadata")

            # Unpack NoneOrBlobSpriteMetadata
            x = cell.x
            y = cell.y
            region_x = cell.region_x
            region_y = cell.region_y
            # Draw each one on pre render
            if self.sprite_sheet_surf is not None:
                # Cannot use fblits because this has regions
                self.pre_render_foreground_surf.blit(self.sprite_sheet_surf, (x, y), (region_x, region_y, TILE_SIZE, TILE_SIZE))

        # Iter over each foreground collision map layer
        for collision_map in self.foreground_collision_map_list:
            # Iter over cells
            for cell in collision_map:
                # Ignore air, if it is not 0, its NoneOrBlobSpriteMetadata
                if cell == 0:
                    continue

                # Make sure value is a NoneOrBlobSpriteMetadata
                if not isinstance(cell, NoneOrBlobSpriteMetadata):
                    raise ValueError("foreground_collision_map_list can only hold int or NoneOrBlobSpriteMetadata")

                # Unpack NoneOrBlobSpriteMetadata
                x = cell.x
                y = cell.y
                region_x = cell.region_x
                region_y = cell.region_y
                # Draw each one on pre render
                if self.sprite_sheet_surf is not None:
                    # Cannot use fblits because this has regions
                    self.pre_render_foreground_surf.blit(
                        self.sprite_sheet_surf, (x, y), (region_x, region_y, TILE_SIZE, TILE_SIZE)
                    )

    def _on_rmb_just_pressed_none_tile_type(
        self,
        collision_map_list: list[Any],
    ) -> None:
        """
        Click filled tile. Erase and set to 0.
        """
        self._fill_cursor_region_collision_map_with_0(collision_map_list)

    def _on_rmb_just_pressed_blob_tile_type(
        self,
        collision_map_list: list[Any],
    ) -> None:
        """
        Click filled tile. Erase and set to 0.
        Tell neighbor to autotile update draw.
        """
        # Get clicked cell
        found_tile = self._get_tile_from_collision_map_list(
            self.world_mouse_tu_x,
            self.world_mouse_tu_y,
            collision_map_list,
        )
        # Cell is filled
        if found_tile != 0 and found_tile != -1:
            # Fill collision map with 0 in cursor pos
            self._set_tile_from_collision_map_list(
                world_tu_x=self.world_mouse_tu_x,
                world_tu_y=self.world_mouse_tu_y,
                value=0,
                collision_map_list=collision_map_list,
            )

            # Get my neighbors
            adjacent_tile_obj_neighbors = self._get_adjacent_tiles(
                self.world_mouse_tu_x,
                self.world_mouse_tu_y,
                collision_map_list,
            )
            # Iterate each neighbors
            for neighbor_obj in adjacent_tile_obj_neighbors:
                # Make sure value is a AdjacentTileMetadata
                if not isinstance(neighbor_obj, AdjacentTileMetadata):
                    raise ValueError("getter result should contain AdjacentTileMetadata only")

                # Unpack AdjacentTileMetadata
                neighbor_tile_name = neighbor_obj.tile
                neighbor_world_tu_x = neighbor_obj.world_tu_x
                neighbor_world_tu_y = neighbor_obj.world_tu_y
                neighbor_world_snapped_x = neighbor_world_tu_x * TILE_SIZE
                neighbor_world_snapped_y = neighbor_world_tu_y * TILE_SIZE

                # Get neighbor sprite metadata
                sprite_metadata_instance: SpriteMetadata = get_one_target_dict_value(
                    key=neighbor_tile_name,
                    target_dict=self.sprite_name_to_sprite_metadata,
                    target_dict_name="self.sprite_name_to_sprite_metadata",
                )
                neighbor_sprite_is_tile_mix = sprite_metadata_instance.sprite_is_tile_mix
                neighbor_sprite_x = sprite_metadata_instance.x
                neighbor_sprite_y = sprite_metadata_instance.y
                neighbor_sprite_tile_type = sprite_metadata_instance.sprite_tile_type

                # Neighbor not my kind?
                if neighbor_tile_name != self.selected_sprite_name:
                    # Neighbor not mixed? Do not want to mix with me
                    if neighbor_sprite_is_tile_mix == 0:
                        # Skip this neighbor
                        continue

                # This neighbor wants to mix with me, so update its autotile

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
        collision_map_list: list[int | NoneOrBlobSpriteMetadata],
        selected_sprite_x: int,
        selected_sprite_y: int,
        selected_sprite_name: str,
        world_tu_x: int,
        world_tu_y: int,
    ) -> None:
        """
        If cursor region is empty, draw and set collision.
        """
        # All cells in cursor region empty
        if not self._is_cursor_region_collision_map_empty(
            collision_map_list,
            world_tu_x,
            world_tu_y,
        ):
            self._fill_cursor_region_collision_map_with_metadata(
                collision_map_list,
                selected_sprite_name,
                selected_sprite_x,
                selected_sprite_y,
                world_tu_x,
                world_tu_y,
            )

    def _on_lmb_just_pressed_blob_tile_type(
        self,
        collision_map_list: list[int | NoneOrBlobSpriteMetadata],
        selected_sprite_x: int,
        selected_sprite_y: int,
        selected_sprite_tile_type: str,
        selected_sprite_name: str,
        world_tu_x: int,
        world_tu_y: int,
    ) -> None:
        """
        If cursor region is empty, draw and set collision.
        Draw with correct autotile and tell neighbor to do it too.
        """
        # Get clicked cell
        found_tile = self._get_tile_from_collision_map_list(
            world_tu_x,
            world_tu_y,
            collision_map_list,
        )
        # Cell is empty
        if found_tile == 0:
            # Construct sprite metadata
            world_snapped_x = world_tu_x * TILE_SIZE
            world_snapped_y = world_tu_y * TILE_SIZE
            new_none_or_blob_sprite_metadata_dict: dict = {
                "name": selected_sprite_name,
                "type": self.sprite_metadata_instance.sprite_type,
                "x": world_snapped_x,
                "y": world_snapped_y,
                "region_x": selected_sprite_x,
                "region_y": selected_sprite_y,
            }

            # Turn into sprite metadata instance
            none_or_blob_sprite_metadata_instance = instance_none_or_blob_sprite_metadata(new_none_or_blob_sprite_metadata_dict)

            # Make sure value is a SpriteMetadata
            if not isinstance(none_or_blob_sprite_metadata_instance, NoneOrBlobSpriteMetadata):
                raise ValueError("Invalid none or blob sprite metadata JSON data against schema")

            # Fill collision map with sprite name in cursor pos
            self._set_tile_from_collision_map_list(
                world_tu_x=world_tu_x,
                world_tu_y=world_tu_y,
                value=none_or_blob_sprite_metadata_instance,
                collision_map_list=collision_map_list,
            )

            # Draw autotile on surf with proper offset
            self._draw_autotile_sprite_on_given_pos(
                selected_sprite_tile_type,
                selected_sprite_x,
                selected_sprite_y,
                world_tu_x,
                world_tu_y,
                collision_map_list,
                # surf,
                world_snapped_x,
                world_snapped_y,
                selected_sprite_name,
            )

            # Get my neighbors
            adjacent_tile_obj_neighbors = self._get_adjacent_tiles(
                world_tu_x,
                world_tu_y,
                collision_map_list,
            )
            # Iterate each neighbors
            for neighbor_obj in adjacent_tile_obj_neighbors:
                # Make sure that neighbor_obj is AdjacentTileMetadata
                if not isinstance(neighbor_obj, AdjacentTileMetadata):
                    raise ValueError("Invalid found adjacent neighbor format, should be AdjacentTileMetadata")
                # Unpack the neighbor object, get name and coords
                neighbor_tile_name = neighbor_obj.tile
                neighbor_world_tu_x = neighbor_obj.world_tu_x
                neighbor_world_tu_y = neighbor_obj.world_tu_y
                neighbor_world_snapped_x = neighbor_world_tu_x * TILE_SIZE
                neighbor_world_snapped_y = neighbor_world_tu_y * TILE_SIZE

                # Get neighbor sprite metadata
                sprite_metadata_instance: SpriteMetadata = get_one_target_dict_value(
                    key=neighbor_tile_name,
                    target_dict=self.sprite_name_to_sprite_metadata,
                    target_dict_name="self.sprite_name_to_sprite_metadata",
                )
                neighbor_sprite_is_tile_mix = sprite_metadata_instance.sprite_is_tile_mix
                neighbor_sprite_x = sprite_metadata_instance.x
                neighbor_sprite_y = sprite_metadata_instance.y
                neighbor_sprite_tile_type = sprite_metadata_instance.sprite_tile_type

                # Neighbor not my kind?
                if neighbor_tile_name != self.selected_sprite_name:
                    # Neighbor not mixed? Do not want to mix with me
                    if neighbor_sprite_is_tile_mix == 0:
                        # Skip this neighbor
                        continue

                # This neighbor wants to mix with me, so update its autotile

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
        # TODO: Type safety for this one
        binary_to_offset_dict = SPRITE_TILE_TYPE_BINARY_TO_OFFSET_DICT[sprite_tile_type]
        directions = SPRITE_TILE_TYPE_SPRITE_ADJACENT_NEIGHBOR_DIRECTIONS_LIST[sprite_tile_type]

        # Prepare top left with offset
        sprite_x_with_offset = sprite_x
        sprite_y_with_offset = sprite_y

        # Check my neighbours to determine my binary representation
        binary_value = self._get_surrounding_tile_value(
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
        # Construct sprite metadata
        new_none_or_blob_sprite_metadata_dict: dict = {
            "name": sprite_name,
            "type": self.sprite_metadata_instance.sprite_type,
            "x": sprite_snapped_x,
            "y": sprite_snapped_y,
            "region_x": sprite_x_with_offset,
            "region_y": sprite_y_with_offset,
        }

        # Turn into sprite metadata instance
        none_or_blob_sprite_metadata_instance = instance_none_or_blob_sprite_metadata(new_none_or_blob_sprite_metadata_dict)

        # Make sure value is a SpriteMetadata
        if not isinstance(none_or_blob_sprite_metadata_instance, NoneOrBlobSpriteMetadata):
            raise ValueError("Invalid none or blob sprite metadata JSON data against schema")

        self._set_tile_from_collision_map_list(
            world_tu_x=sprite_world_tu_x,
            world_tu_y=sprite_world_tu_y,
            value=none_or_blob_sprite_metadata_instance,
            collision_map_list=selected_layer_collision_map,
        )

    def _fill_cursor_region_collision_map_with_0(
        self,
        collision_map: list,
    ) -> None:
        # Fill collision map with sprite name in cursor area
        for cursor_tu_x in range(self.cursor_width_tu):
            for cursor_tu_y in range(self.cursor_height_tu):
                tu_x = self.world_mouse_tu_x + cursor_tu_x
                tu_y = self.world_mouse_tu_y + cursor_tu_y

                self._set_tile_from_collision_map_list(
                    world_tu_x=tu_x,
                    world_tu_y=tu_y,
                    value=0,
                    collision_map_list=collision_map,
                )

    def _fill_cursor_region_collision_map_with_metadata(
        self,
        collision_map_list: list[int | NoneOrBlobSpriteMetadata],
        sprite_name: str,
        region_x: int,
        region_y: int,
        world_tu_x: int,
        world_tu_y: int,
    ) -> None:
        # Fill collision map with sprite name in cursor area
        for cursor_tu_x in range(self.cursor_width_tu):
            for cursor_tu_y in range(self.cursor_height_tu):
                tu_x = world_tu_x + cursor_tu_x
                tu_y = world_tu_y + cursor_tu_y
                world_snapped_x = world_tu_x * TILE_SIZE
                world_snapped_y = world_tu_y * TILE_SIZE
                world_mouse_x_snapped = world_snapped_x + (cursor_tu_x * TILE_SIZE)
                world_mouse_y_snapped = world_snapped_y + (cursor_tu_y * TILE_SIZE)
                region_x_with_offset = region_x + (cursor_tu_x * TILE_SIZE)
                region_y_with_offset = region_y + (cursor_tu_y * TILE_SIZE)

                # Construct sprite metadata
                new_none_or_blob_sprite_metadata_dict: dict = {
                    "name": sprite_name,
                    "type": self.sprite_metadata_instance.sprite_type,
                    "x": world_mouse_x_snapped,
                    "y": world_mouse_y_snapped,
                    "region_x": region_x_with_offset,
                    "region_y": region_y_with_offset,
                }

                # Turn into sprite metadata instance
                none_or_blob_sprite_metadata_instance = instance_none_or_blob_sprite_metadata(
                    new_none_or_blob_sprite_metadata_dict
                )

                # Make sure value is a SpriteMetadata
                if not isinstance(none_or_blob_sprite_metadata_instance, NoneOrBlobSpriteMetadata):
                    raise ValueError("Invalid none or blob sprite metadata JSON data against schema")

                self._set_tile_from_collision_map_list(
                    world_tu_x=tu_x,
                    world_tu_y=tu_y,
                    value=none_or_blob_sprite_metadata_instance,
                    collision_map_list=collision_map_list,
                )

    def _is_cursor_region_collision_map_empty(
        self,
        collision_map: list,
        world_tu_x: int,
        world_tu_y: int,
    ) -> bool:
        # Iterate cursor area
        found_occupied = False
        for cursor_tu_x in range(self.cursor_width_tu):
            if found_occupied:
                break
            for cursor_tu_y in range(self.cursor_height_tu):
                tu_x = world_tu_x + cursor_tu_x
                tu_y = world_tu_y + cursor_tu_y
                # Get each tile in cursor area
                found_tile = self._get_tile_from_collision_map_list(
                    tu_x,
                    tu_y,
                    collision_map,
                )
                # 1 tile in cursor area is occupied?
                if found_tile != 0 and found_tile != -1:
                    # Break
                    found_occupied = True
                    break

        return found_occupied

    def _move_camera_anchor_vector(self, dt: int) -> None:
        # Get direction_horizontal
        direction_horizontal: int = self.game_event_handler.is_right_pressed - self.game_event_handler.is_left_pressed
        # Update camera anchor position with direction and speed
        self.camera_anchor_vector.x += direction_horizontal * self.camera_speed * dt
        # Get direction_vertical
        direction_vertical: int = self.game_event_handler.is_down_pressed - self.game_event_handler.is_up_pressed
        # Update camera anchor position with direction and speed
        self.camera_anchor_vector.y += direction_vertical * self.camera_speed * dt

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

    def _draw_grid(self) -> None:
        blit_sequence = []
        for i in range(NATIVE_WIDTH_TU):
            vertical_line_x_position: float = (TILE_SIZE * i - self.camera.rect.x) % NATIVE_WIDTH
            blit_sequence.append(
                (
                    self.grid_room_vertical_line_surf,
                    (vertical_line_x_position, 0.0),
                )
            )
            horizontal_line_y_position: float = (TILE_SIZE * i - self.camera.rect.y) % NATIVE_WIDTH
            blit_sequence.append(
                (
                    self.grid_room_horizontal_line_surf,
                    (0.0, horizontal_line_y_position),
                )
            )

        NATIVE_SURF.fblits(blit_sequence)

    def _get_tile_from_world_collision_map_list(
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

    def _set_tile_from_world_collision_map_list(
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

    def _get_tile_from_collision_map_list(
        self,
        world_tu_x: int,
        world_tu_y: int,
        collision_map_list: list,
    ) -> int | NoneOrBlobSpriteMetadata:
        """
        Returns -1 if out of bounds
        Because camera needs extra 1 and thus may get out of bound.
        """
        if 0 <= world_tu_x < self.room_width_tu and 0 <= world_tu_y < self.room_height_tu:
            return collision_map_list[world_tu_y * self.room_width_tu + world_tu_x]
        else:
            return -1

    def _set_tile_from_collision_map_list(
        self,
        world_tu_x: int,
        world_tu_y: int,
        value: (int | NoneOrBlobSpriteMetadata),
        collision_map_list: list,
    ) -> None | int:
        """
        Returns -1 if out of bounds
        Because camera needs extra 1 and thus may get out of bound.
        """
        # TODO: create a condition for this, only update collision map list for pre render
        self.is_pre_render_collision_map_list_mutated = True
        if 0 <= world_tu_x < self.room_width_tu and 0 <= world_tu_y < self.room_height_tu:
            collision_map_list[world_tu_y * self.room_width_tu + world_tu_x] = value
            return None
        else:
            return -1

    def _get_surrounding_tile_value(
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
            tile = self._get_tile_from_collision_map_list(
                adjacent_x,
                adjacent_y,
                collision_map_list,
            )
            # Found something
            if tile != -1 and tile != 0:
                # Should be a NoneOrBlobSpriteMetadata not actor
                if not isinstance(tile, NoneOrBlobSpriteMetadata):
                    raise ValueError("Invalid none or blob sprite metadata JSON data against schema")

                sprite_metadata_instance_neighbor_tile_name: SpriteMetadata = get_one_target_dict_value(
                    key=tile.name,
                    target_dict=self.sprite_name_to_sprite_metadata,
                    target_dict_name="self.sprite_name_to_sprite_metadata",
                )

                # Not my kind and not mixed? Skip this one
                neighbor_tile_name = sprite_metadata_instance_neighbor_tile_name.sprite_name

                sprite_metadata_instance_neighbor_sprite_is_tile_mix: SpriteMetadata = get_one_target_dict_value(
                    key=neighbor_tile_name,
                    target_dict=self.sprite_name_to_sprite_metadata,
                    target_dict_name="self.sprite_name_to_sprite_metadata",
                )

                just_added_sprite_name = self.sprite_metadata_instance.sprite_name

                if neighbor_tile_name != just_added_sprite_name:
                    neighbor_sprite_is_tile_mix = sprite_metadata_instance_neighbor_sprite_is_tile_mix.sprite_is_tile_mix
                    if not neighbor_sprite_is_tile_mix:
                        continue
                # For corner tiles, check that they have both neighbor in the cardinal directions
                if (dx, dy) in cardinal_directions:
                    has_cardinal_neighbor = True
                    for cdx, cdy in cardinal_directions[(dx, dy)]:
                        cardinal_x = world_tu_x + cdx
                        cardinal_y = world_tu_y + cdy
                        cardinal_tile = self._get_tile_from_collision_map_list(
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

    def _get_adjacent_tiles_no_corners(
        self,
        world_tu_x: int,
        world_tu_y: int,
        collision_map_list: list,
    ) -> list[list[int]]:
        """
        Returns a list of 4 adjacent empty tiles coord world tu around the specified coordinates.

        Index 0 = adjacent_world_tu_x

        Index 1 = adjacent_world_tu_y
        """
        adjacent_tiles: list[list[int]] = []
        # Directions: top, left, right, bottom
        directions = [(0, -1), (-1, 0), (1, 0), (0, 1)]

        for dx, dy in directions:
            adjacent_world_tu_x = world_tu_x + dx
            adjacent_world_tu_y = world_tu_y + dy

            tile = self._get_tile_from_collision_map_list(
                adjacent_world_tu_x,
                adjacent_world_tu_y,
                collision_map_list,
            )

            # Found empty
            if tile == 0:
                # I do not care what it is here, just need the coord of the empty neighbor
                adjacent_tiles.append(
                    [
                        adjacent_world_tu_x,
                        adjacent_world_tu_y,
                    ]
                )

        return adjacent_tiles

    def _get_adjacent_tiles(
        self,
        world_tu_x: int,
        world_tu_y: int,
        collision_map_list: list,
    ) -> list[AdjacentTileMetadata]:
        """
        Returns a list of 8 adjacent tiles around the specified coordinates.
        Each tile is represented as object with tile value as key and coords as values
        """
        adjacent_tiles: list[AdjacentTileMetadata] = []
        # Directions: top-left, top, top-right, left, right, bottom-left, bottom, bottom-right
        directions = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]

        for dx, dy in directions:
            adjacent_x = world_tu_x + dx
            adjacent_y = world_tu_y + dy

            tile = self._get_tile_from_collision_map_list(
                adjacent_x,
                adjacent_y,
                collision_map_list,
            )

            # Found something
            if tile != -1 and tile != 0:
                # Should be a NoneOrBlobSpriteMetadata not actor
                if not isinstance(tile, NoneOrBlobSpriteMetadata):
                    raise ValueError("Invalid none or blob sprite metadata JSON data against schema")
                adjacent_tile_dict: dict = {
                    "tile": tile.name,
                    "world_tu_x": adjacent_x,
                    "world_tu_y": adjacent_y,
                }
                adjacent_tile_instance = instance_adjacent_tile_metadata(adjacent_tile_dict)
                # Make sure value is a AdjacentTileMetadata
                if not isinstance(adjacent_tile_instance, AdjacentTileMetadata):
                    raise ValueError("getter adjacent tile invalid output construction")
                adjacent_tiles.append(adjacent_tile_instance)

        return adjacent_tiles

    def _process_mouse_cursor(
        self,
        first_rect: pg.FRect,
        second_rect: pg.FRect,
        combined_rect: pg.FRect,
        screen_combined_rect_x: float,
        screen_combined_rect_y: float,
        room_width: int,
        room_height: int,
        cell_size: int,
        clamp_rect: bool,
    ) -> dict[str, Any]:
        """
        This function returns the paseed argument back in a dict where the key is the same str name to its parameters.
        This is because it does not update the self prop in place.
        """
        # Get and scale mouse position
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
        if clamp_rect:
            mouse_position_x_tuple_scaled = clamp(
                mouse_position_x_tuple_scaled,
                (first_rect.x - cell_size),
                # Because this will refer to top left of a cell
                # If it is flushed to the right it is out of bound
                (first_rect.x + 2 * cell_size) - 1,
            )
            mouse_position_y_tuple_scaled = clamp(
                mouse_position_y_tuple_scaled,
                (first_rect.y - cell_size),
                # Because this will refer to top left of a cell
                # If it is flushed to the bottom it is out of bound
                (first_rect.y + 2 * cell_size) - 1,
            )
        else:
            mouse_position_x_tuple_scaled = clamp(
                mouse_position_x_tuple_scaled,
                0,
                # Because this will refer to top left of a cell
                # If it is flushed to the right it is out of bound
                room_width - 1,
            )
            mouse_position_y_tuple_scaled = clamp(
                mouse_position_y_tuple_scaled,
                0,
                # Because this will refer to top left of a cell
                # If it is flushed to the bottom it is out of bound
                room_height - 1,
            )
        # Convert positions
        self.world_mouse_x = mouse_position_x_tuple_scaled + self.camera.rect.x
        self.world_mouse_y = mouse_position_y_tuple_scaled + self.camera.rect.y
        self.world_mouse_x = min(
            self.world_mouse_x,
            room_width - cell_size,
        )
        self.world_mouse_y = min(
            self.world_mouse_y,
            room_height - cell_size,
        )
        self.world_mouse_tu_x = int(self.world_mouse_x // cell_size)
        self.world_mouse_tu_y = int(self.world_mouse_y // cell_size)
        self.world_mouse_snapped_x = self.world_mouse_tu_x * cell_size
        self.world_mouse_snapped_y = self.world_mouse_tu_y * cell_size
        self.screen_mouse_x = self.world_mouse_snapped_x - self.camera.rect.x
        self.screen_mouse_y = self.world_mouse_snapped_y - self.camera.rect.y
        # Combine the first rect with the current cursor position
        second_rect.x = self.world_mouse_snapped_x
        second_rect.y = self.world_mouse_snapped_y
        combined_rect = first_rect.union(second_rect)
        screen_combined_rect_x = combined_rect.x - self.camera.rect.x
        screen_combined_rect_y = combined_rect.y - self.camera.rect.y
        # Draw the combined cursor
        pg.draw.rect(
            NATIVE_SURF,
            "green",
            [
                screen_combined_rect_x,
                screen_combined_rect_y,
                combined_rect.width,
                combined_rect.height,
            ],
            1,
        )
        # TODO: How to create a schema for this when value is Rect?
        return {
            "first_rect": first_rect,
            "second_rect": second_rect,
            "combined_rect": combined_rect,
            "screen_combined_rect_x": screen_combined_rect_x,
            "screen_combined_rect_y": screen_combined_rect_y,
            "room_width": room_width,
            "room_height": room_height,
            "cell_size": cell_size,
            "clamp_rect": clamp_rect,
        }

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
