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

    INDEX_CHANGED: int = 0
    BUTTON_SELECTED: int = 1

    DESCRIPTION_SURF_WIDTH: int = 320
    DESCRIPTION_SURF_HEIGHT: int = 9
    DESCRIPTION_RECT_TOP_LEFT: tuple = (0, 151)
    DESCRIPTION_SURF_COLOR: str = "#000f28"

    def __init__(self, buttons: List[Button], offset: int, limit: int):
        self.buttons: List[Button] = buttons

        self.offset: int = offset

        self.limit: int = limit

        self.end_offset: int = self.offset + self.limit

        self.button_draw_y_offset: int = 0

        self.buttons_len: int = len(self.buttons)

        self.index: int = 0

        self.listener_index_changed: List[Callable] = []
        self.listener_button_selected: List[Callable] = []

        self.is_input_allowed: bool = False

        self.description_surf: pg.Surface = pg.Surface(
            (self.DESCRIPTION_SURF_WIDTH, self.DESCRIPTION_SURF_HEIGHT)
        )
        self.description_surf.fill(self.DESCRIPTION_SURF_COLOR)
        self.description_rect: pg.Rect = self.description_surf.get_rect()
        self.description_rect.bottomleft = NATIVE_RECT.bottomleft

        self.remainder: float = 0

    def add_event_listener(self, value: Callable, event: int) -> None:
        """
        Subscribe to my events.
        """
        if event == self.INDEX_CHANGED:
            self.listener_index_changed.append(value)

        elif event == self.BUTTON_SELECTED:
            self.listener_button_selected.append(value)

    def event(self, game: "Game") -> None:
        """
        Uses event to update index and notify my subscribers.
        """

        if not self.is_input_allowed:
            return

        # Remember old index to set old button inactive
        old_index: int = self.index
        is_pressed_up_or_down: bool = False

        # So that if both are just pressed in 1 frame, index is 0
        if game.is_up_just_pressed:
            is_pressed_up_or_down = True
            self.index -= 1
        if game.is_down_just_pressed:
            is_pressed_up_or_down = True
            self.index += 1

        if is_pressed_up_or_down:
            self.index = self.index % self.buttons_len
            if old_index != self.index:
                if self.index == self.end_offset:
                    self.set_offset(self.offset + 1)

                elif self.index == self.offset - 1:
                    self.set_offset(self.offset - 1)

                elif old_index == self.buttons_len - 1 and self.index == 0:
                    self.set_offset(0)

                elif old_index == 0 and self.index == self.buttons_len - 1:
                    self.set_offset(self.buttons_len - self.limit)

                old_button: Button = self.buttons[old_index]
                new_button: Button = self.buttons[self.index]
                old_button.set_state(Button.INACTIVE)
                new_button.set_state(Button.ACTIVE)
                for callback in self.listener_index_changed:
                    callback(new_button)

        # Selected button
        if game.is_enter_just_pressed:
            selected_button: Button = self.buttons[self.index]
            for callback in self.listener_button_selected:
                callback(selected_button)

    def set_is_input_allowed(self, value: bool) -> None:
        self.is_input_allowed = value

        current_button: Button = self.buttons[self.index]

        if self.is_input_allowed:
            current_button.set_state(Button.ACTIVE)

        if not self.is_input_allowed:
            current_button.set_state(Button.INACTIVE)

    def set_offset(self, value: int) -> None:
        self.offset = value
        self.end_offset = self.offset + self.limit
        self.button_draw_y_offset = -10 * self.offset

    def draw(self, surf: pg.Surface) -> None:
        surf.blit(self.description_surf, self.description_rect)

        for index in range(self.offset, self.end_offset):
            button = self.buttons[index]
            button.draw(surf, self.button_draw_y_offset)

        # TODO: Make container stack auto, like flex box col
        # TODO: Keep track of button height and button bottom margin

        # Get top left for bar
        button_x = self.buttons[0].rect.x
        button_y = self.buttons[0].rect.y

        size_ratio = self.limit / self.buttons_len

        limit_height = (
            10 * self.limit
        )  # 10 = button height + button bottom margin
        bar_height = (
            size_ratio * limit_height
        )  # apply ratio lim height : tot height -> bar height : lim height
        bar_distance_to_cover = limit_height - bar_height
        bar_step = bar_distance_to_cover / (self.buttons_len - 1)

        # take remainder
        bar_step += self.remainder

        bar_step = int(
            clamp(round(self.index * bar_step), 0, bar_distance_to_cover)
        )

        pg.draw.line(
            surf,
            "#44afe7",
            (button_x - 3, button_y + bar_step),
            (button_x - 3, button_y + bar_step + bar_height),
        )

    def update(self, dt: int) -> None:
        # Active animation lerp
        for button in self.buttons:
            button.update(dt)
