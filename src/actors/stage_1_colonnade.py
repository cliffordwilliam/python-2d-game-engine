from typing import TYPE_CHECKING

from actors.parallax_background import ParallaxBackground
from constants import NATIVE_HEIGHT
from constants import NATIVE_WIDTH
from constants import pg
from constants import TILE_SIZE
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.camera import Camera


@typechecked
class Stage1Colonnade(ParallaxBackground):
    """
    Actor that only draws itself with scaled offset.
    Instanced during room data reading.

    TODO: Add the features below later with parent update method
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
        super().__init__(
            sprite_sheet_surf=sprite_sheet_surf,
            camera=camera,
            sprite_name=sprite_name,
            sprite_width=sprite_width,
            sprite_height=sprite_height,
            sprite_x=sprite_x,
            sprite_y=sprite_y,
            draw_scale_x=0.25,
            draw_scale_y=0.25,
        )

    def construct_base_surface(self) -> pg.Surface:
        """
        | Creates the surface to be used for drawing.
        | Can be extended or overridden in child classes.
        | Children must have this method.
        """

        # Make surf
        surf: pg.Surface = pg.Surface((NATIVE_WIDTH, NATIVE_HEIGHT))
        # Fill surf with invisible color
        surf.set_colorkey("red")
        surf.fill("red")
        # Stamp colonnade sprite regions on surf
        surf.blit(
            self.sprite_sheet_surf,
            (
                -4 * TILE_SIZE,
                0,
            ),
            self.sprite_region,
        )
        surf.blit(
            self.sprite_sheet_surf,
            (
                2 * TILE_SIZE,
                0,
            ),
            self.sprite_region,
        )
        surf.blit(
            self.sprite_sheet_surf,
            (
                8 * TILE_SIZE,
                0,
            ),
            self.sprite_region,
        )
        surf.blit(
            self.sprite_sheet_surf,
            (
                14 * TILE_SIZE,
                0,
            ),
            self.sprite_region,
        )
        surf.blit(
            self.sprite_sheet_surf,
            (
                -4 * TILE_SIZE,
                10 * TILE_SIZE,
            ),
            self.sprite_region,
        )
        surf.blit(
            self.sprite_sheet_surf,
            (
                2 * TILE_SIZE,
                10 * TILE_SIZE,
            ),
            self.sprite_region,
        )
        surf.blit(
            self.sprite_sheet_surf,
            (
                8 * TILE_SIZE,
                10 * TILE_SIZE,
            ),
            self.sprite_region,
        )
        surf.blit(
            self.sprite_sheet_surf,
            (
                14 * TILE_SIZE,
                10 * TILE_SIZE,
            ),
            self.sprite_region,
        )
        # Return surf to be my prop
        return surf

    def draw(
        self, blit_sequence: list[tuple[pg.Surface, tuple[float, float]]]
    ) -> list[
        # List of tuples. Tuple -> (surf, tuple coord)
        tuple[pg.Surface, tuple[float, float]]
    ]:
        """
        | Takes existing blit sequence, adds my surf pre renders to it and returns it.
        | Can be extended or overridden in child classes.
        | Children must have this method.
        """

        # Get scaled x draw offset position
        x = (-self.camera.rect.x * self.draw_scale_x) % NATIVE_WIDTH
        # Get scaled y draw offset position
        y = (-self.camera.rect.y * self.draw_scale_y) % NATIVE_HEIGHT

        # Add surf on scaled draw offset position to blit sequence
        blit_sequence.extend(
            [
                # Bottom Right
                (
                    self.surf,
                    (
                        x,
                        y,
                    ),
                ),
                # Bottom Left
                (
                    self.surf,
                    (
                        x - NATIVE_WIDTH,
                        y,
                    ),
                ),
                # Top Right
                (
                    self.surf,
                    (
                        x,
                        y - NATIVE_HEIGHT,
                    ),
                ),
                # Top Left
                (
                    self.surf,
                    (
                        x - NATIVE_WIDTH,
                        y - NATIVE_HEIGHT,
                    ),
                ),
            ]
        )

        # Return blit sequence
        return blit_sequence
