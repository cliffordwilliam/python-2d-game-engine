from typing import TYPE_CHECKING

from constants import NATIVE_SURF
from constants import pg
from pygame.math import Vector2
from typeguard import typechecked
from utils import dynamic_rect_vs_rect
from utils import exp_decay

if TYPE_CHECKING:
    from nodes.camera import Camera
    from nodes.event_handler import EventHandler


@typechecked
class Player:
    """
    TODO: write doc for this actor
    """

    def __init__(
        self,
        camera: "Camera",
        game_event_handler: "EventHandler",
    ):
        # Initialize game
        self.game_event_handler = game_event_handler

        # To offset draw
        self.camera: "Camera" = camera

        # My rect and surf
        self.rect: pg.FRect = pg.FRect(0, 0, 6, 31)
        self.surf: pg.Surface = pg.Surface((6, 31))
        self.surf.fill("red")

        # Movement
        self.max_run: float = 0.09  # Px / ms
        self.run_acceleration: float = 0.000533  # Px / ms2
        self.velocity: pg.Vector2 = pg.Vector2(0.0, 0.0)
        self.decay: float = 0.01

        # My camera anchor
        self.camera_anchor_vector: Vector2 = Vector2(0.0, 0.0)

        # Pretend this a tile from collision map list
        self.collision_map_list_test: list[pg.FRect] = [
            # TODO: Bug when check from op order
            # TODO: Need to SORT PROXIMITY from actor
            # TODO: So sort based on t_hit_near
            pg.FRect(176, 176, 32, 32),  # 1 TL
            pg.FRect(208, 176, 32, 32),  # 2 TR
            pg.FRect(208, 208, 32, 32),  # 3 BR
            pg.FRect(176, 208, 32, 32),  # 4 BL
        ]

    def draw(self) -> None:
        NATIVE_SURF.blit(
            self.surf,
            (
                self.rect.x - self.camera.rect.x,
                self.rect.y - self.camera.rect.y,
            ),
        )

    def update(self, dt: int) -> None:
        # Get dir x
        direction_horizontal: int = self.game_event_handler.is_right_pressed - self.game_event_handler.is_left_pressed
        # Get dir y
        direction_vertical: int = self.game_event_handler.is_down_pressed - self.game_event_handler.is_up_pressed
        # Update vel x
        self.velocity.x = exp_decay(self.velocity.x, direction_horizontal * self.max_run, self.decay, dt)
        # Update vel y
        self.velocity.y = exp_decay(self.velocity.y, direction_vertical * self.max_run, self.decay, dt)

        z: list[tuple[int, list[float]]] = []

        # Handle each rects
        for i in range(len(self.collision_map_list_test)):
            rect = self.collision_map_list_test[i]
            # Collision query with test rect
            contact_point = [pg.Vector2(0, 0)]
            contact_normal = [pg.Vector2(0, 0)]
            t_hit_near = [0.0]
            hit = dynamic_rect_vs_rect(
                self,
                rect,
                contact_point,
                contact_normal,
                t_hit_near,
                dt,
            )
            # Hit?
            if hit:
                # Collect
                z.append((i, t_hit_near))
                # Draw the test rect green
                pg.draw.rect(
                    NATIVE_SURF,
                    "green",
                    (
                        rect.x - self.camera.rect.x,
                        rect.y - self.camera.rect.y,
                        rect.width,
                        rect.height,
                    ),
                    1,
                )
                # # Draw contact point
                # pg.draw.circle(
                #     NATIVE_SURF,
                #     "blue",
                #     (
                #         contact_point[0].x - self.camera.rect.x,
                #         contact_point[0].y - self.camera.rect.y,
                #     ),
                #     3,
                # )
                # # Draw normal
                # pg.draw.line(
                #     NATIVE_SURF,
                #     "yellow",
                #     (
                #         contact_point[0].x - self.camera.rect.x,
                #         contact_point[0].y - self.camera.rect.y,
                #     ),
                #     (
                #         contact_point[0].x + contact_normal[0].x * 16 - self.camera.rect.x,
                #         contact_point[0].y + contact_normal[0].y * 16 - self.camera.rect.y,
                #     ),
                # )
            # No hit?
            else:
                # Draw the test rect green
                pg.draw.rect(
                    NATIVE_SURF,
                    "red",
                    (
                        rect.x - self.camera.rect.x,
                        rect.y - self.camera.rect.y,
                        rect.width,
                        rect.height,
                    ),
                    1,
                )

        # Sort it
        z.sort(key=lambda x: x[1][0])

        # Do the real iter
        for j in range(len(z)):
            index = z[j][0]
            rect = self.collision_map_list_test[index]
            # Collision query with test rect
            contact_point = [pg.Vector2(0, 0)]
            contact_normal = [pg.Vector2(0, 0)]
            t_hit_near = [0.0]
            hit = dynamic_rect_vs_rect(
                self,
                rect,
                contact_point,
                contact_normal,
                t_hit_near,
                dt,
            )
            # Hit?
            if hit:
                # Resolve velocity
                self.velocity.x += contact_normal[0].x * abs(self.velocity.x) * (1 - t_hit_near[0])
                self.velocity.y += contact_normal[0].y * abs(self.velocity.y) * (1 - t_hit_near[0])

        # Vel is correct here
        # Update pos x
        self.rect.x += self.velocity.x * dt
        self.camera_anchor_vector.x = self.rect.centerx
        # Update pos y
        self.rect.y += self.velocity.y * dt
        self.camera_anchor_vector.y = self.rect.centery
