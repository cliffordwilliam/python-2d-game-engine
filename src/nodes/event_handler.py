from typing import Any
from typing import TYPE_CHECKING

from constants import pg
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class EventHandler:
    def __init__(self, game: "Game"):
        # Initialize game
        self.game = game

        # All game input flags.
        # Any just pressed and this event.
        self.is_any_key_just_pressed: bool = False
        self.this_frame_event: Any = None
        # REMOVE IN BUILD
        # Debug pressed.
        self.is_0_pressed: bool = False
        self.is_9_pressed: bool = False
        # Directions pressed.
        self.is_up_pressed: bool = False
        self.is_down_pressed: bool = False
        self.is_left_pressed: bool = False
        self.is_right_pressed: bool = False
        # REMOVE IN BUILD
        # Debug just pressed.
        self.is_0_just_pressed: bool = False
        self.is_9_just_pressed: bool = False
        # Directions just pressed.
        self.is_up_just_pressed: bool = False
        self.is_down_just_pressed: bool = False
        self.is_left_just_pressed: bool = False
        self.is_right_just_pressed: bool = False
        # Directions just released.
        self.is_up_just_released: bool = False
        self.is_down_just_released: bool = False
        self.is_left_just_released: bool = False
        self.is_right_just_released: bool = False
        # REMOVE IN BUILD
        # Mouse pressed.
        self.is_lmb_pressed: bool = False
        self.is_rmb_pressed: bool = False
        self.is_mmb_pressed: bool = False
        # REMOVE IN BUILD
        # Mouse just pressed.
        self.is_lmb_just_pressed: bool = False
        self.is_rmb_just_pressed: bool = False
        self.is_mmb_just_pressed: bool = False
        # REMOVE IN BUILD
        # Mouse just released.
        self.is_lmb_just_released: bool = False
        self.is_rmb_just_released: bool = False
        self.is_mmb_just_released: bool = False
        # Actions pressed.
        self.is_enter_pressed: bool = False
        self.is_pause_pressed: bool = False
        self.is_jump_pressed: bool = False
        self.is_attack_pressed: bool = False
        # Actions just pressed.
        self.is_enter_just_pressed: bool = False
        self.is_pause_just_pressed: bool = False
        self.is_jump_just_pressed: bool = False
        self.is_attack_just_pressed: bool = False
        # Actions just released.
        self.is_enter_just_released: bool = False
        self.is_pause_just_released: bool = False
        self.is_jump_just_released: bool = False
        self.is_attack_just_released: bool = False

        self.key_down_handlers = {
            self.game.local_settings_dict["up"]: self.KEYDOWN_UP,
            self.game.local_settings_dict["down"]: self.KEYDOWN_DOWN,
            self.game.local_settings_dict["left"]: self.KEYDOWN_LEFT,
            self.game.local_settings_dict["right"]: self.KEYDOWN_RIGHT,
            self.game.local_settings_dict["enter"]: self.KEYDOWN_ENTER,
            self.game.local_settings_dict["pause"]: self.KEYDOWN_PAUSE,
            self.game.local_settings_dict["jump"]: self.KEYDOWN_JUMP,
            self.game.local_settings_dict["attack"]: self.KEYDOWN_ATTACK,
            # REMOVE IN BUILD
            pg.K_0: self.KEYDOWN_0,
            pg.K_9: self.KEYDOWN_9,
        }

        self.key_up_handlers = {
            self.game.local_settings_dict["up"]: self.KEYUP_UP,
            self.game.local_settings_dict["down"]: self.KEYUP_DOWN,
            self.game.local_settings_dict["left"]: self.KEYUP_LEFT,
            self.game.local_settings_dict["right"]: self.KEYUP_RIGHT,
            self.game.local_settings_dict["enter"]: self.KEYUP_ENTER,
            self.game.local_settings_dict["pause"]: self.KEYUP_PAUSE,
            self.game.local_settings_dict["jump"]: self.KEYUP_JUMP,
            self.game.local_settings_dict["attack"]: self.KEYUP_ATTACK,
            # REMOVE IN BUILD
            pg.K_0: self.KEYUP_0,
            pg.K_9: self.KEYUP_9,
        }

        # REMOVE IN BUILD
        self.mouse_down_handlers = {
            self.game.local_settings_dict["lmb"]: self.MOUSEDOWN_LMB,
            self.game.local_settings_dict["mmb"]: self.MOUSEDOWN_MMB,
            self.game.local_settings_dict["rmb"]: self.MOUSEDOWN_RMB,
        }

        # REMOVE IN BUILD
        self.mouse_up_handlers = {
            self.game.local_settings_dict["lmb"]: self.MOUSEUP_LMB,
            self.game.local_settings_dict["mmb"]: self.MOUSEUP_MMB,
            self.game.local_settings_dict["rmb"]: self.MOUSEUP_RMB,
        }

    # REMOVE IN BUILD
    # MOUSEUP HANDLERS
    def MOUSEUP_LMB(self) -> None:
        self.is_lmb_pressed = False
        self.is_lmb_just_released = True

    def MOUSEUP_MMB(self) -> None:
        self.is_mmb_pressed = False
        self.is_mmb_just_released = True

    def MOUSEUP_RMB(self) -> None:
        self.is_rmb_pressed = False
        self.is_rmb_just_released = True

    # REMOVE IN BUILD
    # MOUSEDOWN HANDLERS
    def MOUSEDOWN_LMB(self) -> None:
        self.is_lmb_pressed = True
        self.is_lmb_just_pressed = True

    def MOUSEDOWN_MMB(self) -> None:
        self.is_mmb_pressed = True
        self.is_mmb_just_pressed = True

    def MOUSEDOWN_RMB(self) -> None:
        self.is_rmb_pressed = True
        self.is_rmb_just_pressed = True

    # KEYDOWN HANDLERS
    def KEYDOWN_UP(self) -> None:
        self.is_up_pressed = True
        self.is_up_just_pressed = True

    def KEYDOWN_DOWN(self) -> None:
        self.is_down_pressed = True
        self.is_down_just_pressed = True

    def KEYDOWN_LEFT(self) -> None:
        self.is_left_pressed = True
        self.is_left_just_pressed = True

    def KEYDOWN_RIGHT(self) -> None:
        self.is_right_pressed = True
        self.is_right_just_pressed = True

    def KEYDOWN_ENTER(self) -> None:
        self.is_enter_pressed = True
        self.is_enter_just_pressed = True

    def KEYDOWN_PAUSE(self) -> None:
        self.is_pause_pressed = True
        self.is_pause_just_pressed = True

    def KEYDOWN_JUMP(self) -> None:
        self.is_jump_pressed = True
        self.is_jump_just_pressed = True

    def KEYDOWN_ATTACK(self) -> None:
        self.is_attack_pressed = True
        self.is_attack_just_pressed = True

    # REMOVE IN BUILD
    def KEYDOWN_0(self) -> None:
        self.is_0_pressed = True
        self.is_0_just_pressed = True

    # REMOVE IN BUILD
    def KEYDOWN_9(self) -> None:
        self.is_9_pressed = True
        self.is_9_just_pressed = True

    # KEYUP HANDLERS
    def KEYUP_UP(self) -> None:
        self.is_up_pressed = False
        self.is_up_just_released = True

    def KEYUP_DOWN(self) -> None:
        self.is_down_pressed = False
        self.is_down_just_released = True

    def KEYUP_LEFT(self) -> None:
        self.is_left_pressed = False
        self.is_left_just_released = True

    def KEYUP_RIGHT(self) -> None:
        self.is_right_pressed = False
        self.is_right_just_released = True

    def KEYUP_ENTER(self) -> None:
        self.is_enter_pressed = False
        self.is_enter_just_released = True

    def KEYUP_PAUSE(self) -> None:
        self.is_pause_pressed = False
        self.is_pause_just_released = True

    def KEYUP_JUMP(self) -> None:
        self.is_jump_pressed = False
        self.is_jump_just_released = True

    def KEYUP_ATTACK(self) -> None:
        self.is_attack_pressed = False
        self.is_attack_just_released = True

    # REMOVE IN BUILD
    def KEYUP_0(self) -> None:
        self.is_0_pressed = False
        self.is_0_just_released = True

    # REMOVE IN BUILD
    def KEYUP_9(self) -> None:
        self.is_9_pressed = False
        self.is_9_just_released = True

    def quit(self) -> None:
        """
        Exit the game.
        """

        pg.quit()
        exit()

    def event(self, event: pg.Event) -> None:
        """
        This is called by the main.py.
        Updates the input flags every frame.
        """

        # Handle window x button on click.
        if event.type == pg.QUIT:
            pg.quit()
            exit()

        # KEYDOWN.
        # Pressed True.
        # Just pressed True.
        elif event.type == pg.KEYDOWN:
            self.is_any_key_just_pressed = True
            self.this_frame_event = event
            handler = self.key_down_handlers.get(event.key)
            if handler:
                handler()

        # KEYUP.
        # Pressed False.
        # Just released True.
        elif event.type == pg.KEYUP:
            handler = self.key_up_handlers.get(event.key)
            if handler:
                handler()

        # REMOVE IN BUILD
        # MOUSEBUTTONDOWN.
        # Pressed True.
        # Just pressed True.
        if event.type == pg.MOUSEBUTTONDOWN:
            handler = self.mouse_down_handlers.get(event.button)
            if handler:
                handler()

        # REMOVE IN BUILD
        # MOUSEBUTTONUP.
        # Pressed False.
        # Just released True.
        elif event.type == pg.MOUSEBUTTONUP:
            handler = self.mouse_up_handlers.get(event.button)
            if handler:
                handler()

    def reset_just_events(self) -> None:
        """
        Resets the flags for just-pressed and just-released events.
        Called by main.py.
        """

        self.is_any_key_just_pressed = False
        self.this_frame_event = None

        # Directions.
        # just pressed False.
        # just released False.
        self.is_up_just_pressed = False
        self.is_down_just_pressed = False
        self.is_left_just_pressed = False
        self.is_right_just_pressed = False
        self.is_up_just_released = False
        self.is_down_just_released = False
        self.is_left_just_released = False
        self.is_right_just_released = False

        # Actions.
        # just pressed False.
        # just released False.
        self.is_enter_just_pressed = False
        self.is_pause_just_pressed = False
        self.is_jump_just_pressed = False
        self.is_attack_just_pressed = False
        self.is_enter_just_released = False
        self.is_pause_just_released = False
        self.is_jump_just_released = False
        self.is_attack_just_released = False

        # REMOVE IN BUILD
        # Mouse.
        # just pressed False.
        # just released False.
        self.is_lmb_just_pressed = False
        self.is_rmb_just_pressed = False
        self.is_mmb_just_pressed = False
        self.is_lmb_just_released = False
        self.is_rmb_just_released = False
        self.is_mmb_just_released = False

        # REMOVE IN BUILD
        self.is_0_just_pressed = False
        self.is_9_just_pressed = False
        self.is_0_just_released = False
        self.is_9_just_released = False
