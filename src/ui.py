import math
import os
import chess
import pygame

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
WHITE = (255, 255, 255)
GRAY = (60, 60, 60)
WOOD_LIGHT = (240, 217, 181)
WOOD_DARK = (181, 136, 99)

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


class DisplayBoard:
    def __init__(self, screen, tamanho_quadrado=80, skin_data=None):
        self.screen = screen
        self.sq_size = tamanho_quadrado
        
        self.skin_data = skin_data if skin_data else {
            'light': (240, 217, 181), 
            'dark': (181, 136, 99), 
            'path': 'assets/images/pieces'
        }
        
        self.images = {}
        self._carregar_imagens()
        
        self.active_animation = None
        self.animating_dest_square = None
        self.is_flipped = False

    def set_skin(self, skin_data):
        """Troca a skin e recarrega as imagens."""
        self.skin_data = skin_data
        self.images = {}
        self._carregar_imagens()

    def _carregar_imagens(self):
        pieces = {chess.PAWN: 'p', chess.ROOK: 'r', chess.KNIGHT: 'n',
                  chess.BISHOP: 'b', chess.QUEEN: 'q', chess.KING: 'k'}
        
        base_path = self.skin_data.get('path', 'assets/images/pieces')
        
        for piece_type, char in pieces.items():
            for color, prefix in [(chess.WHITE, 'w'), (chess.BLACK, 'b')]:
                filename = f"{prefix}_{char}.png"
                
                full_path = os.path.join(base_path, filename)
                
                if not os.path.exists(full_path):
                    full_path = os.path.join('assets/images/pieces', filename)

                try:
                    img = pygame.image.load(full_path)
                    img = pygame.transform.scale(img, (self.sq_size, self.sq_size))
                    self.images[(piece_type, color)] = img
                except FileNotFoundError:
                    print(f"ERRO CRÍTICO: Imagem {filename} não encontrada nem na skin nem no padrão.")

    def draw(self, board):
        if self.active_animation:
            self.active_animation.update()
            if self.active_animation.finished:
                self.active_animation = None
                self.animating_dest_square = None

        light_c = self.skin_data['light']
        dark_c = self.skin_data['dark']
        
        for r in range(8):
            for c in range(8):
                draw_c = 7 - c if self.is_flipped else c
                draw_r = 7 - r if self.is_flipped else r
                
                color = light_c if (r + c) % 2 == 0 else dark_c
                rect = pygame.Rect(draw_c * self.sq_size, draw_r * self.sq_size, self.sq_size, self.sq_size)
                pygame.draw.rect(self.screen, color, rect)
        
        for square in chess.SQUARES:
            if self.animating_dest_square is not None and square == self.animating_dest_square:
                continue
            piece = board.piece_at(square)
            if piece:
                col = chess.square_file(square)
                row = 7 - chess.square_rank(square)
                draw_col = 7 - col if self.is_flipped else col
                draw_row = 7 - row if self.is_flipped else row
                img = self.images.get((piece.piece_type, piece.color))
                if img:
                    self.screen.blit(img, (draw_col * self.sq_size, draw_row * self.sq_size))

        if self.active_animation:
            self.active_animation.draw(self.screen)
    
    def draw_arrow(self, move, color=(0, 255, 0), width=6):
        """Desenha uma seta direcional sobre o tabuleiro."""
        start_sq = move.from_square
        end_sq = move.to_square
        
        # 1. Calcula coordenadas lógicas
        c1 = chess.square_file(start_sq)
        r1 = 7 - chess.square_rank(start_sq)
        c2 = chess.square_file(end_sq)
        r2 = 7 - chess.square_rank(end_sq)
        
        # 2. Aplica Flip (se necessário)
        if self.is_flipped:
            c1, r1 = 7-c1, 7-r1
            c2, r2 = 7-c2, 7-r2
            
        # 3. Converte para Pixels (Centro da casa)
        offset = self.sq_size // 2
        start_pos = (c1 * self.sq_size + offset, r1 * self.sq_size + offset)
        end_pos = (c2 * self.sq_size + offset, r2 * self.sq_size + offset)
        
        # 4. Desenha a Linha (Corpo da seta)
        pygame.draw.line(self.screen, color, start_pos, end_pos, width)
        
        # 5. Desenha a Ponta (Triângulo)
        # Calcula o ângulo da linha (em radianos)
        # dx = x2 - x1, dy = y2 - y1
        angle = math.atan2(end_pos[1] - start_pos[1], end_pos[0] - start_pos[0])
        
        arrow_size = 25 # Tamanho da ponta
        arrow_angle = math.pi / 6 # 30 graus de abertura
        
        # Pontos da base do triângulo (calculados retrocedendo a partir do destino)
        # Asa Esquerda
        p1_x = end_pos[0] - arrow_size * math.cos(angle - arrow_angle)
        p1_y = end_pos[1] - arrow_size * math.sin(angle - arrow_angle)
        
        # Asa Direita
        p2_x = end_pos[0] - arrow_size * math.cos(angle + arrow_angle)
        p2_y = end_pos[1] - arrow_size * math.sin(angle + arrow_angle)
        
        # Desenha o triângulo preenchido
        pygame.draw.polygon(self.screen, color, [end_pos, (p1_x, p1_y), (p2_x, p2_y)])

    def draw_valid_moves(self, board, selected_square):
        if selected_square is None:
            return

        surface = pygame.Surface((self.sq_size, self.sq_size), pygame.SRCALPHA)
        color = (50, 50, 50, 100)
        radius = int(self.sq_size * 0.15)
        center = int(self.sq_size / 2)
        pygame.draw.circle(surface, color, (center, center), radius)

        for move in board.legal_moves:
            if move.from_square == selected_square:
                dest_col = chess.square_file(move.to_square)
                dest_row = 7 - chess.square_rank(move.to_square)

                if self.is_flipped:
                    draw_col = 7 - dest_col
                    draw_row = 7 - dest_row
                else:
                    draw_col = dest_col
                    draw_row = dest_row
                self.screen.blit(surface, (draw_col * self.sq_size, draw_row * self.sq_size))

    def set_flip(self, flip):
        self.is_flipped = flip

    def animate_move(self, move, board):
        piece = board.piece_at(move.from_square)
        if not piece:
            return
        img = self.images.get((piece.piece_type, piece.color))
        if not img:
            return

        col_from = chess.square_file(move.from_square)
        row_from = 7 - chess.square_rank(move.from_square)
        col_to = chess.square_file(move.to_square)
        row_to = 7 - chess.square_rank(move.to_square)

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

        start_pos = (start_col * self.sq_size, start_row * self.sq_size)
        end_pos = (end_col * self.sq_size, end_row * self.sq_size)

        self.active_animation = PieceAnimation(start_pos, end_pos, img)
        self.animating_dest_square = move.to_square

class Slider:
    def __init__(self, x, y, w, h, label, initial_pct=0.5, color_bar=(100, 200, 100), display_mode='pct'):
        self.rect = pygame.Rect(x, y, w, h)
        self.pct = initial_pct # 0.0 a 1.0
        self.label = label
        self.dragging = False
        self.color_bar = color_bar
        self.display_mode = display_mode

    def handle_event(self, event):
        updated = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.inflate(10, 10).collidepoint(event.pos):
                self.dragging = True
                self.update_from_mouse(event.pos[0])
                updated = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_from_mouse(event.pos[0])
            updated = True
        return updated

    def update_from_mouse(self, mouse_x):
        rel_x = mouse_x - self.rect.x
        self.pct = max(0.0, min(1.0, rel_x / self.rect.width))

    def draw(self, screen, font):
        # Fundo
        pygame.draw.rect(screen, (60, 60, 60), self.rect, border_radius=5)
        # Preenchimento
        fill_w = int(self.pct * self.rect.width)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
        pygame.draw.rect(screen, self.color_bar, fill_rect, border_radius=5)
        # Bolinha
        pygame.draw.circle(screen, (255, 255, 255), (self.rect.x + fill_w, self.rect.centery), self.rect.height + 2)
        
        # Texto
        if self.display_mode == 'pct':
            text = f"{self.label}: {int(self.pct * 100)}%"
        else: # 'val' for 0-255
            text = f"{self.label}: {int(self.pct * 255)}"
        lbl = font.render(text, True, (220, 220, 220))
        screen.blit(lbl, (self.rect.x, self.rect.y - 25))
