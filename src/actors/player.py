from typing import TYPE_CHECKING

from constants import NATIVE_SURF
from constants import pg
from nodes.kinematic import Kinematic
from pygame.math import Vector2
from typeguard import typechecked
from utils import exp_decay

if TYPE_CHECKING:
    from nodes.camera import Camera
    from nodes.event_handler import EventHandler

    # REMOVE IN BUILD
    from nodes.debug_draw import DebugDraw


@typechecked
class Player:
    """
    Listens to input events.
    Mainly for updating its position in the world.
    Has the ability to spawn other actors (like bullets)
    """

    def __init__(
        self,
        # Offset draw
        camera: "Camera",
        # Listen to input
        game_event_handler: "EventHandler",
        # Room metadata for collision
        solid_collision_map_list: list,
        room_width_tu: int,
        room_height_tu: int,
        # REMOVE IN BUILD
        # For debug draw
        game_debug_draw: "DebugDraw",
    ):
        # Initialize game dependencies
        self.game_event_handler: "EventHandler" = game_event_handler
        # REMOVE IN BUILD
        self.game_debug_draw: "DebugDraw" = game_debug_draw

        # Initialize room metadata
        self.solid_collision_map_list: list = solid_collision_map_list
        self.room_width_tu: int = room_width_tu
        self.room_height_tu: int = room_height_tu

        # To offset draw
        self.camera: "Camera" = camera

        self._setup_rects_and_surfs()
        self._setup_movement_metadata()
        self._setup_camera_anchor()
        self._setup_kinematic()

    ##########
    # SETUPS #
    ##########
    def _setup_rects_and_surfs(self) -> None:
        """
        Setup rects and surfs.
        """

        self.surf: pg.Surface = pg.Surface((6, 31))
        self.surf.fill("red")
        self.collider_rect: pg.FRect = self.surf.get_frect()

    def _setup_movement_metadata(self) -> None:
        """
        Setup my movement magic numbers.
        """

        self.max_run: float = 0.09  # Px / ms
        self.run_acceleration: float = 0.000533  # Px / ms2
        self.velocity: pg.Vector2 = pg.Vector2(0.0, 0.0)
        self.decay: float = 0.01

    def _setup_camera_anchor(self) -> None:
        """
        Setup my camera anchor vector.
        """

        self.camera_anchor_vector: Vector2 = Vector2(0.0, 0.0)

    def _setup_kinematic(self) -> None:
        """
        Setup kinematic.
        """

        self.kinematic: Kinematic = Kinematic(
            self.collider_rect,
            self.solid_collision_map_list,
            self.room_width_tu,
            self.room_height_tu,
            self.game_debug_draw,
            self.camera,
        )

    #################
    # SETTER GETTER #
    #################
    def set_solid_collision_map_list(self, value: list) -> None:
        """
        Call when room collision map list updates.
        Content changes.
        """

        self.solid_collision_map_list = value
        self.kinematic.set_solid_collision_map_list(value)

    def set_room_width_tu(self, value: int) -> None:
        """
        Call when room collision map list updates.
        Width changes.
        """

        self.room_width_tu = value
        self.kinematic.set_room_width_tu(value)

    def set_room_height_tu(self, value: int) -> None:
        """
        Call when room collision map list updates.
        Height changes.
        """

        self.room_height_tu = value
        self.kinematic.set_room_height_tu(value)

    ########
    # DRAW #
    ########
    def draw(self) -> None:
        NATIVE_SURF.blit(
            self.surf,
            (
                self.collider_rect.x - self.camera.rect.x,
                self.collider_rect.y - self.camera.rect.y,
            ),
        )

    ##########
    # UPDATE #
    ##########
    def update(self, dt: int) -> None:
        # Get dir input
        direction_horizontal: int = self.game_event_handler.is_right_pressed - self.game_event_handler.is_left_pressed
        direction_vertical: int = self.game_event_handler.is_down_pressed - self.game_event_handler.is_up_pressed

        # Update vel with input
        self.velocity.x = exp_decay(self.velocity.x, direction_horizontal * self.max_run, self.decay, dt)
        self.velocity.y = exp_decay(self.velocity.y, direction_vertical * self.max_run, self.decay, dt)

        # TODO: STATE MACHINE HERE
        # TODO: State machine mutates direction input and velocity here (when crouching dir x set to 0)

        # RESOLVE NEW VEL (like godot move and slide)
        self.velocity = self.kinematic.resolve_vel_against_solid_tiles(dt, self.velocity)

        # Update collider rect pos with RESOLVE VEL
        self.collider_rect.x += self.velocity.x * dt
        self.camera_anchor_vector.x = self.collider_rect.centerx
        self.collider_rect.y += self.velocity.y * dt
        # Clamp my collider rect pos to be in camera rect
        self.collider_rect.clamp_ip(self.camera.rect)
        # Move my camera anchor to my collider rect pos center
        self.camera_anchor_vector.y = self.collider_rect.centery
