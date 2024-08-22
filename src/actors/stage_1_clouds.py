from typing import TYPE_CHECKING

from constants import NATIVE_HEIGHT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import pg
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.camera import Camera


@typechecked
class Stage1Clouds:
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
    sprite_layer: int = 2

    def __init__(
        self,
        sprite_sheet_surf: pg.Surface,
        camera: "Camera",
    ):
        # Load and instanced the sprite sheet and camera for me to use here
        self.sprite_sheet_surf: pg.Surface = sprite_sheet_surf
        self.camera: "Camera" = camera

        # My constants metadata
        self.sprite_name: str = "clouds"
        self.sprite_width: int = 320
        self.sprite_height: int = 160
        self.sprite_x: int = 0
        self.sprite_y: int = 128
        self.draw_scale_x: float = 0.1
        self.draw_scale_y: float = 0.0
        self.sprite_region: tuple[int, int, int, int] = (self.sprite_x, self.sprite_y, self.sprite_width, self.sprite_height)

        # Make my surf
        self.surf: pg.Surface = pg.Surface((NATIVE_WIDTH, NATIVE_HEIGHT))
        # Fill invisible
        self.surf.set_colorkey("red")
        self.surf.fill("red")
        # Draw on it, construct the whole thing here by stamping the regions
        self.surf.blit(
            self.sprite_sheet_surf,
            (
                0,
                0,
            ),
            self.sprite_region,
        )

    def draw(self) -> None:
        blit_sequence = []

        x = (-self.camera.rect.x * self.draw_scale_x) % NATIVE_WIDTH

        # Bottom Right
        blit_sequence.append(
            (
                self.surf,
                (
                    x,
                    0,
                ),
            )
        )
        # Bottom Left
        blit_sequence.append(
            (
                self.surf,
                (
                    x - NATIVE_WIDTH,
                    0,
                ),
            )
        )

        NATIVE_SURF.fblits(blit_sequence)
