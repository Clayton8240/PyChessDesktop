import pygame
import chess

class Engine:
	def __init__(self):
		self.board = chess.Board()
		self.start_time = None
		self.running = False
		# Atributos de tempo
		self.time_limit = None # None significa "Sem Tempo"
		self.white_time = 0
		self.black_time = 0
		self.winner_on_time = None

	def start(self, time_limit=None):
		"""
		time_limit: Tempo em segundos (ex: 600) ou None para jogo livre.
		"""
		self.start_time = pygame.time.get_ticks()
		self.running = True
		self.board.reset()
		self.time_limit = time_limit
		self.winner_on_time = None
		if self.time_limit is not None:
			self.white_time = float(time_limit)
			self.black_time = float(time_limit)
		else:
			self.white_time = 0
			self.black_time = 0

	def stop(self):
		self.running = False

	def update_timer(self, dt_seconds):
		"""Desconta o tempo apenas se houver um limite definido."""
		if not self.running or self.is_game_over():
			return
		# Se for modo "Sem Tempo", não faz nada
		if self.time_limit is None:
			return
		# Desconta do relógio de quem é a vez
		if self.board.turn == chess.WHITE:
			self.white_time -= dt_seconds
			if self.white_time <= 0:
				self.white_time = 0
				self.winner_on_time = 'black'
				self.stop()
		else:
			self.black_time -= dt_seconds
			if self.black_time <= 0:
				self.black_time = 0
				self.winner_on_time = 'white'
				self.stop()

	def get_game_duration(self):
		if self.start_time is None: return 0
		return (pygame.time.get_ticks() - self.start_time) // 1000

	def is_game_over(self):
		return self.board.is_game_over() or (self.winner_on_time is not None)


