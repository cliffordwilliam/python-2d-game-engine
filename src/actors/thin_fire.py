from typing import TYPE_CHECKING

from constants import NATIVE_SURF
from constants import pg
from nodes.animator import Animator
from schemas import AnimationMetadata
from schemas import AnimationSpriteMetadata
from typeguard import typechecked

if TYPE_CHECKING:
    from nodes.camera import Camera


@typechecked
class ThinFire:
    """
    TODO
    """

    def __init__(
        self,
        sprite_sheet_surf: pg.Surface,
        camera: "Camera",
        animation_data: dict[str, AnimationMetadata],
        x: int,
        y: int,
    ):
        # Owner loads sprite sheet, camera and animation data for me
        self.sprite_sheet_surf: pg.Surface = sprite_sheet_surf
        self.camera: "Camera" = camera
        self.aniamtion_data: dict[str, AnimationMetadata] = animation_data

        # Get metadata from animation to init rect and region
        self.initial_animation: str = "burn"
        self.animation_sprite_width: int = self.aniamtion_data[self.initial_animation].animation_sprite_width
        self.animation_sprite_height: int = self.aniamtion_data[self.initial_animation].animation_sprite_height
        self.frame_data: AnimationSpriteMetadata = self.aniamtion_data[self.initial_animation].animation_sprites_list[0]

        # Rect
        self.rect = pg.Rect(x, y, self.animation_sprite_width, self.animation_sprite_height)

        # Animator node
        self.animator = Animator(
            initial_animation_name=self.initial_animation,
            animation_data=self.aniamtion_data,
        )
        self.animator.add_event_listener(self._on_animation_frame_change, Animator.FRAME_CHANGED)

    def _on_animation_frame_change(self, frame_data: AnimationSpriteMetadata) -> None:
        self.frame_data = frame_data

    def draw(self) -> None:
        # Turn my coord to screen coord
        screen_x = self.rect.x - self.camera.rect.x
        screen_y = self.rect.y - self.camera.rect.y

        # Draw on screen coord with region
        NATIVE_SURF.blit(
            self.sprite_sheet_surf,
            (screen_x, screen_y),
            (self.frame_data.x, self.frame_data.y, self.animation_sprite_width, self.animation_sprite_height),
        )

    def update(self, dt: int) -> None:
        # Update animation counter
        self.animator.update(dt)
