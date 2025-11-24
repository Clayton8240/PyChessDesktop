import pygame
import math
import array

class SoundSynthesizer:
    def __init__(self):
        self.sample_rate = 44100
        self.bits = 16
        pygame.mixer.set_reserved(1) # Garante um canal para nossos bips

    def _generate_wave(self, frequency, duration, volume=0.5, wave_type='sine'):
        """Gera os dados brutos de áudio."""
        n_samples = int(self.sample_rate * duration)
        buf = array.array('h') # 'h' = signed short (16-bit)
        amplitude = int(32767 * volume)
        for i in range(n_samples):
            t = float(i) / self.sample_rate
            if wave_type == 'sine':
                val = math.sin(2 * math.pi * frequency * t)
            elif wave_type == 'square':
                val = 1.0 if math.sin(2 * math.pi * frequency * t) > 0 else -1.0
            elif wave_type == 'sawtooth':
                val = 2.0 * (t * frequency - math.floor(t * frequency + 0.5))
            buf.append(int(val * amplitude))
        return pygame.mixer.Sound(buffer=buf)

    def make_move_sound(self):
        # Movimento padrão (peças)
        return self._generate_wave(frequency=220, duration=0.09, volume=0.28, wave_type='sine')

    def make_pawn_move_sound(self):
        # Movimento de peão (mais "seco")
        return self._generate_wave(frequency=170, duration=0.08, volume=0.22, wave_type='square')

    def make_king_move_sound(self):
        # Movimento do rei (grave e longo)
        return self._generate_wave(frequency=110, duration=0.13, volume=0.32, wave_type='sine')

    def make_capture_sound(self):
        # Captura padrão
        return self._generate_wave(frequency=420, duration=0.13, volume=0.38, wave_type='square')

    def make_pawn_capture_sound(self):
        # Captura de peão (mais curta)
        return self._generate_wave(frequency=320, duration=0.09, volume=0.32, wave_type='square')

    def make_king_capture_sound(self):
        # Captura do rei (grave, "alarme")
        return self._generate_wave(frequency=90, duration=0.25, volume=0.45, wave_type='sawtooth')

    def make_notify_sound(self):
        # Vitória
        return self._generate_wave(frequency=700, duration=0.5, volume=0.5, wave_type='sine')

    def make_defeat_sound(self):
        # Derrota
        return self._generate_wave(frequency=120, duration=0.5, volume=0.5, wave_type='sawtooth')

    def make_hint_sound(self):
        # Dica (bip agudo)
        return self._generate_wave(frequency=900, duration=0.08, volume=0.25, wave_type='sine')

    def make_undo_sound(self):
        n_samples = int(self.sample_rate * 0.3)
        buf = array.array('h')
        amplitude = int(32767 * 0.4)
        for i in range(n_samples):
            t = float(i) / self.sample_rate
            freq_atual = 400 - (300 * (i / n_samples))
            val = math.sin(2 * math.pi * freq_atual * t)
            buf.append(int(val * amplitude))
        return pygame.mixer.Sound(buffer=buf)

    def make_menu_sound(self):
        # Som de menu (clique)
        return self._generate_wave(frequency=500, duration=0.06, volume=0.18, wave_type='sine')
