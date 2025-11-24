import math
# --- Barra de Avaliação Visual ---
class EvaluationBar:
	def __init__(self, rect):
		self.rect = rect
		self.target_score = 0
		self.visual_score = 0
		self.max_score = 2000
		self.is_flipped = False  # NOVO: Estado de rotação

	def set_flip(self, flip):
		"""Define se a barra deve ser invertida visualmente."""
		self.is_flipped = flip

	def update(self, current_eval):
		# Limita visualmente para não quebrar o gráfico em mates forçados
		if current_eval > 20000: current_eval = self.max_score
		if current_eval < -20000: current_eval = -self.max_score
		self.target_score = current_eval
		# Animação suave (LERP)
		self.visual_score += (self.target_score - self.visual_score) * 0.1

	def draw(self, screen):
		import pygame
		# 1. Desenha fundo (Preto)
		pygame.draw.rect(screen, (40, 40, 40), self.rect)
		# 2. Calcula porcentagem das BRANCAS
		# Score 0 = 0.5 (50%)
		percent = 0.5 + (self.visual_score / (2 * self.max_score))
		percent = max(0.0, min(1.0, percent))
		white_height = int(self.rect.height * percent)
		# 3. Desenha a parte Branca (AQUI ESTÁ A MÁGICA DO FLIP)
		if self.is_flipped:
			# Se virado (Pretas embaixo): Brancas ficam no TOPO
			white_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, white_height)
		else:
			# Normal (Brancas embaixo): Brancas ficam no FUNDO
			white_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height - white_height, self.rect.width, white_height)
		pygame.draw.rect(screen, (240, 240, 240), white_rect)
		# 4. Linha do meio (Empate) e Borda
		mid_y = self.rect.y + (self.rect.height // 2)
		pygame.draw.line(screen, (100, 100, 100), (self.rect.x, mid_y), (self.rect.x + self.rect.width, mid_y), 2)
		pygame.draw.rect(screen, (100, 100, 100), self.rect, 2) # Borda da barra
import math # Importante para a animação suave
class PieceAnimation:
	def __init__(self, start_pos, end_pos, image, duration=250):
		self.start_x, self.start_y = start_pos
		self.end_x, self.end_y = end_pos
		self.image = image
		self.duration = duration
		self.start_time = pygame.time.get_ticks()
		self.finished = False
		self.current_x = self.start_x
		self.current_y = self.start_y

	def update(self):
		now = pygame.time.get_ticks()
		elapsed = now - self.start_time
		t = min(elapsed / self.duration, 1.0)
		t = 1 - pow(1 - t, 3)  # Ease-out cubic
		if t >= 1.0:
			self.finished = True
			self.current_x = self.end_x
			self.current_y = self.end_y
		else:
			self.current_x = self.start_x + (self.end_x - self.start_x) * t
			self.current_y = self.start_y + (self.end_y - self.start_y) * t

	def draw(self, screen):
		screen.blit(self.image, (self.current_x, self.current_y))

# Interface gráfica e input de texto
import pygame

# Paleta de cores madeira clássica

# --- Temas de Tabuleiro ---
THEMES = {
	'classico': {
		'light': (222, 184, 135),  # Burlywood
		'dark': (139, 69, 19),     # SaddleBrown
	},
	'torneio': {
		'light': (240, 217, 181),  # Creme (Chess.com)
		'dark': (120, 154, 100),   # Verde (Chess.com)
	},
	'dark': {
		'light': (60, 60, 80),     # Cinza escuro
		'dark': (0, 180, 255),     # Azul Neon
	},
	'retro': {
		'light': (255, 255, 255),  # Branco puro
		'dark': (0, 0, 0),         # Preto puro
	},
}
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
		def draw_arrow(self, move, color=(0, 255, 0)):
			"""Desenha uma seta do movimento sobre o tabuleiro."""
			start_sq = move.from_square
			end_sq = move.to_square
			
			# Coordenadas Lógicas
			c1 = chess.square_file(start_sq)
			r1 = 7 - chess.square_rank(start_sq)
			c2 = chess.square_file(end_sq)
			r2 = 7 - chess.square_rank(end_sq)
			
			# Ajuste Flip
			if self.is_flipped:
				c1, r1 = 7-c1, 7-r1
				c2, r2 = 7-c2, 7-r2
				
			# Coordenadas em Pixels (Centro da casa)
			offset = self.sq_size // 2
			start = (c1 * self.sq_size + offset, r1 * self.sq_size + offset)
			end = (c2 * self.sq_size + offset, r2 * self.sq_size + offset)
			
			# Desenha a Linha
			pygame.draw.line(self.screen, color, start, end, 6)
			
			# Desenha a Ponta (Trigonometria)
			rotation = math.atan2(start[1] - end[1], end[0] - start[0]) + math.pi/2
			rad = 20 # Tamanho da ponta
			p1 = (end[0] + rad * math.sin(rotation - math.pi/6), end[1] + rad * math.cos(rotation - math.pi/6))
			p2 = (end[0] + rad * math.sin(rotation + math.pi/6), end[1] + rad * math.cos(rotation + math.pi/6))
			pygame.draw.polygon(self.screen, color, [end, p1, p2])
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
					# Corrige para flip do tabuleiro
					if self.is_flipped:
						draw_col = 7 - dest_col
						draw_row = 7 - dest_row
					else:
						draw_col = dest_col
						draw_row = dest_row
					self.screen.blit(surface, (draw_col * self.sq_size, draw_row * self.sq_size))
		def __init__(self, screen, tamanho_quadrado=80, tema='classico'):
			self.screen = screen
			self.sq_size = tamanho_quadrado
			self.images = {}
			self._carregar_imagens()
			self.active_animation = None
			self.animating_dest_square = None
			self.is_flipped = False
			self.tema = tema
			self.tema_cores = THEMES.get(tema, THEMES['classico'])

		def set_tema(self, tema):
			self.tema = tema
			self.tema_cores = THEMES.get(tema, THEMES['classico'])

		def set_flip(self, flip):
			self.is_flipped = flip
		def animate_move(self, move, board):
			piece = board.piece_at(move.from_square)
			if not piece:
				return
			img = self.images.get((piece.piece_type, piece.color))
			if not img:
				return

			# 1. Calcula coordenadas lógicas (Padrão: Brancas embaixo)
			col_from = chess.square_file(move.from_square)
			row_from = 7 - chess.square_rank(move.from_square)
			col_to = chess.square_file(move.to_square)
			row_to = 7 - chess.square_rank(move.to_square)

			# 2. Aplica o Flip se necessário (Inverte espelhado)
			if self.is_flipped:
				start_col = 7 - col_from
				start_row = 7 - row_from
				end_col = 7 - col_to
				end_row = 7 - row_to
			else:
				start_col = col_from
				start_row = row_from
				end_col = col_to
				end_row = row_to

			# 3. Converte para Pixels
			start_pos = (start_col * self.sq_size, start_row * self.sq_size)
			end_pos = (end_col * self.sq_size, end_row * self.sq_size)

			self.active_animation = PieceAnimation(start_pos, end_pos, img)
			self.animating_dest_square = move.to_square

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
			# Atualiza o estado da animação (se houver)
			if self.active_animation:
				self.active_animation.update()
				if self.active_animation.finished:
					self.active_animation = None
					self.animating_dest_square = None

			# 1. Desenha o Grid
			for r in range(8):
				for c in range(8):
					draw_c = 7 - c if self.is_flipped else c
					draw_r = 7 - r if self.is_flipped else r
					# Escolhe cor do tema
					if self.tema == 'retro':
						# Pixelado: desenha quadrados "pixel" (8x8)
						color = self.tema_cores['light'] if (r + c) % 2 == 0 else self.tema_cores['dark']
						rect = pygame.Rect(draw_c * self.sq_size, draw_r * self.sq_size, self.sq_size, self.sq_size)
						for y in range(0, self.sq_size, 10):
							for x in range(0, self.sq_size, 10):
								pygame.draw.rect(self.screen, color, (rect.x + x, rect.y + y, 10, 10))
					else:
						color = self.tema_cores['light'] if (r + c) % 2 == 0 else self.tema_cores['dark']
						rect = pygame.Rect(draw_c * self.sq_size, draw_r * self.sq_size, self.sq_size, self.sq_size)
						pygame.draw.rect(self.screen, color, rect)

			# 2. Desenha as Peças
			for square in chess.SQUARES:
				# Se uma animação está acontecendo indo para ESTA casa, não desenha a peça estática
				if self.animating_dest_square is not None and square == self.animating_dest_square:
					continue
				piece = board.piece_at(square)
				if piece:
					col = chess.square_file(square)
					row = 7 - chess.square_rank(square)
					# Flip visual
					draw_col = 7 - col if self.is_flipped else col
					draw_row = 7 - row if self.is_flipped else row
					img = self.images.get((piece.piece_type, piece.color))
					if img:
						self.screen.blit(img, (draw_col * self.sq_size, draw_row * self.sq_size))

			# 3. Desenha a Peça Animada por cima de tudo
			if self.active_animation:
				self.active_animation.draw(self.screen)
	# --- Cores padrão para LeaderboardView (Ranking) ---
WOOD_LIGHT = (240, 217, 181)
WOOD_DARK = (181, 136, 99)
