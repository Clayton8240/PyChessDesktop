import pygame
import os
from .synthesizer import SoundSynthesizer

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.enabled = True
        self.synth = SoundSynthesizer()
        base_path = os.path.join("assets", "sounds")
        sound_keys = [
            'move', 'pawn_move', 'king_move',
            'capture', 'pawn_capture', 'king_capture',
            'game_over', 'defeat', 'hint', 'undo', 'menu'
        ]
        for name in sound_keys:
            self.sounds[name] = self._get_synthetic_sound(name)

    def _get_synthetic_sound(self, name):
        if name == 'move': return self.synth.make_move_sound()
        if name == 'pawn_move': return self.synth.make_pawn_move_sound()
        if name == 'king_move': return self.synth.make_king_move_sound()
        if name == 'capture': return self.synth.make_capture_sound()
        if name == 'pawn_capture': return self.synth.make_pawn_capture_sound()
        if name == 'king_capture': return self.synth.make_king_capture_sound()
        if name == 'game_over': return self.synth.make_notify_sound()
        if name == 'defeat': return self.synth.make_defeat_sound()
        if name == 'hint': return self.synth.make_hint_sound()
        if name == 'undo': return self.synth.make_undo_sound()
        if name == 'menu': return self.synth.make_menu_sound()
        return None

    def play(self, sound_name):
        if self.enabled and sound_name in self.sounds:
            self.sounds[sound_name].play()

    def set_volume(self, volume):
        """Volume de 0.0 a 1.0"""
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
