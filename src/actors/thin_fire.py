from typing import TYPE_CHECKING

from constants import pg
from constants import TILE_SIZE
from nodes.animator import Animator
from schemas import AnimationMetadata
from schemas import AnimationSpriteMetadata
from typeguard import typechecked

if TYPE_CHECKING:
    from nodes.camera import Camera


@typechecked
class ThinFire:
    """
    TODO: write doc for this actor
    """

    def __init__(
        self,
        sprite_sheet_surf: pg.Surface,
        camera: "Camera",
        animation_data: dict[str, AnimationMetadata],
        room_width: int,
        room_height: int,
        room_width_tu: int,
        room_height_tu: int,
    ):
        # Owner loads sprite sheet, camera and animation data for me
        self.sprite_sheet_surf: pg.Surface = sprite_sheet_surf
        self.camera: "Camera" = camera
        self.aniamtion_data: dict[str, AnimationMetadata] = animation_data

        # Get metadata from animation to init rect and region
        self.initial_animation: str = "burn"
        self.animation_sprite_width: int = self.aniamtion_data[self.initial_animation].animation_sprite_width
        self.animation_sprite_height: int = self.aniamtion_data[self.initial_animation].animation_sprite_height
        self.frame_index: int = 0
        self.animation_sprites_list: list[AnimationSpriteMetadata] = self.aniamtion_data[
            self.initial_animation
        ].animation_sprites_list
        self.animation_sprites_list_len: int = len(self.animation_sprites_list)
        self.pre_render_frame_surf_width: int = room_width
        self.pre_render_frame_surf_height: int = room_height
        self.pre_render_frame_surf_width_tu: int = room_width_tu
        self.pre_render_frame_surf_height_tu: int = room_height_tu

        # Pre render surfs as big as room, 1 surf for 1 frame
        self.pre_render_frame_surfs_list: list[pg.Surface] = []

        # For every frame creates a surf as big as room
        for _ in range(self.animation_sprites_list_len):
            pre_render_frame_surf: pg.Surface = pg.Surface((self.pre_render_frame_surf_width, self.pre_render_frame_surf_height))
            pre_render_frame_surf.set_colorkey("red")
            pre_render_frame_surf.fill("red")
            self.pre_render_frame_surfs_list.append(pre_render_frame_surf)

        # Animator node
        self.animator = Animator(
            initial_animation_name=self.initial_animation,
            animation_data=self.aniamtion_data,
        )
        self.animator.add_event_listener(self._on_animation_frame_change, Animator.FRAME_CHANGED)

    def _on_animation_frame_change(self, frame_index: int, _frame_data: AnimationSpriteMetadata) -> None:
        self.frame_index = frame_index

    def update_pre_render_frame_surfs(self, collision_map_list: list[int]) -> None:
        """
        Reads the given collision map.
        Whenever it reads, it will recreate the whole pre render from square one.
        Then based on what is on collision map, will draw on pre render as if it is the first time.
        """

        # Reset the pre render surfs
        self.pre_render_frame_surfs_list = []
        # For every frame creates a surf as big as room
        for _ in range(self.animation_sprites_list_len):
            pre_render_frame_surf = pg.Surface((self.pre_render_frame_surf_width, self.pre_render_frame_surf_height))
            pre_render_frame_surf.set_colorkey("red")
            pre_render_frame_surf.fill("red")
            self.pre_render_frame_surfs_list.append(pre_render_frame_surf)
        # Iter over the collision map cells
        for cell_index in range(len(collision_map_list)):
            # Get cell
            cell = collision_map_list[cell_index]
            # Cell occupied?
            if cell == 1:
                # Turn occupied cell index to coord
                coord = self._get_coords_from_index(
                    cell_index,
                    self.pre_render_frame_surf_width_tu,
                    self.pre_render_frame_surf_height_tu,
                )
                # Make sure index exists
                if coord[0] == -1 or coord[1] == -1:
                    return
                world_x_tu = coord[0]
                world_y_tu = coord[1]
                world_x_snapped = world_x_tu * TILE_SIZE
                world_y_snapped = world_y_tu * TILE_SIZE
                # Use coord to update each pre render
                for j in range(self.animation_sprites_list_len):
                    # Get this pre render frame surf
                    pre_render_frame_surf = self.pre_render_frame_surfs_list[j]
                    # Get this animation frame
                    animation_sprite_metadata = self.animation_sprites_list[j]
                    # Draw this animation frame on this pre render on snapped world mouse
                    pre_render_frame_surf.blit(
                        self.sprite_sheet_surf,
                        (world_x_snapped, world_y_snapped),
                        (
                            animation_sprite_metadata.x,
                            animation_sprite_metadata.y,
                            self.animation_sprite_width,
                            self.animation_sprite_height,
                        ),
                    )

    def draw(
        self, blit_sequence: list[tuple[pg.Surface, tuple[float, float]]]
    ) -> list[
        # List of tuples. Tuple -> (surf, tuple coord)
        tuple[pg.Surface, tuple[float, float]]
    ]:
        """
        This takes existing blit sequence, adds my current pre render frame to it and returns it.
        """

        blit_sequence.append(
            (
                self.pre_render_frame_surfs_list[self.frame_index],
                (
                    -self.camera.rect.x,
                    -self.camera.rect.y,
                ),
            )
        )

        return blit_sequence

    def update(self, dt: int) -> None:
        # Update animation counter
        self.animator.update(dt)

    # Helper
    def _get_coords_from_index(self, index: int, room_width_tu: int, room_height_tu: int) -> tuple[int, int]:
        """
        Returns the (x, y) coordinates for a given index in the collision map list.
        Returns (-1, -1) if the index is out of bounds.
        """
        if 0 <= index < room_width_tu * room_height_tu:
            x = index % room_width_tu
            y = index // room_width_tu
            return x, y
        else:
            return -1, -1
