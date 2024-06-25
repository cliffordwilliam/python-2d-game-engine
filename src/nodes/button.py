from constants import FONT
from constants import NATIVE_RECT
from constants import pg
from nodes.curtain import Curtain
from typeguard import typechecked


@typechecked
class Button:
    """
    Needs to be inside a button container.

    Parameters:
    - surf_size_tuple: button surf.
    - topleft: button rect topleft.
    - text: button text.
    - text_topleft: relative to button rect.
    - description_text: text near screen bottom.

    Update:
    - Active curtain.

    Draw:
    - description.
    - surf.
    - active curtain.

    States:
    - INACTIVE.
    - ACTIVE.
    """

    # Inactive colors.
    BUTTON_INACTIVE_BODY_COLOR: str = "#000f28"
    BUTTON_INACTIVE_LINE_COLOR: str = "#004a89"
    BUTTON_INACTIVE_TEXT_COLOR: str = "#bac3d2"

    # Active colors.
    BUTTON_ACTIVE_BODY_COLOR: str = "#126a9c"
    BUTTON_ACTIVE_LINE_COLOR: str = "#1896ea"
    BUTTON_ACTIVE_TEXT_COLOR: str = "#feffff"

    DESCRIPTION_TEXT_BOTTOM_PADDING: int = 2

    # States.
    INACTIVE: int = 0
    ACTIVE: int = 1

    def __init__(
        self,
        surf_size_tuple: tuple[int, int],
        topleft: tuple[int, int],
        text: str,
        text_topleft: tuple[int, int],
        description_text: str,
    ):
        # Create surf.
        self.surf: pg.Surface = pg.Surface(surf_size_tuple)
        self.surf.fill(self.BUTTON_INACTIVE_BODY_COLOR)

        # Get surf rect.
        self.rect: pg.Rect = self.surf.get_rect()
        # Position rect with topleft.
        self.rect.topleft = topleft

        # Draw decor on surf
        pg.draw.line(
            self.surf,
            self.BUTTON_INACTIVE_LINE_COLOR,
            (0, 0),
            (0, self.rect.height),
        )

        # Get text and position it relative to rect.
        self.text: str = text
        self.text_top_left: tuple[int, int] = text_topleft
        # Draw text to surf.
        FONT.render_to(
            self.surf,
            self.text_top_left,
            self.text,
            self.BUTTON_INACTIVE_TEXT_COLOR,
        )

        # Create active curtain surf.
        self.active_curtain_duration: float = 300.0
        self.active_curtain_start: int = Curtain.INVISIBLE
        self.active_curtain_max_alpha: int = 225
        self.active_curtain_is_invisible: bool = False
        self.active_curtain: Curtain = Curtain(
            self.active_curtain_duration,
            self.active_curtain_start,
            self.active_curtain_max_alpha,
            (self.rect.width + 1, self.rect.height),
            self.active_curtain_is_invisible,
            self.BUTTON_ACTIVE_BODY_COLOR,
        )
        self.active_curtain.rect.topright = self.rect.topright
        # Draw decor on active curtain surf.
        pg.draw.line(
            self.active_curtain.surf,
            self.BUTTON_ACTIVE_TEXT_COLOR,
            (0, 0),
            (0, self.rect.height),
        )
        pg.draw.line(
            self.active_curtain.surf,
            self.BUTTON_ACTIVE_LINE_COLOR,
            (1, 0),
            (1, self.rect.height),
        )
        # Draw font on active curtain surf.
        FONT.render_to(
            self.active_curtain.surf,
            self.text_top_left,
            self.text,
            self.BUTTON_ACTIVE_TEXT_COLOR,
        )

        # Get description text.
        self.description_text: str = description_text
        # Get description rect.
        self.description_text_rect: pg.Rect = FONT.get_rect(
            self.description_text
        )
        # Position description rect.
        self.description_text_rect.center = NATIVE_RECT.center
        self.description_text_rect.bottom = NATIVE_RECT.bottom
        self.description_text_rect.y -= self.DESCRIPTION_TEXT_BOTTOM_PADDING

        # Set initial state to INACTIVE.
        self.initial_state: int = self.INACTIVE
        self.state: int = self.initial_state

    def update(self, dt: int) -> None:
        """
        Update:
        - active_curtain
        """

        self.active_curtain.update(dt)

    def draw(self, surf: pg.Surface, y_offset: int) -> None:
        """
        Draw:
        - description.
        - surf.
        - active curtain.
        """

        # Draw my description if I am active
        if self.state == self.ACTIVE:
            FONT.render_to(
                surf,
                self.description_text_rect,
                self.description_text,
                self.BUTTON_ACTIVE_TEXT_COLOR,
            )

        # Draw my surf.
        surf.blit(self.surf, (self.rect.x, self.rect.y + y_offset))

        # Draw my active surf.
        self.active_curtain.draw(surf, y_offset)

    def set_state(self, value: int) -> None:
        """
        State setter and cleanup.
        """

        old_state: int = self.state
        self.state = value

        # From INACTIVE?
        if old_state == self.INACTIVE:
            # To ACTIVE?
            if self.state == self.ACTIVE:
                # Active surf go to opaque.
                self.active_curtain.go_to_opaque()

        # From ACTIVE?
        elif old_state == self.ACTIVE:
            # To INACTIVE?
            if self.state == self.INACTIVE:
                # Active surf go to invisible.
                self.active_curtain.go_to_invisible()
