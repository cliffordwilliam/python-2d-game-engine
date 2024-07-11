from enum import Enum
from typing import Callable
from typing import Dict
from typing import Tuple

from typeguard import typechecked


@typechecked
class StateMachine:
    def __init__(
        self,
        initial_state: Enum,
        state_handlers: Dict[Enum, Callable],
        transition_actions: Dict[Tuple[Enum, Enum], Callable],
    ):
        self.state = initial_state
        self.state_handlers = state_handlers
        self.transition_actions = transition_actions

    def change_state(self, new_state: Enum) -> None:
        transition = (self.state, new_state)
        if new_state in self.state_handlers:
            if transition in self.transition_actions:
                self.transition_actions[transition]()
            self.state = new_state
        else:
            print(f"Invalid state transition: {new_state}")

    def handle(self, dt: int) -> None:
        handler = self.state_handlers.get(self.state)
        if handler:
            handler(dt)
        else:
            print(f"No handler for state: {self.state}")
