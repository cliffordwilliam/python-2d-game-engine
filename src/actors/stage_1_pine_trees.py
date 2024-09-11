from typing import TYPE_CHECKING

from constants import NATIVE_HEIGHT
from constants import NATIVE_WIDTH
from constants import pg
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.camera import Camera


@typechecked
class Stage1PineTrees:
    """
    Too confusing to make a single parallax background class
    So a parallax background is an actor like goblin or fire
    This way it is more flexible to do things
    Like opacity changing when player gets closer to the right
    Or if it moves on its own like elevator or moving train
    """

    def __init__(
        self,
        sprite_sheet_surf: pg.Surface,
        camera: "Camera",
        sprite_name: str,
        sprite_width: int,
        sprite_height: int,
        sprite_x: int,
        sprite_y: int,
    ):
        # Load and instanced the sprite sheet and camera for me to use here
        self.sprite_sheet_surf: pg.Surface = sprite_sheet_surf
        self.camera: "Camera" = camera

        # My constants metadata
        self.sprite_name: str = sprite_name
        self.sprite_width: int = sprite_width
        self.sprite_height: int = sprite_height
        self.sprite_x: int = sprite_x
        self.sprite_y: int = sprite_y

        # Flexible for me to set however this is going to be
        self.draw_scale_x: float = 0.5
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
                32,
            ),
            self.sprite_region,
        )
        self.surf.blit(
            self.sprite_sheet_surf,
            (
                96,
                64,
            ),
            self.sprite_region,
        )
        self.surf.blit(
            self.sprite_sheet_surf,
            (
                160,
                32,
            ),
            self.sprite_region,
        )
        self.surf.blit(
            self.sprite_sheet_surf,
            (
                224,
                16,
            ),
            self.sprite_region,
        )

    def draw(
        self, blit_sequence: list[tuple[pg.Surface, tuple[float, float]]]
    ) -> list[
        # List of tuples. Tuple -> (surf, tuple coord)
        tuple[pg.Surface, tuple[float, float]]
    ]:
        """
        This takes existing blit sequence, adds my surf pre renders to it and returns it.
        """

        x = (-self.camera.rect.x * self.draw_scale_x) % NATIVE_WIDTH

        blit_sequence.extend(
            [
                # Bottom Right
                (
                    self.surf,
                    (
                        x,
                        0,
                    ),
                ),
                # Bottom Left
                (
                    self.surf,
                    (
                        x - NATIVE_WIDTH,
                        0,
                    ),
                ),
            ]
        )

        return blit_sequence
