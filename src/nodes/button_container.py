from typing import Callable
from typing import List
from typing import TYPE_CHECKING

from constants import NATIVE_RECT
from constants import pg
from nodes.button import Button
from pygame.math import clamp
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class ButtonContainer:
    """
    This thing only job is to listen to input.
    Toggle button active states (draw and update too).
    Fire events on index change and clicks.

    Also draws the desc background
    """

    # Events.
    # Button index changed.
    INDEX_CHANGED: int = 0
    # Button selected.
    BUTTON_SELECTED: int = 1

    # Description dimension, position and color.
    DESCRIPTION_SURF_WIDTH: int = 320
    DESCRIPTION_SURF_HEIGHT: int = 9
    DESCRIPTION_RECT_TOP_LEFT: tuple = (0, 151)
    DESCRIPTION_SURF_COLOR: str = "#000f28"

    def __init__(
        self,
        buttons: List[Button],
        offset: int,
        limit: int,
        is_pagination: bool,
    ):
        # Set pagination or not.
        self.is_pagination = is_pagination

        # Buttons list.
        self.buttons: List[Button] = buttons
        self.buttons_len: int = len(self.buttons)

        # Get button total occupied vertical space.
        self.button_height_with_margin: int = self.buttons[0].height + 1

        # Reposition button like flex col.
        for i in range(self.buttons_len):
            self.buttons[i].rect.y += i * self.button_height_with_margin
            self.buttons[i].active_curtain.rect.y += (
                i * self.button_height_with_margin
            )

        # Pagination.
        self.offset: int = offset
        self.limit: int = limit
        self.end_offset: int = self.offset + self.limit
        # Draw offset for pagination.
        self.button_draw_y_offset: int = 0

        # Focused button index.
        self.index: int = 0

        # INDEX_CHANGED event subscribers list.
        self.listener_index_changed: List[Callable] = []
        # BUTTON_SELECTED event subscribers list.
        self.listener_button_selected: List[Callable] = []

        # User input blocker.
        self.is_input_allowed: bool = False

        # Description surf, rect and position.
        self.description_surf: pg.Surface = pg.Surface(
            (self.DESCRIPTION_SURF_WIDTH, self.DESCRIPTION_SURF_HEIGHT)
        )
        self.description_surf.fill(self.DESCRIPTION_SURF_COLOR)
        self.description_rect: pg.Rect = self.description_surf.get_rect()
        self.description_rect.bottomleft = NATIVE_RECT.bottomleft

        # Scrollbar color
        self.scrollbar_color: str = "#44afe7"
        self.scrollbar_right_margin: int = 3

        # Scrollbar y remainder.
        self.remainder: float = 0

        # Scrollbar top left
        self.scrollbar_x: int = self.buttons[0].rect.x
        self.scrollbar_y: int = self.buttons[0].rect.y

        # Pagination?
        if self.is_pagination:
            # Compute scrollbar step and height for first time.

            # Handle scrollbar, get ratio
            size_ratio: float = self.limit / self.buttons_len

            # Compute the limit height.
            limit_height: int = self.button_height_with_margin * self.limit

            # Constant ratio.
            # (limit height : tot height) = (bar height : limit height)
            self.bar_height: float = size_ratio * limit_height

            # Compute distance to cover.
            bar_distance_to_cover: float = limit_height - self.bar_height

            # Compute step to take this frame.
            self.bar_step: float = bar_distance_to_cover / (
                self.buttons_len - 1
            )

            # Add lost remainder from prev float truncation.
            self.bar_step += self.remainder

            # Truncate bar step.
            self.bar_step = int(
                clamp(
                    round(self.index * self.bar_step), 0, bar_distance_to_cover
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
        Uses event to update index and notify subscribers.
        """

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
                    # Update pagination offset.

                    # Handle next page or prev page for set offset.
                    if self.index == self.end_offset:
                        self.set_offset(self.offset + 1)
                    elif self.index == self.offset - 1:
                        self.set_offset(self.offset - 1)

                    # Handle modulo loop for pagiantion set offset.
                    elif old_index == self.buttons_len - 1 and self.index == 0:
                        self.set_offset(0)
                    elif old_index == 0 and self.index == self.buttons_len - 1:
                        self.set_offset(self.buttons_len - self.limit)

                    # Compute scrollbar step and height.

                    # Handle scrollbar, get ratio
                    size_ratio: float = self.limit / self.buttons_len

                    # Compute the limit height.
                    limit_height: int = (
                        self.button_height_with_margin * self.limit
                    )

                    # Constant ratio.
                    # (limit height : tot height) = (bar height : limit height)
                    self.bar_height = size_ratio * limit_height

                    # Compute distance to cover.
                    bar_distance_to_cover: float = (
                        limit_height - self.bar_height
                    )

                    # Compute step to take this frame.
                    self.bar_step = bar_distance_to_cover / (
                        self.buttons_len - 1
                    )

                    # Add lost remainder from prev float truncation.
                    self.bar_step += self.remainder

                    # Truncate bar step.
                    self.bar_step = int(
                        clamp(
                            round(self.index * self.bar_step),
                            0,
                            bar_distance_to_cover,
                        )
                    )

        # Press enter (can press this same time with directions).
        if game.is_enter_just_pressed:
            # Fire BUTTON_SELECTED event.
            selected_button: Button = self.buttons[self.index]
            for callback in self.listener_button_selected:
                callback(selected_button)

    def set_is_input_allowed(self, value: bool) -> None:
        """
        Set input blocker.
        """

        self.is_input_allowed = value

        # Activate / deactivate current button.
        current_button: Button = self.buttons[self.index]
        if self.is_input_allowed:
            current_button.set_state(Button.ACTIVE)
        elif not self.is_input_allowed:
            current_button.set_state(Button.INACTIVE)

    def set_offset(self, value: int) -> None:
        """
        Set pagination offset and pagination draw y offset.
        """

        self.offset = value
        self.end_offset = self.offset + self.limit
        self.button_draw_y_offset = (
            -self.button_height_with_margin * self.offset
        )

    def draw(self, surf: pg.Surface) -> None:
        """
        Draw:
        - Description.
        - Buttons.
        - Scrollbar.
        """

        # Description.
        surf.blit(self.description_surf, self.description_rect)

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
                    self.scrollbar_y + self.bar_step,
                ),
                (
                    self.scrollbar_x - self.scrollbar_right_margin,
                    self.scrollbar_y + self.bar_step + self.bar_height,
                ),
            )

    def update(self, dt: int) -> None:
        # Active animation lerp.
        for button in self.buttons:
            button.update(dt)
