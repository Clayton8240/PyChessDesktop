
import pygame
import chess

class Engine:
	def __init__(self):
		self.board = chess.Board()
		self.start_time = None
		self.end_time = None
		self.running = False

	def start(self):
		self.start_time = pygame.time.get_ticks()
		self.running = True
		self.end_time = None
		self.board.reset()

	def stop(self):
		self.end_time = pygame.time.get_ticks()
		self.running = False

	def get_game_duration(self):
		if self.start_time is None:
			return 0
		if self.running:
			return (pygame.time.get_ticks() - self.start_time) // 1000
		elif self.end_time:
			return (self.end_time - self.start_time) // 1000
		return 0

	def is_game_over(self):
		return self.board.is_game_over()

	def get_winner(self):
		if not self.is_game_over():
			return None
		result = self.board.result()
		if result == '1-0':
			return 'white'
		elif result == '0-1':
			return 'black'
		else:
			return 'draw'

	# Métodos para integração futura com UI e lógica de movimento
	# def make_move(self, move): ...
	# def get_material(self, color): ...
