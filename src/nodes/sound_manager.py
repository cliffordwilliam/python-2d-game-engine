from typing import Union

from constants import pg
from typeguard import typechecked


@typechecked
class SoundManager:
    def __init__(self) -> None:
        self.sounds: dict[str, pg.mixer.Sound] = {}

    def load_sound(self, name: str, path: str) -> None:
        sound: pg.mixer.Sound = pg.mixer.Sound(path)
        self.sounds[name] = sound

    def play_sound(self, name: str, loop: int = 0) -> None:
        if name in self.sounds:
            self.sounds[name].play(loop)

    def stop_sound(self, name: str) -> None:
        if name in self.sounds:
            self.sounds[name].stop()

    def stop_all_sounds(self) -> None:
        pg.mixer.stop()

    def set_volume(self, name: str, volume: float) -> None:
        if name in self.sounds:
            self.sounds[name].set_volume(volume)

    def get_volume(self, name: str) -> Union[float, None]:
        if name in self.sounds:
            return self.sounds[name].get_volume()
        return None

    def reset_sounds(self) -> None:
        self.sounds = {}
