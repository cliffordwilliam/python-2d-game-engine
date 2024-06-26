from collections.abc import Callable
from typing import TYPE_CHECKING

from constants import NATIVE_RECT, pg
from nodes.button import Button
from pygame.math import clamp
from typeguard import typechecked

if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class ButtonContainer:
    """
    Listen to input, updates button index.

    Events:
    - INDEX_CHANGED.
    - BUTTON_SELECTED.

    Consts:
    - DESCRIPTION_SURF_WIDTH
    - DESCRIPTION_SURF_HEIGHT
    - DESCRIPTION_RECT_TOP_LEFT
    - DESCRIPTION_SURF_COLOR

    Parameters:
    - buttons: buttons list.
    - offset: pagination.
    - limit: pagination.
    - is_pagination: pagination toggle feature.

    Update:
    - Buttons active curtain.

    Draw:
    - Description.
    - Buttons.
    - Scrollbar.
    """

    # Events.
    INDEX_CHANGED: int = 0
    BUTTON_SELECTED: int = 1

    # Description dimension, position and color.
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
    ):
        # Set pagination on or off.
        self.is_pagination = is_pagination

        # Get buttons list.
        self.buttons: list[Button] = buttons
        self.buttons_len: int = len(self.buttons)

        if self.buttons_len > 0:
            # Button margin and height with margin.
            self.bottom_margin: int = 1
            self.button_height_with_margin: int = (
                self.buttons[0].rect.height + self.bottom_margin
            )

            # Reposition button like flex col, from top first button.
            for i in range(self.buttons_len):
                self.buttons[i].rect.y += i * self.button_height_with_margin
                self.buttons[i].active_curtain.rect.y += (
                    i * self.button_height_with_margin
                )
        else:
            self.bottom_margin = 0
            self.button_height_with_margin = 0

        # Pagination.
        self.offset: int = offset
        self.limit: int = limit
        self.end_offset: int = self.offset + self.limit
        self.button_draw_y_offset: int = 0

        # Hovered button index.
        self.index: int = 0

        # Event subscribers list.
        self.listener_index_changed: list[Callable] = []
        self.listener_button_selected: list[Callable] = []

        # Input blocker.
        self.is_input_allowed: bool = False

        # Description surf, rect and position.
        self.description_surf: pg.Surface = pg.Surface(
            (self.DESCRIPTION_SURF_WIDTH, self.DESCRIPTION_SURF_HEIGHT)
        )
        self.description_surf.fill(self.DESCRIPTION_SURF_COLOR)
        self.description_rect: pg.Rect = self.description_surf.get_rect()
        self.description_rect.bottomleft = NATIVE_RECT.bottomleft

        # Scrollbar color, margin, y remainder, position.
        self.scrollbar_color: str = "#44afe7"
        self.scrollbar_right_margin: int = 3
        self.remainder: float = 0
        self.scrollbar_x: int = self.buttons[0].rect.x if self.buttons_len > 0 else 0
        self.scrollbar_y: int = self.buttons[0].rect.y if self.buttons_len > 0 else 0

        # Pagination?
        if self.is_pagination and self.buttons_len > 0:
            # Init scrollbar height and step.
            self.scrollbar_step: float = 0.0
            self.scrollbar_height: float = 0.0

            self.update_scrollbar_step_and_height()

    def update_scrollbar_step_and_height(self) -> None:
        """
        Call this whenever the pagination changes.
        This updates scrollbar_step and scrollbar_height.
        Which determines where the scrollbar is drawn.
        """
        if self.buttons_len == 0:
            return

        # Handle scrollbar, get ratio
        size_ratio: float = self.limit / self.buttons_len

        # Compute the limit height.
        limit_height: int = self.button_height_with_margin * self.limit

        # Constant ratio.
        # (limit height : tot height) = (bar height : limit height)
        self.scrollbar_height = size_ratio * limit_height

        # Compute distance to cover.
        bar_distance_to_cover: float = limit_height - self.scrollbar_height

        # Compute step to take this frame.
        self.scrollbar_step = bar_distance_to_cover / (self.buttons_len - 1)

        # Add lost remainder from prev float truncation.
        self.scrollbar_step += self.remainder

        # Truncate bar step.
        self.scrollbar_step = int(
            clamp(
                round(self.index * self.scrollbar_step),
                0,
                bar_distance_to_cover,
            )
        )

    def add_event_listener(self, value: Callable, event: int) -> None:
        """
        Use this to subscribe to my events:
        - INDEX_CHANGED
        - BUTTON_SELECTED
        """

        if event == self.INDEX_CHANGED:
            self.listener_index_changed.append(value)
        elif event == self.BUTTON_SELECTED:
            self.listener_button_selected.append(value)

    def event(self, game: "Game") -> None:
        """
        Does the following:
        - Listen to up down input.
        - Updates index with up down input.
        - Fire INDEX_CHANGED event.
        - Got pagination?
            - Next / prev page based on index value.
            - Compute scrollbar step and height.

        - Listen to enter input. (if up down were not pressed)
        - Fire BUTTON_SELECTED event.
        """
        if self.buttons_len == 0:
            return

        # Input blocker.
        if not self.is_input_allowed:
            return

        # Remember old index to set old button to inactive.
        old_index: int = self.index
        is_pressed_up_or_down: bool = False

        # Get up down direction like player controller.
        if game.is_up_just_pressed:
            is_pressed_up_or_down = True
            self.index -= 1
        if game.is_down_just_pressed:
            is_pressed_up_or_down = True
            self.index += 1

        # Up or down was pressed?
        if is_pressed_up_or_down:
            # Index changed?
            if old_index != self.index:
                # Modulo wrap loop index.
                self.index = self.index % self.buttons_len

                # Activate / deactivate old and new button.
                old_button: Button = self.buttons[old_index]
                new_button: Button = self.buttons[self.index]
                old_button.set_state(Button.INACTIVE)
                new_button.set_state(Button.ACTIVE)

                # Fire INDEX_CHANGED event.
                for callback in self.listener_index_changed:
                    callback(new_button)

                # Pagination?
                if self.is_pagination:
                    # Call next / prev page based on index position.
                    # Handle next page or prev page.
                    if self.index == self.end_offset:
                        self.set_offset(self.offset + 1)
                    elif self.index == self.offset - 1:
                        self.set_offset(self.offset - 1)
                    # Handle modulo loop.
                    elif old_index == self.buttons_len - 1 and self.index == 0:
                        self.set_offset(0)
                    elif old_index == 0 and self.index == self.buttons_len - 1:
                        self.set_offset(self.buttons_len - self.limit)

                    # Compute scrollbar step and height.
                    self.update_scrollbar_step_and_height()

        # Press enter. (if up / down not pressed)
        elif game.is_enter_just_pressed:
            # Fire BUTTON_SELECTED event.
            selected_button: Button = self.buttons[self.index]
            for callback in self.listener_button_selected:
                callback(selected_button)

    def set_is_input_allowed(self, value: bool) -> None:
        """
        Set input blocker.
        """
        if self.buttons_len == 0:
            return

        self.is_input_allowed = value

        # Activate / deactivate current button.
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
        if self.buttons_len == 0:
            return

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
        # Description.
        surf.blit(self.description_surf, self.description_rect)

        if self.buttons_len == 0:
            return

        # Buttons.
        for index in range(self.offset, self.end_offset):
            button = self.buttons[index]
            button.draw(surf, self.button_draw_y_offset)

        # Pagination?
        if self.is_pagination:
            # Scrollbar.
            pg.draw.line(
                surf,
                self.scrollbar_color,
                (
                    self.scrollbar_x - self.scrollbar_right_margin,
                    self.scrollbar_y + self.scrollbar_step,
                ),
                (
                    self.scrollbar_x - self.scrollbar_right_margin,
                    self.scrollbar_y + self.scrollbar_step + self.scrollbar_height,
                ),
            )

    def update(self, dt: int) -> None:
        """
        Update:
        - Buttons active curtain.
        """
        if self.buttons_len == 0:
            return

        # Update all buttons active surf.
        for button in self.buttons:
            button.update(dt)
