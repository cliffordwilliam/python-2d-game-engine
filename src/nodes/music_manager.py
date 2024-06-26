import os

from constants import pg
from typeguard import typechecked


@typechecked
class MusicManager:
    """
    Background music player.
    TODO: refactor this.
    """

    def __init__(self) -> None:
        pg.mixer.init()
        self.current_music_path: str = ""

    def set_current_music_path(self, path: str) -> None:
        """
        Set current_music_path.
        """

        if os.path.exists(path):
            self.current_music_path = path
        else:
            print(f"Error: Music file {path} does not exist.")

    def play_music(self, loops: int, start: float, fade_ms: int) -> None:
        """
        Load and play.
        """

        if self.current_music_path:
            pg.mixer.music.load(self.current_music_path)
            pg.mixer.music.play(loops, start, fade_ms)
        else:
            print("No music loaded to play.")

    def fade_out_music(self, duration: int) -> None:
        """
        Fade out and then stop the music.
        """

        pg.mixer.music.fadeout(duration)

    def stop_music(self) -> None:
        """
        Stop the music.
        """

        pg.mixer.music.stop()

    def pause_music(self) -> None:
        """
        Pause the music.
        """

        pg.mixer.music.pause()

    def unpause_music(self) -> None:
        """
        Unpause the music.
        """

        pg.mixer.music.unpause()

    def set_music_volume(self, volume: float) -> None:
        """
        Set the volume for the music.
        Volume should be a float between 0.0 and 1.0.
        """

        pg.mixer.music.set_volume(volume)
