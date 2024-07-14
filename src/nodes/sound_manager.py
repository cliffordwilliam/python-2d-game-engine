from os.path import exists

from constants import pg
from typeguard import typechecked


@typechecked
class SoundManager:
    """
    Plays sound effects.
    """

    def __init__(self) -> None:
        pg.mixer.init()
        self.sounds: dict[str, pg.mixer.Sound] = {}
        self.channels: list[pg.mixer.Channel] = [pg.mixer.Channel(i) for i in range(pg.mixer.get_num_channels())]

    def load_sound(self, name: str, path: str) -> None:
        """
        Load a sound and add it to the sound dictionary.
        """

        if exists(path):
            self.sounds[name] = pg.mixer.Sound(path)
        else:
            print(f"Error: Sound file {path} does not exist.")

    def play_sound(self, name: str, loops: int, maxtime: int, fade_ms: int) -> None:
        """
        Play a sound by its name.
        """

        if name in self.sounds:
            sound = self.sounds[name]
            channel = self._get_free_channel()
            if channel:
                channel.play(sound, loops, maxtime, fade_ms)
            else:
                print("No available channel to play sound.")
        else:
            print(f"Sound '{name}' not found.")

    def set_volume(self, name: str, volume: float) -> None:
        """
        Set the volume for a sound.
        Volume should be a float between 0.0 and 1.0.
        """

        if name in self.sounds:
            self.sounds[name].set_volume(volume)
        else:
            print(f"Sound '{name}' not found.")

    def _get_free_channel(self) -> None | pg.mixer.Channel:
        """
        Get the first available channel.
        """

        for channel in self.channels:
            if not channel.get_busy():
                return channel
        return None

    def stop_all_sounds(self) -> None:
        """
        Stop all sounds.
        """

        pg.mixer.stop()
