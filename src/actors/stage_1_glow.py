from typing import TYPE_CHECKING

from constants import NATIVE_HEIGHT
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

    # Need to use this "sprite_layer" before instancing
    # To check if there is an instance or not in this index
    # If got instance then no need to instace
    # If empty then we instance this
    # TODO: move this to the sprite sheet metadata json
    # TODO: so that I have to read then fill in the constructor here instead of hard coding it
    # TODO: Create new arguments here, take in the
    # TODO: Name, width, height, region x and y, from the sprte name to sprite metadata in the rooms editor
    # TODO: So here you are flexible in how you construct the background, where you stamp the trees and so on
    # TODO: The sprite_layer is not being used in there, you get it from the json, so why have it here
    sprite_layer: int = 5

    def __init__(
        self,
        sprite_sheet_surf: pg.Surface,
        camera: "Camera",
    ):
        # Load and instanced the sprite sheet and camera for me to use here
        self.sprite_sheet_surf: pg.Surface = sprite_sheet_surf
        self.camera: "Camera" = camera

        # My constants metadata
        # TODO: Get from room name to metadata dict later
        self.sprite_name: str = "glow"
        self.sprite_width: int = 16
        self.sprite_height: int = 128
        self.sprite_x: int = 96
        self.sprite_y: int = 288

        # Flexible for me to set however this is going to be
        self.draw_scale_x: float = 0.0
        self.draw_scale_y: float = 0.0
        self.sprite_region: tuple[int, int, int, int] = (
            self.sprite_x,
            self.sprite_y,
            self.sprite_width,
            self.sprite_height,
        )

        # Make my surf
        self.surf: pg.Surface = pg.Surface((NATIVE_WIDTH, NATIVE_HEIGHT), pg.SRCALPHA)
        # Fill with fully transparent color
        self.surf.fill((0, 0, 0, 0))
        # Draw on it, construct the whole thing here by stamping the regions (Flexible)
        for i in range(NATIVE_WIDTH_TU):
            self.surf.blit(
                self.sprite_sheet_surf,
                (
                    i * TILE_SIZE,
                    53,
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

        # Bottom Right
        blit_sequence.append(
            (
                self.surf,
                (
                    0,
                    0,
                ),
            )
        )

        return blit_sequence
