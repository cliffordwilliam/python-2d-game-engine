from typing import Callable

from schemas import AnimationMetadata
from schemas import AnimationSpriteMetadata
from typeguard import typechecked


@typechecked
class Animator:
    # Event names
    ANIMATION_END: int = 0
    FRAME_CHANGED: int = 1

    def __init__(
        self,
        initial_animation_name: str,
        animation_data: dict[str, AnimationMetadata],
    ):
        # Starting animation
        if initial_animation_name not in animation_data:
            raise ValueError(f"Unsupported animation name: {initial_animation_name}")
        self.current_animation = initial_animation_name

        # Get animation metadata
        self.animation_data = animation_data
        self.animation_is_loop: int = self.animation_data[self.current_animation].animation_is_loop
        self.next_animation_name: str = self.animation_data[self.current_animation].next_animation_name
        self.animation_duration: int = self.animation_data[self.current_animation].animation_duration
        self.animation_sprite_height: int = self.animation_data[self.current_animation].animation_sprite_height
        self.animation_sprite_width: int = self.animation_data[self.current_animation].animation_sprite_width
        self.animation_sprites_list: list[AnimationSpriteMetadata] = self.animation_data[
            self.current_animation
        ].animation_sprites_list
        self.frames_list_len: int = len(self.animation_sprites_list)
        self.frames_list_index_len: int = self.frames_list_len - 1
        self.frame_index: int = 0
        self.timer: int = 0

        # Set to true when done counting
        self.is_done: bool = False

        # Key is event name, value is a list of listeners
        self.event_listeners: dict[int, list[Callable]] = {
            self.ANIMATION_END: [],
            self.FRAME_CHANGED: [],
        }

    def add_event_listener(self, value: Callable, event: int) -> None:
        """
        Subscribe to my events.
        """

        # The event user is supported?
        if event in self.event_listeners:
            # Collect it
            self.event_listeners[event].append(value)
        else:
            # Throw error
            raise ValueError(f"Unsupported event type: {event}")

    def set_current_animation(self, value: str) -> None:
        """
        Set animation name.
        This also resets frame index and timer.
        """

        # Calling the same animation name when it is playing will reset it to start
        self.is_done = False

        # Get current animation data
        if value not in self.animation_data:
            raise ValueError(f"Unsupported animation name: {value}")
        self.current_animation = value
        self.animation_is_loop = self.animation_data[self.current_animation].animation_is_loop
        self.next_animation_name = self.animation_data[self.current_animation].next_animation_name
        self.animation_duration = self.animation_data[self.current_animation].animation_duration
        self.animation_sprite_height = self.animation_data[self.current_animation].animation_sprite_height
        self.animation_sprite_width = self.animation_data[self.current_animation].animation_sprite_width
        self.animation_sprites_list = self.animation_data[self.current_animation].animation_sprites_list
        self.frames_list_len = len(self.animation_sprites_list)
        self.frames_list_index_len = self.frames_list_len - 1
        self._set_frame_index(0)
        self.timer = 0

    def _set_frame_index(self, value: int) -> None:
        # Update frame index
        self.frame_index = value

        # Prev frame was last frame?
        if self.frame_index > self.frames_list_index_len:
            # This anim loop?
            if self.animation_is_loop == 1:
                # Reset frame index
                self.frame_index = 0

            # This anim do not loop?
            else:
                # Stay on last frame
                self.frame_index -= 1

                # Has transition animation?
                if self.next_animation_name in self.animation_data:
                    # Change to transition animation, reset timer and frame index
                    self.set_current_animation(self.next_animation_name)
                    return

                # Set is done true
                self.is_done = True
                # Fire ANIMATION END event
                for callback in self.event_listeners[self.ANIMATION_END]:
                    callback()

                # If staying on last frame no need to update owner region data
                return

        # Fire FRAME_CHANGED event with info region x y
        self.frame_data = self.animation_sprites_list[self.frame_index]
        for callback in self.event_listeners[self.FRAME_CHANGED]:
            callback(self.frame_index, self.frame_data)

    def update(self, dt: int) -> None:
        # Prev frame stayed on last frame?
        if self.is_done:
            # Return
            return

        # Count up
        self.timer += dt
        # Count beyond duration?
        if self.timer >= self.animation_duration:
            # Reset timer 0
            self.timer = 0
            # Update to next frame index by 1
            self._set_frame_index(self.frame_index + 1)
