from typing import TYPE_CHECKING

from constants import NATIVE_HALF_HEIGHT
from constants import NATIVE_HALF_WIDTH
from constants import NATIVE_HEIGHT
from constants import NATIVE_RECT
from constants import NATIVE_WIDTH
from constants import pg
from pygame.math import clamp
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.game import Game

from pygame.math import lerp
from pygame.math import Vector2


@typechecked
class Camera:
    """
    Camera is a frect, it follows a vector point smoothly.
    Frect so that I can get the sides quickly from its prop.
    Frect because it moves in floats.
    Vector point is clamped; impossible for camera edge to be outside limit.

    You move the vector point and the camera rect follows within its limits.

    Parameters:
    - asd: asd.

    Update:
    - asd.
    """

    def __init__(
        self,
        target_vector: Vector2,
        # REMOVE IN BUILD.
        game: "Game",
    ):
        # REMOVE IN BUILD.
        self.game = game

        self.target_vector = target_vector

        self.rect: pg.FRect = pg.FRect(0, 0, NATIVE_WIDTH, NATIVE_HEIGHT)

        # Set this in terms of camera rect to define.
        self.limit_top_rect = -999999.9
        self.limit_bottom_rect = 999999.9
        self.limit_left_rect = -999999.9
        self.limit_right_rect = 999999.9
        # Generated from rect limit to limit the target vector internally.
        self.left_limit_target_vector = (
            self.limit_left_rect + NATIVE_HALF_WIDTH
        )
        self.right_limit_target_vector = (
            self.limit_right_rect - NATIVE_HALF_WIDTH
        )
        self.top_limit_target_vector = self.limit_top_rect + NATIVE_HALF_HEIGHT
        self.bottom_limit_target_vector = (
            self.limit_bottom_rect - NATIVE_HALF_HEIGHT
        )

        self.lerp_weight: float = 0.01
        self.lerp_distance_tolerance: float = 0.01

    def set_target_vector(self, value: Vector2) -> None:
        self.target_vector = value

    def set_rect_limit(
        self,
        limit_top_rect: float,
        limit_bottom_rect: float,
        limit_left_rect: float,
        limit_right_rect: float,
    ) -> None:
        # Set this in terms of camera rect to define.
        self.limit_top_rect = limit_top_rect
        self.limit_bottom_rect = limit_bottom_rect
        self.limit_left_rect = limit_left_rect
        self.limit_right_rect = limit_right_rect
        # Generated from rect limit to limit the target vector internally.
        self.left_limit_target_vector = (
            self.limit_left_rect + NATIVE_HALF_WIDTH
        )
        self.right_limit_target_vector = (
            self.limit_right_rect - NATIVE_HALF_WIDTH
        )
        self.top_limit_target_vector = self.limit_top_rect + NATIVE_HALF_HEIGHT
        self.bottom_limit_target_vector = (
            self.limit_bottom_rect - NATIVE_HALF_HEIGHT
        )

    def update(self, dt: int) -> None:
        # No target_vector? Return.
        if self.target_vector is None:
            return

        # Prevent target to be in a pos where cam is outside room.
        # Camera is the same size as native surf.
        self.target_vector.x = clamp(
            self.target_vector.x,
            self.left_limit_target_vector,
            self.right_limit_target_vector,
        )
        self.target_vector.y = clamp(
            self.target_vector.y,
            self.top_limit_target_vector,
            self.bottom_limit_target_vector,
        )

        # Camera rect center x not on target vector x?
        if (
            abs(self.rect.centerx - self.target_vector.x)
            > self.lerp_distance_tolerance
        ):
            # Lerp it to target horizontally.
            self.rect.centerx = lerp(
                self.rect.centerx, self.target_vector.x, self.lerp_weight * dt
            )
        # Snap to target if close enough.
        else:
            self.rect.centerx = self.target_vector.x

        # Camera rect center y not on target vector y?
        if (
            abs(self.rect.centery - self.target_vector.y)
            > self.lerp_distance_tolerance
        ):
            # Lerp it to target vertically.
            self.rect.centery = lerp(
                self.rect.centery, self.target_vector.y, self.lerp_weight * dt
            )
        # Snap to target if close enough.
        else:
            self.rect.centery = self.target_vector.y

        # REMOVE IN BUILD.
        # Debug draw.
        if self.game.is_debug:
            # Draw my center.
            x = NATIVE_RECT.centerx
            y = NATIVE_RECT.centery

            self.game.debug_draw.add(
                {
                    "type": "circle",
                    "layer": 5,
                    "color": "red",
                    "center": (x, y),
                    "radius": 2,
                }
            )

            # Draw target.
            float_x = self.target_vector.x - self.rect.x
            float_y = self.target_vector.y - self.rect.y

            self.game.debug_draw.add(
                {
                    "type": "circle",
                    "layer": 5,
                    "color": "yellow",
                    "center": (float_x, float_y),
                    "radius": 2,
                }
            )
