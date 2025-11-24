import pygame
import os

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.enabled = True
        try:
            base_path = os.path.join("assets", "sounds")
            self.sounds['move'] = pygame.mixer.Sound(os.path.join(base_path, 'move.wav'))
            self.sounds['capture'] = pygame.mixer.Sound(os.path.join(base_path, 'capture.wav'))
            self.sounds['game_over'] = pygame.mixer.Sound(os.path.join(base_path, 'notify.wav'))
        except Exception as e:
            print(f"Aviso: Sons não puderam ser carregados. {e}")
            self.enabled = False

    def play(self, sound_name):
        if self.enabled and sound_name in self.sounds:
            self.sounds[sound_name].play()
