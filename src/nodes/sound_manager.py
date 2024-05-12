from constants import pg


class SoundManager:
    def __init__(self):
        self.sounds: dict[str, pg.mixer.Sound] = {}

    def load_sound(self, name: str, path: str):
        sound: pg.mixer.Sound = pg.mixer.Sound(path)
        self.sounds[name] = sound

    def play_sound(self, name: str, loop=0):
        if name in self.sounds:
            self.sounds[name].play(loop)

    def stop_sound(self, name: str):
        if name in self.sounds:
            self.sounds[name].stop()

    def stop_all_sounds(self):
        pg.mixer.stop()

    def set_volume(self, name: str, volume: float):
        if name in self.sounds:
            self.sounds[name].set_volume(volume)

    def get_volume(self, name: str):
        if name in self.sounds:
            return self.sounds[name].get_volume()
        return None

    def reset_sounds(self):
        self.sounds = {}
