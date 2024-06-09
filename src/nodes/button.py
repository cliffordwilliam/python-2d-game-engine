# from typing import Callable
from constants import FONT
from constants import NATIVE_SURF
from constants import pg
from typeguard import typechecked


@typechecked
class Button:
    """
    asd
    """

    BUTTON_INACTIVE_BODY_COLOR: str = "#000f28"
    BUTTON_INACTIVE_LINE_COLOR: str = "#004a89"
    BUTTON_INACTIVE_TEXT_COLOR: str = "#bac3d2"

    # TODO: Use curtain to fade in / out active to inactive
    BUTTON_ACTIVE_BODY_COLOR: str = "#126a9c"
    BUTTON_ACTIVE_LINE_COLOR: str = "#1896ea"
    BUTTON_ACTIVE_TEXT_COLOR: str = "#feffff"

    INACTIVE: int = 0
    ACTIVE: int = 1

    def __init__(
        self,
        width: int,
        height: int,
        topleft: tuple[int, int],
        text: str,
        text_topleft: tuple[int, int],
    ):
        self.width: int = width

        self.height: int = height

        self.surf: pg.Surface = pg.Surface((self.width, self.height))

        self.surf.fill(self.BUTTON_INACTIVE_BODY_COLOR)

        pg.draw.line(
            self.surf,
            self.BUTTON_INACTIVE_LINE_COLOR,
            (0, 0),
            (0, self.height),
        )

        self.rect: pg.Rect = self.surf.get_rect()

        self.rect.topleft = topleft

        self.text: str = text

        self.text_top_left: tuple[int, int] = text_topleft

        FONT.render_to(
            self.surf,
            self.text_top_left,
            self.text,
            self.BUTTON_INACTIVE_TEXT_COLOR,
        )

        self.initial_state: int = self.INACTIVE

        self.state: int = self.initial_state

        self.init_state()

    def init_state(self) -> None:
        """
        This is set state for none to initial state.
        """

        self.surf.fill(self.BUTTON_INACTIVE_BODY_COLOR)

        pg.draw.line(
            self.surf,
            self.BUTTON_INACTIVE_LINE_COLOR,
            (0, 0),
            (0, self.height),
        )

        FONT.render_to(
            self.surf,
            self.text_top_left,
            self.text,
            self.BUTTON_INACTIVE_TEXT_COLOR,
        )

    def draw(self) -> None:
        NATIVE_SURF.blit(self.surf, self.rect)

    def set_state(self, value: int) -> None:
        old_state: int = self.state
        self.state = value

        if old_state == self.INACTIVE:
            if self.state == self.ACTIVE:
                self.surf.fill(self.BUTTON_ACTIVE_BODY_COLOR)

                pg.draw.line(
                    self.surf,
                    self.BUTTON_ACTIVE_LINE_COLOR,
                    (0, 0),
                    (0, self.height),
                )

                FONT.render_to(
                    self.surf,
                    self.text_top_left,
                    self.text,
                    self.BUTTON_ACTIVE_TEXT_COLOR,
                )

        elif old_state == self.ACTIVE:
            if self.state == self.INACTIVE:
                self.surf.fill(self.BUTTON_INACTIVE_BODY_COLOR)

                pg.draw.line(
                    self.surf,
                    self.BUTTON_INACTIVE_LINE_COLOR,
                    (0, 0),
                    (0, self.height),
                )

                FONT.render_to(
                    self.surf,
                    self.text_top_left,
                    self.text,
                    self.BUTTON_INACTIVE_TEXT_COLOR,
                )

    # def add_event_listener(self, value: Callable, event: int) -> None:
    #     if event == self.END:
    #         self.listener_end.append(value)

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
