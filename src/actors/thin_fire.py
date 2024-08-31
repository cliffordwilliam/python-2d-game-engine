from typing import TYPE_CHECKING

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
    TODO: write doc for this actor
    """

    def __init__(
        self,
        sprite_sheet_surf: pg.Surface,
        camera: "Camera",
        animation_data: dict[str, AnimationMetadata],
        room_width: int,
        room_height: int,
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

        # Pre render surfs as big as room, 1 surf for 1 frame
        self.pre_render_frame_surfs_list: list[pg.Surface] = []

        # For every frame creates a surf as big as room
        for _ in range(self.animation_sprites_list_len):
            self.pre_render_frame_surf: pg.Surface = pg.Surface(
                (self.pre_render_frame_surf_width, self.pre_render_frame_surf_height)
            )
            self.pre_render_frame_surf.set_colorkey("red")
            self.pre_render_frame_surf.fill("red")
            self.pre_render_frame_surfs_list.append(self.pre_render_frame_surf)

        # Animator node
        self.animator = Animator(
            initial_animation_name=self.initial_animation,
            animation_data=self.aniamtion_data,
        )
        self.animator.add_event_listener(self._on_animation_frame_change, Animator.FRAME_CHANGED)

    def _on_animation_frame_change(self, frame_index: int, _frame_data: AnimationSpriteMetadata) -> None:
        self.frame_index = frame_index

    def POST_draw_frames_on_each_pre_render_frame_surfs(self, world_mouse_snapped_x: int, world_mouse_snapped_y: int) -> None:
        # TODO: Create new surfs on every add and delete
        # TODO: need to find way to keep track of added ones top left positions, since I already know the size
        # TODO: Use the collision map and turn that into top left coord
        # TODO: Then loop the bottom one with the lists of top left coords
        # Iter each pre render frame surfs / animation frames
        for i in range(self.animation_sprites_list_len):
            # Get this pre render frame surf
            pre_render_frame_surf = self.pre_render_frame_surfs_list[i]
            # Get this animation frame
            animation_sprite_metadata = self.animation_sprites_list[i]
            # Draw this animation frame on this pre render on snapped world mouse
            pre_render_frame_surf.blit(
                self.sprite_sheet_surf,
                (world_mouse_snapped_x, world_mouse_snapped_y),
                (
                    animation_sprite_metadata.x,
                    animation_sprite_metadata.y,
                    self.animation_sprite_width,
                    self.animation_sprite_height,
                ),
            )

    def draw(self) -> pg.Surface:
        # Return the current pre render frame for fblits
        return self.pre_render_frame_surfs_list[self.frame_index]

    def update(self, dt: int) -> None:
        # Update animation counter
        self.animator.update(dt)
