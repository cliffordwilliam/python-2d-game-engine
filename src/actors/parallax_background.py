from typing import TYPE_CHECKING

from constants import pg
from typeguard import typechecked

if TYPE_CHECKING:
    from nodes.camera import Camera


@typechecked
class ParallaxBackground:
    """
    | Parent class for parallax background actors.
    | Provides common functionality.
    | Allows type hints.
    | All child are ParallaxBackground type.
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
        draw_scale_x: float = 0.0,
        draw_scale_y: float = 0.0,
    ):
        # Get ref of loaded sprite sheet surf
        self.sprite_sheet_surf: pg.Surface = sprite_sheet_surf
        # Get ref instanced camera
        self.camera: "Camera" = camera

        # Sprite name
        self.sprite_name: str = sprite_name
        # Sprite size
        self.sprite_width: int = sprite_width
        self.sprite_height: int = sprite_height
        # Sprite position in respect to sprite sheet
        self.sprite_x: int = sprite_x
        self.sprite_y: int = sprite_y

        # Drawing offset scaling for parallax effect
        self.draw_scale_x: float = draw_scale_x
        self.draw_scale_y: float = draw_scale_y

        # Sprite region in sprite sheet
        self.sprite_region: tuple[int, int, int, int] = (
            self.sprite_x,
            self.sprite_y,
            self.sprite_width,
            self.sprite_height,
        )

        # Construct base surface (like stamping 4 trees)
        self.surf: pg.Surface = self.construct_base_surface()

    def construct_base_surface(self) -> pg.Surface:
        """
        | Creates the surface to be used for drawing.
        | Can be extended or overridden in child classes.
        | Children must have this method.
        """

        raise NotImplementedError("Subclasses must implement `construct_base_surface`")

    def draw(
        self,
        blit_sequence: list[tuple[pg.Surface, tuple[float, float]]],
    ) -> list[
        # Tuple -> (surf, world position)
        tuple[pg.Surface, tuple[float, float]]
    ]:
        """
        | Takes existing blit sequence, adds my surf pre renders to it and returns it.
        | Can be extended or overridden in child classes.
        | Children must have this method.
        """

        raise NotImplementedError("Subclasses must implement `draw`")
