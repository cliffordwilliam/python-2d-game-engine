from math import ceil
from typing import Callable
from typing import TYPE_CHECKING

from constants import NATIVE_RECT
from constants import pg
from nodes.button import Button
from pygame.math import clamp
from pygame.math import lerp
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.event_handler import EventHandler
    from nodes.sound_manager import SoundManager


@typechecked
class ButtonContainer:
    # Event names
    INDEX_CHANGED: int = 0
    BUTTON_SELECTED: int = 1

    # Description dimension, position and color
    DESCRIPTION_SURF_WIDTH: int = 320
    DESCRIPTION_SURF_HEIGHT: int = 9
    DESCRIPTION_RECT_TOP_LEFT: tuple = (0, 151)
    DESCRIPTION_SURF_COLOR: str = "#000f28"

    def __init__(
        self,
        buttons: list[Button],
        offset: int,
        limit: int,
        is_pagination: bool,
        game_event_handler: "EventHandler",
        game_sound_manager: "SoundManager",
    ):
        # Initialize game
        self.game_event_handler = game_event_handler
        self.game_sound_manager = game_sound_manager

        # Set pagination on or off
        self.is_pagination = is_pagination

        # Get buttons list
        self.buttons: list[Button] = buttons
        self.buttons_len: int = len(self.buttons)
        self.buttons_len_index: int = self.buttons_len - 1

        # Button margin and height with margin
        self.bottom_margin: int = 1
        self.button_height_with_margin: int = self.buttons[0].rect.height + self.bottom_margin

        # Reposition button like flex col, from top first button
        for i in range(self.buttons_len):
            self.buttons[i].apply_y_offset_to_rect_and_curtain_rects(i * self.button_height_with_margin)

        # Needed by both default and pagination
        self.offset: int = offset
        self.limit: int = min(limit, self.buttons_len)
        # Not pagination?
        if not self.is_pagination:
            # Set limit to total button len
            self.limit = self.buttons_len
        self.end_offset: int = self.offset + self.limit
        self.button_draw_y_offset: int = 0

        # Hovered button index
        self.index: int = 0

        # Event subscribers list
        self.event_listeners: dict[int, list[Callable]] = {
            self.INDEX_CHANGED: [],
            self.BUTTON_SELECTED: [],
        }

        # Input blocker
        self.is_input_allowed: bool = False

        # Description surf, rect and position
        self.description_surf: pg.Surface = pg.Surface((self.DESCRIPTION_SURF_WIDTH, self.DESCRIPTION_SURF_HEIGHT))
        self.description_surf.fill(self.DESCRIPTION_SURF_COLOR)
        self.description_rect: pg.Rect = self.description_surf.get_rect()
        self.description_rect.bottomleft = NATIVE_RECT.bottomleft

        # Pagination?
        if self.is_pagination:
            # Init scrollbar
            self.scrollbar_x: int = self.buttons[0].rect.x
            self.scrollbar_y: int = self.buttons[0].rect.y
            self.scrollbar_right_margin: int = 3
            self.scrollbar_color: str = "#44afe7"
            self.scrollbar_step: int = 0
            self.limit_height: int = self.button_height_with_margin * self.limit
            self.size_ratio: float = self.limit / self.buttons_len
            self.scrollbar_height: float = self.size_ratio * self.limit_height
            self.bar_distance_to_cover: float = self.limit_height - self.scrollbar_height

            self.update_scrollbar_step_with_index()
            self.scrollbar_surf: pg.Surface = pg.Surface((1, self.scrollbar_height))
            self.scrollbar_surf.fill(self.scrollbar_color)

    def update_scrollbar_step_with_index(self) -> None:
        """
        Call this whenever the pagination changes.
        This updates scrollbar_step and scrollbar_height.
        Which determines where the scrollbar is drawn.
        """

        fraction: float = self.index / (self.buttons_len_index)
        scrollbar_step: float = lerp(0, self.bar_distance_to_cover, fraction)

        # Truncate, clamp and round up bar step
        self.scrollbar_step = ceil(
            clamp(
                scrollbar_step,
                0.0,
                self.bar_distance_to_cover,
            )
        )

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

    def set_is_input_allowed(self, value: bool) -> None:
        """
        Set input blocker.
        """

        self.is_input_allowed = value

        # Activate / deactivate current button
        current_button: Button = self.buttons[self.index]
        if self.is_input_allowed:
            current_button.set_state(Button.ACTIVE)
        elif not self.is_input_allowed:
            current_button.set_state(Button.INACTIVE)

    def set_offset(self, value: int) -> None:
        """
        Sets:
        - offset.
        - end_offset.
        - button_draw_y_offset.
        """

        self.offset = value
        self.end_offset = self.offset + self.limit
        self.button_draw_y_offset = -self.button_height_with_margin * self.offset

    def draw(self, surf: pg.Surface) -> None:
        """
        Draw:
        - Description.
        - Buttons.

        - Got pagination?
            - Scrollbar.
        """

        # Description
        surf.blit(self.description_surf, self.description_rect)

        # Buttons
        for index in range(self.offset, self.end_offset):
            button = self.buttons[index]
            button.draw(surf, self.button_draw_y_offset)

        # Pagination?
        if self.is_pagination:
            # Scrollbar
            surf.blit(
                self.scrollbar_surf,
                (
                    self.scrollbar_x - self.scrollbar_right_margin,
                    self.scrollbar_y + self.scrollbar_step,
                ),
            )

    def update(self, dt: int) -> None:
        """
        Update:
        - Buttons active curtain.
        - Indexing pagination.
        """

        # Update all buttons active surf
        for button in self.buttons:
            button.update(dt)

        # Input blocker
        if not self.is_input_allowed:
            return

        # No key pressed?
        if not self.game_event_handler.is_any_key_just_pressed:
            return

        # Remember old index to set old button to inactive
        old_index: int = self.index

        # Get up down dir
        dir: int = self.game_event_handler.is_down_just_pressed - self.game_event_handler.is_up_just_pressed
        # If up / down not pressed
        if dir != 0:
            # Update index with dir
            self.index += dir
            # Modulo wrap loop index
            self.index = self.index % self.buttons_len

            # Activate / deactivate old and new button
            old_button: Button = self.buttons[old_index]
            new_button: Button = self.buttons[self.index]
            old_button.set_state(Button.INACTIVE)
            new_button.set_state(Button.ACTIVE)

            # Fire INDEX_CHANGED event
            for callback in self.event_listeners[self.INDEX_CHANGED]:
                callback(new_button)

            # Play hover sound
            self.game_sound_manager.play_sound("001_hover_01.ogg", 0, 0, 0)

            # Pagination?
            if self.is_pagination:
                # Call next / prev page based on index position
                # Handle next page or prev page
                if self.index == self.end_offset:
                    self.set_offset(self.offset + 1)
                elif self.index == self.offset - 1:
                    self.set_offset(self.offset - 1)
                # Handle modulo loop
                elif old_index == self.buttons_len_index and self.index == 0:
                    self.set_offset(0)
                elif old_index == 0 and self.index == self.buttons_len_index:
                    self.set_offset(self.buttons_len - self.limit)

                # Compute scrollbar step and height
                self.update_scrollbar_step_with_index()

        # if up / down not pressed
        else:
            # Press enter
            if self.game_event_handler.is_enter_just_pressed:
                # Fire BUTTON_SELECTED event
                selected_button: Button = self.buttons[self.index]
                for callback in self.event_listeners[self.BUTTON_SELECTED]:
                    callback(selected_button)
                # Play confirm sound
                self.game_sound_manager.play_sound("confirm.ogg", 0, 0, 0)
