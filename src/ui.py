
# Interface gráfica e input de texto
import pygame

# Paleta de cores madeira clássica
WOOD_LIGHT = (222, 184, 135)  # Burlywood
WOOD_DARK = (139, 69, 19)     # SaddleBrown
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (60, 60, 60)

class TextInput:
	"""
	Caixa de texto customizada para input de nome.
	- Captura eventos KEYDOWN
	- Limita caracteres
	- Renderiza texto e cursor piscante
	"""
	def __init__(self, font, max_length=12, rect=None):
		self.text = ""
		self.font = font
		self.max_length = max_length
		self.active = True
		self.rect = rect or pygame.Rect(100, 100, 300, 50)
		self.cursor_visible = True
		self.cursor_timer = 0
		self.cursor_interval = 500  # ms

	def handle_event(self, event):
		if event.type == pygame.KEYDOWN and self.active:
			if event.key == pygame.K_BACKSPACE:
				self.text = self.text[:-1]
			elif event.key == pygame.K_RETURN:
				return 'submit'
			elif len(self.text) < self.max_length and event.unicode.isprintable():
				self.text += event.unicode
		return None

	def update(self, dt):
		self.cursor_timer += dt
		if self.cursor_timer >= self.cursor_interval:
			self.cursor_visible = not self.cursor_visible
			self.cursor_timer = 0

	def draw(self, surface):
		pygame.draw.rect(surface, GRAY, self.rect, border_radius=8)
		txt_surf = self.font.render(self.text, True, WHITE)
		surface.blit(txt_surf, (self.rect.x + 10, self.rect.y + 10))
		# Cursor
		if self.active and self.cursor_visible:
			cursor_x = self.rect.x + 10 + txt_surf.get_width() + 2
			cursor_y = self.rect.y + 10
			cursor_h = txt_surf.get_height()
			pygame.draw.line(surface, WHITE, (cursor_x, cursor_y), (cursor_x, cursor_y + cursor_h), 2)


class LeaderboardView:
	"""
	Renderiza o Top 10 de recordes na tela.
	"""
	def __init__(self, font, scores):
		self.font = font
		self.scores = scores  # lista de dicts: {name, score, time}

	def draw(self, surface, pos=(100, 100)):
		x, y = pos
		title = self.font.render("TOP 10 RECORDES", True, WOOD_DARK)
		surface.blit(title, (x, y))
		y += title.get_height() + 10
		for idx, entry in enumerate(self.scores):
			line = f"{idx+1:2d}. {entry['name']:<12}  {entry['score']:>5}  {entry['time']}"
			color = WOOD_LIGHT if idx % 2 == 0 else WOOD_DARK
			txt = self.font.render(line, True, color)
			surface.blit(txt, (x, y))
			y += txt.get_height() + 2


import os
import chess

class DisplayBoard:
	def draw_valid_moves(self, board, selected_square):
		if selected_square is None:
			return

		# Cria uma superfície transparente para as bolinhas
		surface = pygame.Surface((self.sq_size, self.sq_size), pygame.SRCALPHA)
		color = (50, 50, 50, 100)  # Cinza escuro semi-transparente
		radius = int(self.sq_size * 0.15)
		center = int(self.sq_size / 2)
		pygame.draw.circle(surface, color, (center, center), radius)

		# Itera sobre todos os movimentos legais para achar os da peça selecionada
		for move in board.legal_moves:
			if move.from_square == selected_square:
				dest_col = chess.square_file(move.to_square)
				dest_row = 7 - chess.square_rank(move.to_square)
				self.screen.blit(surface, (dest_col * self.sq_size, dest_row * self.sq_size))
	def __init__(self, screen, tamanho_quadrado=80):
		self.screen = screen
		self.sq_size = tamanho_quadrado
		self.images = {}
		self._carregar_imagens()

	def _carregar_imagens(self):
		# Mapeia peças do python-chess para nomes de arquivos
		pieces = {chess.PAWN: 'p', chess.ROOK: 'r', chess.KNIGHT: 'n',
				  chess.BISHOP: 'b', chess.QUEEN: 'q', chess.KING: 'k'}
		base_path = os.path.join("assets", "images", "pieces")
		for piece_type, char in pieces.items():
			for color, prefix in [(chess.WHITE, 'w'), (chess.BLACK, 'b')]:
				filename = f"{prefix}_{char}.png"
				try:
					img = pygame.image.load(os.path.join(base_path, filename))
					img = pygame.transform.scale(img, (self.sq_size, self.sq_size))
					self.images[(piece_type, color)] = img
				except FileNotFoundError:
					print(f"Erro: Imagem {filename} não encontrada.")

	def draw(self, board):
		# 1. Desenha o Grid
		for r in range(8):
			for c in range(8):
				color = WOOD_LIGHT if (r + c) % 2 == 0 else WOOD_DARK
				rect = pygame.Rect(c * self.sq_size, r * self.sq_size, self.sq_size, self.sq_size)
				pygame.draw.rect(self.screen, color, rect)
		# 2. Desenha as Peças
		for square in chess.SQUARES:
			piece = board.piece_at(square)
			if piece:
				col = chess.square_file(square)
				row = 7 - chess.square_rank(square)
				img = self.images.get((piece.piece_type, piece.color))
				if img:
					self.screen.blit(img, (col * self.sq_size, row * self.sq_size))
