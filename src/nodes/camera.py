from math import exp
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

from pygame.math import Vector2


@typechecked
class Camera:
    def __init__(
        self,
        target_vector: Vector2,
        # REMOVE IN BUILD
        game: "Game",
    ):
        # REMOVE IN BUILD
        self.game = game

        # Follows this and also limits its position
        self.target_vector: Vector2 = target_vector

        # My rect
        self.rect: pg.FRect = pg.FRect(0, 0, NATIVE_WIDTH, NATIVE_HEIGHT)

        # Set this in terms of camera rect to define
        self.limit_top_rect: float = -10000000.0
        self.limit_bottom_rect: float = 10000000.0
        self.limit_left_rect: float = -10000000.0
        self.limit_right_rect: float = 10000000.0

        # Limit target vector position so it never cause my rect to be outside limit
        self.left_limit_target_vector: float = self.limit_left_rect + NATIVE_HALF_WIDTH
        self.right_limit_target_vector: float = self.limit_right_rect - NATIVE_HALF_WIDTH
        self.top_limit_target_vector: float = self.limit_top_rect + NATIVE_HALF_HEIGHT
        self.bottom_limit_target_vector: float = self.limit_bottom_rect - NATIVE_HALF_HEIGHT

        # Exponential decay
        self.decay: float = 0.01

        # Tolerance to snap to target if close enough
        self.distance_tolerance: float = 1.0

    def set_target_vector(self, value: Vector2) -> None:
        self.target_vector = value

    def set_rect_limit(
        self,
        limit_top_rect: float,
        limit_bottom_rect: float,
        limit_left_rect: float,
        limit_right_rect: float,
    ) -> None:
        # Set this in terms of camera rect to define
        self.limit_top_rect = limit_top_rect
        self.limit_bottom_rect = limit_bottom_rect
        self.limit_left_rect = limit_left_rect
        self.limit_right_rect = limit_right_rect

        # Limit target vector position so it never cause my rect to be outside limit
        self.left_limit_target_vector = self.limit_left_rect + NATIVE_HALF_WIDTH
        self.right_limit_target_vector = self.limit_right_rect - NATIVE_HALF_WIDTH
        self.top_limit_target_vector = self.limit_top_rect + NATIVE_HALF_HEIGHT
        self.bottom_limit_target_vector = self.limit_bottom_rect - NATIVE_HALF_HEIGHT

    def update(self, dt: int) -> None:
        # No target_vector? Return
        if self.target_vector is None:
            return

        # Limit target vector position so it never cause my rect to be outside limit
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

        # Check within tolerance
        is_within_distance_tolerance_x: bool = abs(self.rect.centerx - self.target_vector.x) < self.distance_tolerance
        is_within_distance_tolerance_y: bool = abs(self.rect.centery - self.target_vector.y) < self.distance_tolerance

        # Already arrived on target?
        if is_within_distance_tolerance_x and is_within_distance_tolerance_y:
            # Return
            return

        # Camera rect center x not on target vector x?
        if not is_within_distance_tolerance_x:
            # Lerp it to target horizontally
            self.rect.centerx = self._exp_decay(self.rect.centerx, self.target_vector.x, self.decay, dt)
        # Snap to target horizontally
        else:
            self.rect.centerx = self.target_vector.x

        # Camera rect center y not on target vector y?
        if not is_within_distance_tolerance_y:
            # Lerp it to target vertically
            self.rect.centery = self._exp_decay(self.rect.centery, self.target_vector.y, self.decay, dt)
        # Snap to target vertically
        else:
            self.rect.centery = self.target_vector.y

        # REMOVE IN BUILD
        # Debug draw
        if self.game.is_debug:
            # Draw my center.
            x: int = NATIVE_RECT.centerx
            y: int = NATIVE_RECT.centery
            self.game.debug_draw.add(
                {
                    "type": "circle",
                    "layer": 5,
                    "color": "red",
                    "center": (x, y),
                    "radius": 2,
                }
            )

            # Draw target
            float_x: float = self.target_vector.x - self.rect.x
            float_y: float = self.target_vector.y - self.rect.y
            self.game.debug_draw.add(
                {
                    "type": "circle",
                    "layer": 5,
                    "color": "yellow",
                    "center": (float_x, float_y),
                    "radius": 2,
                }
            )

    def _exp_decay(self, a: float, b: float, decay: float, dt: int) -> float:
        return b + (a - b) * exp(-decay * dt)
