from typing import TYPE_CHECKING

from constants import pg
from constants import TILE_SIZE
from schemas import NoneOrBlobSpriteMetadata
from typeguard import typechecked
from utils import dynamic_rect_vs_rect
from utils import get_tile_from_collision_map_list

if TYPE_CHECKING:
    # REMOVE IN BUILD
    from nodes.debug_draw import DebugDraw
    from nodes.camera import Camera


@typechecked
class Kinematic:
    def __init__(
        self,
        # Actor metadata
        collider_rect: pg.FRect,
        # Room metadata
        solid_collision_map_list: list[int | NoneOrBlobSpriteMetadata],
        room_width_tu: int,
        room_height_tu: int,
        # REMOVE IN BUILD
        # For debug draw
        game_debug_draw: "DebugDraw",
        camera: "Camera",
    ):
        """
        Responsible solving dynamic actors to solid tiles collisions.
        Needs solid actor collider.
        Needs velocity input.
        Uses input velocity to get future position.
        Resolve velocity with collision, and returns new velocity.
        New vel prevents overlap in next frame.
        Use new returned vel to update position, position should not overlap next frame.
        """

        # TODO: is on floor flag, collided cell name prop

        # REMOVE IN BUILD
        self.camera: "Camera" = camera
        self.game_debug_draw = game_debug_draw

        # Init room metadata
        # TODO: Make the solid collision map list be safe
        self.solid_collision_map_list: list[int | NoneOrBlobSpriteMetadata] = solid_collision_map_list
        self.room_width_tu: int = room_width_tu
        self.room_height_tu: int = room_height_tu

        # Init collider rect
        self.collider_rect: pg.FRect = collider_rect

        # One tile frect for collision testing SOLID TILES ARE ALWAYS 1 TILE SIZE
        self.one_tile_rect: pg.FRect = pg.FRect(0, 0, TILE_SIZE, TILE_SIZE)

    #################
    # SETTER GETTER #
    #################
    def set_solid_collision_map_list(self, value: list[int | NoneOrBlobSpriteMetadata]) -> None:
        """
        Call when room collision map list updates.
        """

        self.solid_collision_map_list = value

    def set_room_width_tu(self, value: int) -> None:
        """
        Call when room collision map list updates.
        """

        self.room_width_tu = value

    def set_room_height_tu(self, value: int) -> None:
        """
        Call when room collision map list updates.
        """

        self.room_height_tu = value

    def determine_movement_direction(self, velocity_vector: pg.Vector2) -> tuple[int, int]:
        # Extract x and y components from the Pygame vector
        x, y = velocity_vector.x, velocity_vector.y

        # Determine the direction based on the sign of x and y
        direction_x: int = 0
        direction_y: int = 0

        if abs(x) > 0.01:
            direction_x = (x > 0) - (x < 0)  # 1 for right, -1 for left, 0 for none

        if abs(y) > 0.01:
            direction_y = (y > 0) - (y < 0)  # 1 for down, -1 for up, 0 for none

        return (direction_x, direction_y)

    #############
    # ABILITIES #
    #############
    def resolve_vel_against_solid_tiles(self, dt: int, velocity: pg.Vector2) -> pg.Vector2:
        """
        Return resolved velocity against solid tiles.
        """

        input_velocity: pg.Vector2 = velocity
        resolved_velocity: pg.Vector2 = velocity

        # Compute my future rect position with vel
        distance_to_be_covered_vector: pg.Vector2 = input_velocity * dt
        future_rect_x = self.collider_rect.x + distance_to_be_covered_vector.x
        future_rect_y = self.collider_rect.y + distance_to_be_covered_vector.y

        # Compute present future combined rect pos and size
        present_future_combined_rect = self.collider_rect.union(
            [
                future_rect_x,
                future_rect_y,
                self.collider_rect.width,
                self.collider_rect.height,
            ]
        )

        # Get all 4 points of present_future_combined_rect
        left_point = present_future_combined_rect.left
        top_point = present_future_combined_rect.top
        right_point = left_point + present_future_combined_rect.width
        bottom_point = top_point + present_future_combined_rect.height

        # Truncate the points
        l_tu = int(left_point // TILE_SIZE)
        t_tu = int(top_point // TILE_SIZE)
        r_tu = int(right_point // TILE_SIZE)
        b_tu = int(bottom_point // TILE_SIZE)

        # Collect solid tiles in present_future_combined_rect
        combined_rect_width_ru = r_tu - l_tu + 1
        combined_rect_height_ru = b_tu - t_tu + 1
        combined_rect_x_ru = l_tu
        combined_rect_y_ru = t_tu

        # Get direction
        direction_x, direction_y = self.determine_movement_direction(input_velocity)

        # Determine x and y iteration ranges based on the direction
        if direction_x == 1:  # Moving right or no horizontal movement
            x_range = range(combined_rect_x_ru, combined_rect_x_ru + combined_rect_width_ru)
        elif direction_x == -1:  # Moving left
            x_range = range(combined_rect_x_ru + combined_rect_width_ru - 1, combined_rect_x_ru - 1, -1)
        else:
            x_range = range(combined_rect_x_ru, combined_rect_x_ru + combined_rect_width_ru)

        if direction_y == 1:  # Moving down or no vertical movement
            y_range = range(combined_rect_y_ru, combined_rect_y_ru + combined_rect_height_ru)
        elif direction_y == -1:  # Moving up
            y_range = range(combined_rect_y_ru + combined_rect_height_ru - 1, combined_rect_y_ru - 1, -1)
        else:
            y_range = range(combined_rect_y_ru, combined_rect_y_ru + combined_rect_height_ru)

        # Iterate region candidate
        for world_tu_x in x_range:
            for world_tu_y in y_range:
                # Get each one in solid_collision_map_list
                cell = get_tile_from_collision_map_list(
                    world_tu_x,
                    world_tu_y,
                    self.room_width_tu,
                    self.room_height_tu,
                    self.solid_collision_map_list,
                )
                # Ignore air, if it is not 0, its NoneOrBlobSpriteMetadata
                if cell == 0 or cell == -1:
                    continue

                # Make sure value is a NoneOrBlobSpriteMetadata
                if not isinstance(cell, NoneOrBlobSpriteMetadata):
                    raise ValueError("foreground_collision_map_list can only hold int or NoneOrBlobSpriteMetadata")

                self.one_tile_rect.x = cell.x
                self.one_tile_rect.y = cell.y
                # Collision query with test rect
                contact_point = [pg.Vector2(0, 0)]
                contact_normal = [pg.Vector2(0, 0)]
                t_hit_near = [0.0]
                # This one is passed the correct sorted, so returns correct data like t hit near
                hit = dynamic_rect_vs_rect(
                    input_velocity,
                    self.collider_rect,
                    self.one_tile_rect,
                    contact_point,
                    contact_normal,
                    t_hit_near,
                    dt,
                )
                if hit:
                    # RESOLVE VEL
                    resolved_velocity.x += contact_normal[0].x * abs(input_velocity.x) * (1 - t_hit_near[0])
                    resolved_velocity.y += contact_normal[0].y * abs(input_velocity.y) * (1 - t_hit_near[0])

                # REMOVE IN BUILD
                # Debug draw
                if self.game_debug_draw.is_active:
                    # Prepare offset to correct expanded rect collision
                    offset_x: float = 0.0
                    offset_y: float = 0.0
                    collider_rect_half_width: float = self.collider_rect.width / 2
                    collider_rect_half_height: float = self.collider_rect.height / 2
                    if contact_normal[0] == (1, 0):
                        offset_x = -collider_rect_half_width
                    elif contact_normal[0] == (-1, 0):
                        offset_x = collider_rect_half_width
                    elif contact_normal[0] == (0, 1):
                        offset_y = -collider_rect_half_height
                    elif contact_normal[0] == (0, -1):
                        offset_y = collider_rect_half_height
                    # Draw the test rect green
                    self.game_debug_draw.add(
                        {
                            "type": "rect",
                            "layer": 4,
                            "rect": [
                                self.one_tile_rect.x - self.camera.rect.x,
                                self.one_tile_rect.y - self.camera.rect.y,
                                self.one_tile_rect.width,
                                self.one_tile_rect.height,
                            ],
                            "color": "green",
                            "width": 0,
                        }
                    )
                    # Draw contact point
                    self.game_debug_draw.add(
                        {
                            "type": "circle",
                            "layer": 4,
                            "color": "blue",
                            "center": (
                                contact_point[0].x - self.camera.rect.x + offset_x,
                                contact_point[0].y - self.camera.rect.y + offset_y,
                            ),
                            "radius": 3,
                        }
                    )
                    # Draw normal
                    self.game_debug_draw.add(
                        {
                            "type": "line",
                            "layer": 4,
                            "start": (
                                contact_point[0].x - self.camera.rect.x + offset_x,
                                contact_point[0].y - self.camera.rect.y + offset_y,
                            ),
                            "end": (
                                contact_point[0].x + contact_normal[0].x * 16 - self.camera.rect.x + offset_x,
                                contact_point[0].y + contact_normal[0].y * 16 - self.camera.rect.y + offset_y,
                            ),
                            "color": "yellow",
                            "width": 1,
                        }
                    )
                    # Draw tile type
                    self.game_debug_draw.add(
                        {
                            "type": "text",
                            "layer": 4,
                            "x": self.one_tile_rect.x - self.camera.rect.x,
                            "y": self.one_tile_rect.y - self.camera.rect.y,
                            "text": (f"type: {cell.type}"),
                        }
                    )

        # REMOVE IN BUILD
        # Debug draw
        # Draw resolved velocity vector
        if self.game_debug_draw.is_active:
            collider_rect_center_world_x = self.collider_rect.centerx - self.camera.rect.x
            collider_rect_center_world_y = self.collider_rect.centery - self.camera.rect.y
            self.game_debug_draw.add(
                {
                    "type": "line",
                    "layer": 4,
                    "start": (
                        collider_rect_center_world_x,
                        collider_rect_center_world_y,
                    ),
                    "end": (
                        collider_rect_center_world_x + resolved_velocity.x * 200,
                        collider_rect_center_world_y + resolved_velocity.y * 200,
                    ),
                    "color": "blue",
                    "width": 1,
                }
            )

        # Return the resolved vel
        return resolved_velocity
