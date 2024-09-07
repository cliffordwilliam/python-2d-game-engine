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
    TODO: write doc for this actor
    """

    def __init__(
        self,
        # Offset draw
        camera: "Camera",
        # Listen to input
        game_event_handler: "EventHandler",
        # Room metadata
        solid_collision_map_list: list,
        room_width_tu: int,
        room_height_tu: int,
        # REMOVE IN BUILD
        # For debug draw
        game_debug_draw: "DebugDraw",
    ):
        # REMOVE IN BUILD
        self.game_debug_draw = game_debug_draw

        # Init room metadata
        self.solid_collision_map_list = solid_collision_map_list
        self.room_width_tu: int = room_width_tu
        self.room_height_tu: int = room_height_tu

        # Initialize game
        self.game_event_handler = game_event_handler

        # To offset draw
        self.camera: "Camera" = camera

        # My rect and surf
        self.surf: pg.Surface = pg.Surface((6, 31))
        self.surf.fill("red")
        self.collider_rect: pg.FRect = self.surf.get_frect()

        # Movement
        self.max_run: float = 0.09  # Px / ms
        self.run_acceleration: float = 0.000533  # Px / ms2
        self.velocity: pg.Vector2 = pg.Vector2(0.0, 0.0)
        self.decay: float = 0.01

        # My camera anchor
        self.camera_anchor_vector: Vector2 = Vector2(0.0, 0.0)

        # My kinematic
        self.kinematic = Kinematic(
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
        Call when room collision map list updates
        """

        self.solid_collision_map_list = value
        self.kinematic.set_solid_collision_map_list(value)

    def set_room_width_tu(self, value: int) -> None:
        """
        Call when room collision map list updates
        """

        self.room_width_tu = value
        self.kinematic.set_room_width_tu(value)

    def set_room_height_tu(self, value: int) -> None:
        """
        Call when room collision map list updates
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
        # TODO: State machine mutates direction input and velocity here

        # RESOLVE NEW VEL
        self.velocity = self.kinematic.resolve_vel_against_solid_tiles(dt, self.velocity)

        # Update collider rect pos with RESOLVE VEL
        self.collider_rect.x += self.velocity.x * dt
        self.camera_anchor_vector.x = self.collider_rect.centerx
        self.collider_rect.y += self.velocity.y * dt
        # Clamp my collider rect pos to be in camera rect
        self.collider_rect.clamp_ip(self.camera.rect)
        # Move camera anchor to my collider rect pos
        self.camera_anchor_vector.y = self.collider_rect.centery
