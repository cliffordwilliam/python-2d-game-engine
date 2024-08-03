from typing import TYPE_CHECKING

from constants import NATIVE_HEIGHT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import NATIVE_WIDTH_TU
from constants import pg
from constants import TILE_SIZE
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.camera import Camera


@typechecked
class Stage1Glow:
    """
    Too confusing to make a single parallax background class
    So a parallax background is an actor like goblin or fire
    This way it is more flexible to do things
    Like opacity changing when player gets closer to the right
    Or if it moves on its own like elevator or moving train
    """

    # Need to use this before instancing
    # To check if there is an instance or not in this index
    # If got instance then no need to instace
    # If empty then we instance this
    sprite_layer: int = 5

    def __init__(
        self,
        sprite_sheet_surf: pg.Surface,
        camera: "Camera",
    ):
        self.sprite_sheet_surf: pg.Surface = sprite_sheet_surf
        self.camera: "Camera" = camera

        self.sprite_name: str = "glow"
        self.sprite_width: int = 16
        self.sprite_height: int = 128
        self.sprite_x: int = 96
        self.sprite_y: int = 288
        self.draw_scale_x: float = 0.0
        self.draw_scale_y: float = 0.0
        self.sprite_region: tuple[int, int, int, int] = (self.sprite_x, self.sprite_y, self.sprite_width, self.sprite_height)

        # Draw the surf
        self.surf: pg.Surface = pg.Surface((NATIVE_WIDTH, NATIVE_HEIGHT), pg.SRCALPHA)
        # Fill with fully transparent color
        self.surf.fill((0, 0, 0, 0))
        # Draw on it
        for i in range(NATIVE_WIDTH_TU):
            self.surf.blit(
                self.sprite_sheet_surf,
                (
                    i * TILE_SIZE,
                    53,
                ),
                self.sprite_region,
            )

    def draw(self) -> None:
        # Bottom Right
        NATIVE_SURF.blit(
            self.surf,
            (
                0,
                0,
            ),
        )
