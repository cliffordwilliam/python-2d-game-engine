from typing import Callable
from typing import List
from typing import TYPE_CHECKING

from nodes.button import Button
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class ButtonContainer:
    """
    This thing only job is to listen to input.
    Toggle button active states.
    Fire events on index change and clicks.
    """

    INDEX_CHANGED: int = 0

    def __init__(self, buttons: List[Button]):
        self.buttons: List[Button] = buttons

        self.buttons_len: int = len(self.buttons)

        self.index: int = 0

        self.listener_index_changed: List[Callable] = []

        # TODO: When do I activate first button?

    def add_event_listener(self, value: Callable, event: int) -> None:
        if event == self.INDEX_CHANGED:
            self.listener_index_changed.append(value)

    def event(self, game: "Game") -> None:
        """
        Uses event to update index and notify my subscribers.
        """

        # Remember old index to set old button inactive
        old_index: int = self.index
        is_pressed: bool = False

        # So that if both are just pressed in 1 frame, index is 0
        if game.is_up_just_pressed:
            is_pressed = True
            self.index -= 1
        if game.is_down_just_pressed:
            is_pressed = True
            self.index += 1

        if is_pressed:
            self.index = self.index % self.buttons_len
            if old_index != self.index:
                old_button: Button = self.buttons[old_index]
                new_button: Button = self.buttons[self.index]
                old_button.set_state(Button.INACTIVE)
                new_button.set_state(Button.ACTIVE)

    # def update(self, dt: int) -> None:
    #     """
    #     Update my counting until duration.
    #     """
    #     if self.is_done:
    #         return

    #     self.timer += dt

    #     if self.timer > self.duration:
    #         self.is_done = True

    #         for callback in self.listener_end:
    #             callback()
