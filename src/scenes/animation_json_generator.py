from os.path import exists
from typing import Any
from typing import List
from typing import Tuple
from typing import TYPE_CHECKING

from constants import FONT
from constants import FONT_HEIGHT
from constants import NATIVE_HEIGHT
from constants import NATIVE_RECT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import NATIVE_WIDTH_TU
from constants import pg
from constants import TILE_HEIGHT
from constants import TILE_WIDTH
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
    - JUST_ENTERED.
    - GOING_TO_INVISIBLE.
    - REACHED_INVISIBLE.
    - GOING_TO_OPAQUE.
    - REACHED_OPAQUE.
    - FILE_PATH_QUERY.
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

    JUST_ENTERED: int = 0
    GOING_TO_INVISIBLE: int = 1
    REACHED_INVISIBLE: int = 2
    GOING_TO_OPAQUE: int = 3
    REACHED_OPAQUE: int = 4
    FILE_PATH_QUERY: int = 5
    ADD_FRAMES: int = 6

    # REMOVE IN BUILD
    state_names: List = [
        "JUST_ENTERED",
        "GOING_TO_INVISIBLE",
        "REACHED_INVISIBLE",
        "GOING_TO_OPAQUE",
        "REACHED_OPAQUE",
        "FILE_PATH_QUERY",
        "ADD_FRAMES",
    ]

    def __init__(self, game: "Game"):
        # - Set scene.
        # - Debug draw.
        # - Events.
        self.game = game

        # Initial state.
        self.initial_state: int = self.JUST_ENTERED
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
        # File name prompt.
        self.file_name_text_prompt: str = (
            "type the file name to be saved, "
            f"hit {pg.key.name(self.game.local_settings_dict['enter'])} "
            "to proceed"
        )

        self.file_name_prompt_rect: pg.Rect = FONT.get_rect(
            self.file_name_text_prompt
        )
        self.file_name_prompt_rect.center = NATIVE_RECT.center
        self.file_name_prompt_rect.y -= FONT_HEIGHT + 1
        # File name.
        self.file_name_text: str = ""
        self.file_name_rect: pg.Rect = FONT.get_rect(self.file_name_text)
        self.file_name_rect.center = NATIVE_RECT.center
        # Png path prompt.
        self.png_path_text_prompt: str = (
            "type the png path to be used, "
            f"hit {pg.key.name(self.game.local_settings_dict['enter'])} "
            "to proceed"
        )

        self.png_path_prompt_rect: pg.Rect = FONT.get_rect(
            self.png_path_text_prompt
        )
        self.png_path_prompt_rect.center = NATIVE_RECT.center
        self.png_path_prompt_rect.y -= FONT_HEIGHT + 1
        # Png path.
        self.png_path_text: str = ""
        self.png_path_rect: pg.Rect = FONT.get_rect(self.png_path_text)
        self.png_path_rect.center = NATIVE_RECT.center

        # Sprite sheet.
        self.sprite_sheet_path: str | None = None
        self.sprite_sheet_surface: Any = None
        self.sprite_sheet_rect: pg.Rect | None = None

        # Camera.
        self.camera_anchor_vector: Vector2 = Vector2(0.0, 0.0)
        self.camera: Camera = Camera(
            self.camera_anchor_vector,
            # REMOVE IN BUILD.
            self.game,
        )
        # Px / ms
        self.camera_speed: float = 0.09

    # Callbacks.
    def on_entry_delay_timer_end(self) -> None:
        self.set_state(self.GOING_TO_INVISIBLE)

    def on_exit_delay_timer_end(self) -> None:
        self.game.set_scene("MadeWithSplashScreen")

    def on_curtain_invisible(self) -> None:
        self.set_state(self.REACHED_INVISIBLE)

    def on_curtain_opaque(self) -> None:
        self.set_state(self.REACHED_OPAQUE)

    def draw(self) -> None:
        """
        - clear NATIVE_SURF.
        - file_text.
        - tips_text.
        - curtain.
        """

        NATIVE_SURF.fill(self.native_clear_color)

        if self.state == self.REACHED_INVISIBLE:
            FONT.render_to(
                NATIVE_SURF,
                self.file_name_prompt_rect,
                self.file_name_text_prompt,
                self.font_color,
            )
            FONT.render_to(
                NATIVE_SURF,
                self.file_name_rect,
                self.file_name_text,
                self.font_color,
            )

        elif self.state == self.FILE_PATH_QUERY:
            FONT.render_to(
                NATIVE_SURF,
                self.png_path_prompt_rect,
                self.png_path_text_prompt,
                self.font_color,
            )
            FONT.render_to(
                NATIVE_SURF,
                self.png_path_rect,
                self.png_path_text,
                self.font_color,
            )

        elif self.state == self.ADD_FRAMES:
            # Draw grid with camera offset.
            for i in range(NATIVE_WIDTH_TU):
                offset: int = TILE_HEIGHT * i
                gxd: float = (offset - self.camera.rect.x) % NATIVE_WIDTH
                gyd: float = (offset - self.camera.rect.y) % NATIVE_HEIGHT
                pg.draw.line(
                    NATIVE_SURF,
                    self.grid_line_color,
                    (gxd, 0),
                    (gxd, NATIVE_HEIGHT),
                )
                pg.draw.line(
                    NATIVE_SURF,
                    self.grid_line_color,
                    (0, gyd),
                    (NATIVE_WIDTH, gyd),
                )

            # Draw sprite sheet with camera offset.
            NATIVE_SURF.blit(
                self.sprite_sheet_surface,
                (
                    -self.camera.rect.x,
                    -self.camera.rect.y,
                ),
            )

            # Draw cursor.
            mouse_position_tuple: Tuple[int, int] = pg.mouse.get_pos()

            mouse_position_x_tuple: int = mouse_position_tuple[0]
            # Set top left to be -y_offset instead of 0.
            mouse_position_y_tuple: int = (
                mouse_position_tuple[1] - self.game.native_y_offset
            )

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

            # TODO: Rename it better.
            xd: float = mouse_position_x_tuple_scaled + self.camera.rect.x
            yd: float = mouse_position_y_tuple_scaled + self.camera.rect.y
            xd_tu: float = xd // TILE_WIDTH
            yd_tu: float = yd // TILE_HEIGHT
            xds: float = xd_tu * TILE_WIDTH
            yds: float = yd_tu * TILE_HEIGHT
            xs: float = xds - self.camera.rect.x
            ys: float = yds - self.camera.rect.y
            pg.draw.rect(
                NATIVE_SURF, "green", [xs, ys, TILE_WIDTH, TILE_HEIGHT], 1
            )

        self.curtain.draw(NATIVE_SURF, 0)

    def set_png_path_text(self, value: str) -> None:
        self.png_path_text = value
        self.png_path_rect = FONT.get_rect(self.png_path_text)
        self.png_path_rect.center = NATIVE_RECT.center

    def set_file_name_text(self, value: str) -> None:
        self.file_name_text = value
        self.file_name_rect = FONT.get_rect(self.file_name_text)
        self.file_name_rect.center = NATIVE_RECT.center

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
                    f"animation json generator state"
                    f"state: {self.state_names[self.state]}"
                ),
            }
        )

        if self.state == self.JUST_ENTERED:
            """
            - Counts up entry delay time.
            """

            self.entry_delay_timer.update(dt)

        elif self.state == self.GOING_TO_INVISIBLE:
            """
            - Updates curtain alpha.
            """

            self.curtain.update(dt)

        elif self.state == self.REACHED_INVISIBLE:
            """
            - Get user input for file name.
            """
            if self.game.this_frame_event:
                if self.game.this_frame_event.type == pg.KEYDOWN:
                    if self.game.this_frame_event.key == pg.K_RETURN:
                        self.set_state(self.FILE_PATH_QUERY)
                    elif self.game.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.file_name_text[:-1]
                        self.set_file_name_text(new_value)
                    else:
                        new_value = (
                            self.file_name_text
                            + self.game.this_frame_event.unicode
                        )
                        self.set_file_name_text(new_value)

        elif self.state == self.FILE_PATH_QUERY:
            """
            - Get user input for png path.
            """
            if self.game.this_frame_event:
                if self.game.this_frame_event.type == pg.KEYDOWN:
                    if self.game.this_frame_event.key == pg.K_RETURN:
                        if exists(
                            self.png_path_text
                        ) and self.png_path_text.endswith(".png"):
                            # Setup the sprite sheet data.
                            self.sprite_sheet_path = self.png_path_text
                            self.sprite_sheet_surface = pg.image.load(
                                self.sprite_sheet_path
                            ).convert_alpha()
                            self.sprite_sheet_rect = (
                                self.sprite_sheet_surface.get_rect()
                            )
                            # Setup camera limits.
                            self.camera.set_rect_limit(
                                float(self.sprite_sheet_rect.top),
                                float(self.sprite_sheet_rect.bottom),
                                float(self.sprite_sheet_rect.left),
                                float(self.sprite_sheet_rect.right),
                            )
                            # Exit to ADD_FRAMES.
                            self.set_state(self.ADD_FRAMES)
                        else:
                            self.set_png_path_text("png path does not exist!")
                    elif self.game.this_frame_event.key == pg.K_BACKSPACE:
                        new_value = self.png_path_text[:-1]
                        self.set_png_path_text(new_value)
                    else:
                        new_value = (
                            self.png_path_text
                            + self.game.this_frame_event.unicode
                        )
                        self.set_png_path_text(new_value)

        elif self.state == self.ADD_FRAMES:
            """
            - Move camera and add frames to be saved.
            """
            # Camera movement.
            # Get direction_horizontal.
            direction_horizontal: int = (
                self.game.is_right_pressed - self.game.is_left_pressed
            )
            # Update camera anchor with direction and speed.
            self.camera_anchor_vector.x += (
                direction_horizontal * self.camera_speed * dt
            )
            # Get direction_vertical.
            direction_vertical: int = (
                self.game.is_down_pressed - self.game.is_up_pressed
            )
            # Update camera anchor with direction and speed.
            self.camera_anchor_vector.y += (
                direction_vertical * self.camera_speed * dt
            )
            # Lerp camera to target.
            self.camera.update(dt)

        elif self.state == self.GOING_TO_OPAQUE:
            """
            - Updates curtain alpha.
            """

            self.curtain.update(dt)

        elif self.state == self.REACHED_OPAQUE:
            """
            - Counts up exit delay time.
            """

            self.exit_delay_timer.update(dt)

    def set_state(self, value: int) -> None:
        old_state: int = self.state
        self.state = value

        # From JUST_ENTERED.
        if old_state == self.JUST_ENTERED:
            # To GOING_TO_INVISIBLE.
            if self.state == self.GOING_TO_INVISIBLE:
                self.curtain.go_to_invisible()

        # From GOING_TO_INVISIBLE.
        elif old_state == self.GOING_TO_INVISIBLE:
            # To REACHED_INVISIBLE.
            if self.state == self.REACHED_INVISIBLE:
                pass

        # From REACHED_INVISIBLE.
        elif old_state == self.REACHED_INVISIBLE:
            # To GOING_TO_OPAQUE.
            if self.state == self.GOING_TO_OPAQUE:
                self.curtain.go_to_opaque()
            # To FILE_PATH_QUERY.
            elif self.state == self.FILE_PATH_QUERY:
                pass

        # From FILE_PATH_QUERY.
        elif old_state == self.FILE_PATH_QUERY:
            # To ADD_FRAMES.
            if self.state == self.ADD_FRAMES:
                pass

        # From GOING_TO_OPAQUE.
        elif old_state == self.GOING_TO_OPAQUE:
            # To REACHED_OPAQUE.
            if self.state == self.REACHED_OPAQUE:
                NATIVE_SURF.fill("black")
