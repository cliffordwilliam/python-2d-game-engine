from os.path import exists
from typing import Any
from typing import List
from typing import Tuple
from typing import TYPE_CHECKING

from constants import FONT
from constants import FONT_HEIGHT
from constants import NATIVE_HEIGHT
from constants import NATIVE_HEIGHT_TU_EXTRA_ONE
from constants import NATIVE_RECT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import NATIVE_WIDTH_TU
from constants import NATIVE_WIDTH_TU_EXTRA_ONE
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
    Fades in and out to show created by text.
    Player can skip for an early fade out if they input during fade in.

    States:
    - JUST_ENTERED_SCENE.
    - OPENING_SCENE_CURTAIN.
    - SCENE_CURTAIN_OPENED.
    - CLOSING_SCENE_CURTAIN.
    - SCENE_CURTAIN_CLOSED.
    - SPRITE_SHEET_PNG_PATH_QUERY.
    - SPRITE_SIZE_QUERY.
    - ANIMATION_NAME_QUERY.
    - LOOP_QUERY.
    - NEXT_ANIMATION_QUERY.
    - DURATION_QUERY.
    - ADD_FRAMES.

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
    SPRITE_SHEET_PNG_PATH_QUERY: int = 5
    SPRITE_SIZE_QUERY: int = 6
    ANIMATION_NAME_QUERY: int = 7
    LOOP_QUERY: int = 8
    NEXT_ANIMATION_QUERY: int = 9
    DURATION_QUERY: int = 10
    ADD_FRAMES: int = 11

    # REMOVE IN BUILD
    state_names: List = [
        "JUST_ENTERED_SCENE",
        "OPENING_SCENE_CURTAIN",
        "SCENE_CURTAIN_OPENED",
        "CLOSING_SCENE_CURTAIN",
        "SCENE_CURTAIN_CLOSED",
        "SPRITE_SHEET_PNG_PATH_QUERY",
        "SPRITE_SIZE_QUERY",
        "ANIMATION_NAME_QUERY",
        "LOOP_QUERY",
        "NEXT_ANIMATION_QUERY",
        "DURATION_QUERY",
        "ADD_FRAMES",
    ]

    def __init__(self, game: "Game"):
        # - Set scene.
        # - Debug draw.
        # - Events.
        self.game = game

        # Initial state.
        self.initial_state: int = self.JUST_ENTERED_SCENE
        # Null to initial state.
        self.state: int = self.initial_state

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
        self.curtain.add_event_listener(
            self.on_curtain_invisible, Curtain.INVISIBLE_END
        )
        self.curtain.add_event_listener(
            self.on_curtain_opaque, Curtain.OPAQUE_END
        )

        # Timers.
        # Entry delay.
        self.entry_delay_timer_duration: float = 1000
        self.entry_delay_timer: Timer = Timer(self.entry_delay_timer_duration)
        self.entry_delay_timer.add_event_listener(
            self.on_entry_delay_timer_end, Timer.END
        )
        # Exit delay.
        self.exit_delay_timer_duration: float = 1000
        self.exit_delay_timer: Timer = Timer(self.exit_delay_timer_duration)
        self.exit_delay_timer.add_event_listener(
            self.on_exit_delay_timer_end, Timer.END
        )

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
        self.sprite_size: int = TILE_SIZE
        self.sprite_size_tu: int = int(self.sprite_size // TILE_SIZE)
        self.animation_name: str = ""
        self.animation_is_loop: int = 0
        self.next_animation_name: str = ""
        self.animation_duration: int = 0
        # Sprite sheet surf.
        self.sprite_sheet_png_path: str | None = None
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
        self.sprites_list: List = []

        # Selected surf marker.
        self.selected_surf: pg.Surface = pg.Surface((TILE_SIZE, TILE_SIZE))
        self.selected_surf.fill("red")

        # Grid surf.
        self.grid_vertical_line_surf: pg.Surface = pg.Surface(
            (NATIVE_HEIGHT, 1)
        )
        self.grid_vertical_line_surf.fill(self.grid_line_color)
        self.grid_horizontal_line_surf: pg.Surface = pg.Surface(
            (1, NATIVE_HEIGHT)
        )
        self.grid_horizontal_line_surf.fill(self.grid_line_color)

    # Callbacks.
    def on_entry_delay_timer_end(self) -> None:
        self.set_state(self.OPENING_SCENE_CURTAIN)

    def on_exit_delay_timer_end(self) -> None:
        self.game.set_scene("MadeWithSplashScreen")

    def on_curtain_invisible(self) -> None:
        if self.state == self.OPENING_SCENE_CURTAIN:
            self.set_state(self.SCENE_CURTAIN_OPENED)
            return

    def on_curtain_opaque(self) -> None:
        if self.state == self.SCENE_CURTAIN_OPENED:
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
            self.set_state(self.ADD_FRAMES)
            self.curtain.go_to_invisible()
            return

        # TODO: Set condition to go to opaque.
        # self.set_state(self.SCENE_CURTAIN_CLOSED)

    # Helpers.
    def draw_grid(self) -> None:
        for i in range(NATIVE_WIDTH_TU):
            offset: int = TILE_SIZE * i
            vertical_line_x_position: float = (
                offset - self.camera.rect.x
            ) % NATIVE_WIDTH
            horizontal_line_y_position: float = (
                offset - self.camera.rect.y
            ) % NATIVE_HEIGHT
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
        if (
            0 <= world_tu_x < self.room_collision_map_width_tu
            and 0 <= world_tu_y < self.room_collision_map_height_tu
        ):
            return self.room_collision_map_list[
                world_tu_y * self.room_collision_map_width_tu + world_tu_x
            ]
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
        if (
            0 <= world_tu_x < self.room_collision_map_width_tu
            and 0 <= world_tu_y < self.room_collision_map_height_tu
        ):
            self.room_collision_map_list[
                world_tu_y * self.room_collision_map_width_tu + world_tu_x
            ] = value
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
            0
            for _ in range(
                self.room_collision_map_width_tu
                * self.room_collision_map_height_tu
            )
        ]

    def set_input_text(self, value: str) -> None:
        self.input_text = value
        self.input_rect = FONT.get_rect(self.input_text)
        self.input_rect.center = NATIVE_RECT.center

    def set_prompt_text(self, value: str) -> None:
        self.prompt_text = (
            f"{value} "
            f"hit {pg.key.name(self.game.local_settings_dict['enter'])} "
            "to proceed"
        )
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
            self.SCENE_CURTAIN_OPENED,
            self.SPRITE_SHEET_PNG_PATH_QUERY,
            self.SPRITE_SIZE_QUERY,
            self.ANIMATION_NAME_QUERY,
            self.LOOP_QUERY,
            self.NEXT_ANIMATION_QUERY,
            self.DURATION_QUERY,
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

        elif self.state == self.ADD_FRAMES:
            self.draw_grid()

            # Draw sprite sheet with camera offset.
            NATIVE_SURF.blit(
                self.sprite_sheet_surf,
                (
                    -self.camera.rect.x,
                    -self.camera.rect.y,
                ),
            )

            # Draw occupied tiles.
            for camera_tu_xi in range(NATIVE_WIDTH_TU_EXTRA_ONE):
                for camera_tu_yi in range(NATIVE_HEIGHT_TU_EXTRA_ONE):
                    # Get tl tu.
                    root_camera_tu_x: int = int(
                        self.camera.rect.x // TILE_SIZE
                    )
                    root_camera_tu_y: int = int(
                        self.camera.rect.y // TILE_SIZE
                    )
                    # Get this tu.
                    camera_tu_x: int = root_camera_tu_x + camera_tu_xi
                    camera_tu_y: int = root_camera_tu_y + camera_tu_yi
                    # Get each one in room_collision_map_list.
                    found_camera_tile: int = (
                        self.get_tile_from_room_collision_map_list(
                            camera_tu_x,
                            camera_tu_y,
                        )
                    )
                    # Draw.
                    if found_camera_tile == 1:
                        NATIVE_SURF.blit(
                            self.selected_surf,
                            (
                                (camera_tu_x * TILE_SIZE) - self.camera.rect.x,
                                (camera_tu_y * TILE_SIZE) - self.camera.rect.y,
                            ),
                        )

            # Draw cursor.
            # Get mouse position.
            mouse_position_tuple: Tuple[int, int] = pg.mouse.get_pos()
            mouse_position_x_tuple: int = mouse_position_tuple[0]
            # Set top left to be -y_offset instead of 0.
            mouse_position_y_tuple: int = (
                mouse_position_tuple[1] - self.game.native_y_offset
            )
            # Scale mouse position.
            mouse_position_x_tuple_scaled: int | float = (
                mouse_position_x_tuple
                // self.game.local_settings_dict["resolution_scale"]
            )
            mouse_position_y_tuple_scaled: int | float = (
                mouse_position_y_tuple
                // self.game.local_settings_dict["resolution_scale"]
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
            self.world_mouse_x = (
                mouse_position_x_tuple_scaled + self.camera.rect.x
            )
            self.world_mouse_y = (
                mouse_position_y_tuple_scaled + self.camera.rect.y
            )
            self.world_mouse_tu_x = int(self.world_mouse_x // TILE_SIZE)
            self.world_mouse_tu_y = int(self.world_mouse_y // TILE_SIZE)
            self.world_mouse_snapped_x = int(self.world_mouse_tu_x * TILE_SIZE)
            self.world_mouse_snapped_y = int(self.world_mouse_tu_y * TILE_SIZE)
            self.world_mouse_snapped_x = min(
                self.world_mouse_snapped_x,
                self.sprite_sheet_rect.right - self.sprite_size,
            )
            self.world_mouse_snapped_y = min(
                self.world_mouse_snapped_y,
                self.sprite_sheet_rect.bottom - self.sprite_size,
            )
            self.screen_mouse_x = (
                self.world_mouse_snapped_x - self.camera.rect.x
            )
            self.screen_mouse_y = (
                self.world_mouse_snapped_y - self.camera.rect.y
            )
            pg.draw.rect(
                NATIVE_SURF,
                "green",
                [
                    self.screen_mouse_x,
                    self.screen_mouse_y,
                    self.sprite_size,
                    self.sprite_size,
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
                "text": (
                    f"animation json generator "
                    f"state: {self.state_names[self.state]}"
                ),
            }
        )

        if self.state == self.JUST_ENTERED_SCENE:
            """
            - Counts up entry delay time.
            """

            self.entry_delay_timer.update(dt)

        elif self.state == self.OPENING_SCENE_CURTAIN:
            """
            - Updates curtain alpha.
            """

            self.curtain.update(dt)

        elif self.state == self.SCENE_CURTAIN_OPENED:
            """
            - Get user input for file name.
            - Updates curtain alpha.
            """
            # Wait for curtain to be fully invisible.
            if self.curtain.is_done:
                # Caught 1 key event this frame?
                if self.game.this_frame_event:
                    if self.game.this_frame_event.type == pg.KEYDOWN:
                        # Accept.
                        if self.game.this_frame_event.key == pg.K_RETURN:
                            if self.input_text != "":
                                self.file_name = self.input_text
                                # Close curtain.
                                # Exit to SPRITE_SHEET_PNG_PATH_QUERY.
                                self.curtain.go_to_opaque()
                        # Delete.
                        elif self.game.this_frame_event.key == pg.K_BACKSPACE:
                            new_value = self.input_text[:-1]
                            self.set_input_text(new_value)
                        # Add.
                        else:
                            new_value = (
                                self.input_text
                                + self.game.this_frame_event.unicode
                            )
                            self.set_input_text(new_value)

            # Update curtain.
            self.curtain.update(dt)

        elif self.state == self.SPRITE_SHEET_PNG_PATH_QUERY:
            """
            - Get user input for png path.
            - Updates curtain alpha.
            """
            # Wait for curtain to be fully invisible.
            if self.curtain.is_done:
                # Caught 1 key event this frame?
                if self.game.this_frame_event:
                    if self.game.this_frame_event.type == pg.KEYDOWN:
                        # Accept.
                        if self.game.this_frame_event.key == pg.K_RETURN:
                            if exists(
                                self.input_text
                            ) and self.input_text.endswith(".png"):
                                # Setup the sprite sheet data.
                                self.sprite_sheet_png_path = self.input_text
                                self.sprite_sheet_surf = pg.image.load(
                                    self.sprite_sheet_png_path
                                ).convert_alpha()
                                self.sprite_sheet_rect = (
                                    self.sprite_sheet_surf.get_rect()
                                )
                                # Setup camera limits.
                                self.camera.set_rect_limit(
                                    float(self.sprite_sheet_rect.top),
                                    float(self.sprite_sheet_rect.bottom),
                                    float(self.sprite_sheet_rect.left),
                                    float(self.sprite_sheet_rect.right),
                                )
                                # Init room collision map list.
                                sprite_sheet_width_tu: int = (
                                    self.sprite_sheet_rect.width // TILE_SIZE
                                )
                                sprite_sheet_height_tu: int = (
                                    self.sprite_sheet_rect.height // TILE_SIZE
                                )
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
                        elif self.game.this_frame_event.key == pg.K_BACKSPACE:
                            new_value = self.input_text[:-1]
                            self.set_input_text(new_value)
                        # Add.
                        else:
                            new_value = (
                                self.input_text
                                + self.game.this_frame_event.unicode
                            )
                            self.set_input_text(new_value)

            # Update curtain.
            self.curtain.update(dt)

        elif self.state == self.SPRITE_SIZE_QUERY:
            """
            - Get user input for sprite size.
            - Updates curtain alpha.
            """
            # Wait for curtain to be fully invisible.
            if self.curtain.is_done:
                # Caught 1 key event this frame?
                if self.game.this_frame_event:
                    if self.game.this_frame_event.type == pg.KEYDOWN:
                        # Accept.
                        if self.game.this_frame_event.key == pg.K_RETURN:
                            if self.input_text.isdigit():
                                # Setup the sprite_size.
                                self.sprite_size = max(
                                    int(self.input_text) * TILE_SIZE, 0
                                )
                                self.sprite_size_tu = int(
                                    self.sprite_size // TILE_SIZE
                                )
                                # Exit to ADD_FRAMES.
                                # Close curtain to exit to ADD_FRAMES.
                                self.curtain.go_to_opaque()
                            else:
                                self.set_input_text("type int only please!")
                        # Delete.
                        elif self.game.this_frame_event.key == pg.K_BACKSPACE:
                            new_value = self.input_text[:-1]
                            self.set_input_text(new_value)
                        # Add.
                        else:
                            new_value = (
                                self.input_text
                                + self.game.this_frame_event.unicode
                            )
                            self.set_input_text(new_value)

            # Update curtain.
            self.curtain.update(dt)

        elif self.state == self.ANIMATION_NAME_QUERY:
            """
            - Get user input for sprite size.
            - Updates curtain alpha.
            """
            # Wait for curtain to be fully invisible.
            if self.curtain.is_done:
                # Caught 1 key event this frame?
                if self.game.this_frame_event:
                    if self.game.this_frame_event.type == pg.KEYDOWN:
                        # Accept.
                        if self.game.this_frame_event.key == pg.K_RETURN:
                            # TODO: Trim white space.
                            if self.input_text != "":
                                self.animation_name = self.input_text
                                # Close curtain.
                                # Exit to SPRITE_SHEET_PNG_PATH_QUERY.
                                self.curtain.go_to_opaque()
                        # Delete.
                        elif self.game.this_frame_event.key == pg.K_BACKSPACE:
                            new_value = self.input_text[:-1]
                            self.set_input_text(new_value)
                        # Add.
                        else:
                            new_value = (
                                self.input_text
                                + self.game.this_frame_event.unicode
                            )
                            self.set_input_text(new_value)

            # Update curtain.
            self.curtain.update(dt)

        elif self.state == self.LOOP_QUERY:
            """
            - Get user input for sprite size.
            - Updates curtain alpha.
            """
            # Wait for curtain to be fully invisible.
            if self.curtain.is_done:
                # Caught 1 key event this frame?
                if self.game.this_frame_event:
                    if self.game.this_frame_event.type == pg.KEYDOWN:
                        # Accept.
                        if self.game.this_frame_event.key == pg.K_RETURN:
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
                        elif self.game.this_frame_event.key == pg.K_BACKSPACE:
                            new_value = self.input_text[:-1]
                            self.set_input_text(new_value)
                        # Add.
                        else:
                            new_value = (
                                self.input_text
                                + self.game.this_frame_event.unicode
                            )
                            self.set_input_text(new_value)

            # Update curtain.
            self.curtain.update(dt)

        elif self.state == self.NEXT_ANIMATION_QUERY:
            """
            - Get user input for sprite size.
            - Updates curtain alpha.
            """
            # Wait for curtain to be fully invisible.
            if self.curtain.is_done:
                # Caught 1 key event this frame?
                if self.game.this_frame_event:
                    if self.game.this_frame_event.type == pg.KEYDOWN:
                        # Accept.
                        if self.game.this_frame_event.key == pg.K_RETURN:
                            # TODO: Trim white space.
                            if self.input_text != "":
                                self.animation_name = self.input_text
                                # Close curtain.
                                # Exit to SPRITE_SHEET_PNG_PATH_QUERY.
                                self.curtain.go_to_opaque()
                        # Delete.
                        elif self.game.this_frame_event.key == pg.K_BACKSPACE:
                            new_value = self.input_text[:-1]
                            self.set_input_text(new_value)
                        # Add.
                        else:
                            new_value = (
                                self.input_text
                                + self.game.this_frame_event.unicode
                            )
                            self.set_input_text(new_value)

            # Update curtain.
            self.curtain.update(dt)

        elif self.state == self.DURATION_QUERY:
            """
            - Get user input for sprite size.
            - Updates curtain alpha.
            """
            # Wait for curtain to be fully invisible.
            if self.curtain.is_done:
                # Caught 1 key event this frame?
                if self.game.this_frame_event:
                    if self.game.this_frame_event.type == pg.KEYDOWN:
                        # Accept.
                        if self.game.this_frame_event.key == pg.K_RETURN:
                            if self.input_text.isdigit():
                                # Setup the sprite_size.
                                self.animation_duration = int(self.input_text)
                                # Exit to ADD_FRAMES.
                                # Close curtain to exit to ADD_FRAMES.
                                self.curtain.go_to_opaque()
                            else:
                                self.set_input_text("type int only please!")
                        # Delete.
                        elif self.game.this_frame_event.key == pg.K_BACKSPACE:
                            new_value = self.input_text[:-1]
                            self.set_input_text(new_value)
                        # Add.
                        else:
                            new_value = (
                                self.input_text
                                + self.game.this_frame_event.unicode
                            )
                            self.set_input_text(new_value)

            # Update curtain.
            self.curtain.update(dt)

        elif self.state == self.ADD_FRAMES:
            """
            - Move camera and add frames to be saved.
            - Updates curtain alpha.
            """
            # Wait for curtain to be fully invisible.
            if self.curtain.is_done:
                # Camera movement.
                # Get direction_horizontal.
                direction_horizontal: int = (
                    self.game.is_right_pressed - self.game.is_left_pressed
                )
                # Update camera anchor position with direction and speed.
                self.camera_anchor_vector.x += (
                    direction_horizontal * self.camera_speed * dt
                )
                # Get direction_vertical.
                direction_vertical: int = (
                    self.game.is_down_pressed - self.game.is_up_pressed
                )
                # Update camera anchor position with direction and speed.
                self.camera_anchor_vector.y += (
                    direction_vertical * self.camera_speed * dt
                )
                # Lerp camera position to target camera anchor.
                self.camera.update(dt)

                # Sprite selection.
                # Lmb just pressed.
                if self.game.is_lmb_just_pressed:
                    # Store selected rect.
                    # Iterate size.
                    for world_mouse_tu_xi in range(self.sprite_size_tu):
                        for world_mouse_tu_yi in range(self.sprite_size_tu):
                            world_mouse_tu_x: int = (
                                self.world_mouse_tu_x + world_mouse_tu_xi
                            )
                            world_mouse_tu_y: int = (
                                self.world_mouse_tu_y + world_mouse_tu_yi
                            )
                            # Store each one in room_collision_map_list.
                            self.set_tile_from_room_collision_map_list(
                                world_mouse_tu_x,
                                world_mouse_tu_y,
                                1,
                            )

            # Update curtain.
            self.curtain.update(dt)

        elif self.state == self.CLOSING_SCENE_CURTAIN:
            """
            - Updates curtain alpha.
            """

            self.curtain.update(dt)

        elif self.state == self.SCENE_CURTAIN_CLOSED:
            """
            - Counts up exit delay time.
            """

            self.exit_delay_timer.update(dt)

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
            # To SCENE_CURTAIN_OPENED.
            if self.state == self.SCENE_CURTAIN_OPENED:
                # Reset the input text.
                self.set_input_text("")
                # Set my prompt text:
                self.set_prompt_text("type the file name to be saved,")

        # From SCENE_CURTAIN_OPENED.
        elif old_state == self.SCENE_CURTAIN_OPENED:
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
                self.set_prompt_text(
                    "type the sprite size in tile units to be used,"
                )

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
                self.set_prompt_text(
                    "type the next animation name (optional),"
                )

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
            # To ADD_FRAMES.
            if self.state == self.ADD_FRAMES:
                pass

        # From CLOSING_SCENE_CURTAIN.
        elif old_state == self.CLOSING_SCENE_CURTAIN:
            # To SCENE_CURTAIN_CLOSED.
            if self.state == self.SCENE_CURTAIN_CLOSED:
                NATIVE_SURF.fill("black")
