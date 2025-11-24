import sys
import pygame
import chess
from src.config import *
from src.ui import TextInput, LeaderboardView, DisplayBoard
from src.engine import Engine
from src.scoring import ScoreManager
from src.ai import movimento_aleatorio

# Função auxiliar para calcular material (insira aqui ou no engine.py)
def calcular_material(board, is_white_player):
    valores = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
    pontos = 0
    cor_jogador = chess.WHITE if is_white_player else chess.BLACK
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == cor_jogador and piece.piece_type != chess.KING:
            pontos += valores.get(piece.piece_type, 0)
    return pontos

# Estados do Jogo
ESTADO_MENU = 0
ESTADO_ESCOLHA_COR = 1
ESTADO_JOGANDO = 2
ESTADO_INPUT_NOME = 3
ESTADO_RANKING = 4

def main():
    pygame.init()
    screen = pygame.display.set_mode((840, 640)) # 80px * 8 casas + painel lateral
    pygame.display.set_caption("PyChess Desktop")
    clock = pygame.time.Clock()
    
    # Inicialização
    engine = Engine()
    engine.start()
    
    score_manager = ScoreManager()
    display_board = DisplayBoard(screen, tamanho_quadrado=80)
    input_nome = TextInput(pygame.font.SysFont("consolas", 30), rect=pygame.Rect(170, 300, 300, 50))
    
    estado_atual = ESTADO_MENU

    # Variáveis de controle
    selecionado = None
    aguardando_ia = False
    pontuacao_final = 0
    tempo_decorrido = 0
    jogador_brancas = True  # True = jogador é brancas, False = jogador é pretas
    
    while True:
        dt = clock.tick(60)
        eventos = pygame.event.get()

        # --- Botões do menu ---
        btn_novo = pygame.Rect(260, 250, 320, 50)
        btn_pont = pygame.Rect(260, 320, 320, 50)
        btn_brancas = pygame.Rect(180, 250, 220, 50)
        btn_pretas = pygame.Rect(420, 250, 220, 50)

        for event in eventos:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # --- Menu Inicial ---
            if estado_atual == ESTADO_MENU:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        selecionado = None
                        aguardando_ia = False
                        estado_atual = ESTADO_ESCOLHA_COR
                    elif event.key == pygame.K_2:
                        estado_atual = ESTADO_RANKING
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_novo.collidepoint(event.pos):
                        selecionado = None
                        aguardando_ia = False
                        estado_atual = ESTADO_ESCOLHA_COR
                    elif btn_pont.collidepoint(event.pos):
                        estado_atual = ESTADO_RANKING

            # --- Tela de escolha de cor ---
            elif estado_atual == ESTADO_ESCOLHA_COR:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_b:
                        jogador_brancas = True
                        estado_atual = ESTADO_JOGANDO
                    elif event.key == pygame.K_p:
                        jogador_brancas = False
                        estado_atual = ESTADO_JOGANDO
                        if engine.board.turn == chess.WHITE:
                            move = movimento_aleatorio(engine.board)
                            if move:
                                engine.board.push(move)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_brancas.collidepoint(event.pos):
                        jogador_brancas = True
                        engine.start()
                        selecionado = None
                        aguardando_ia = False
                        estado_atual = ESTADO_JOGANDO
                    elif btn_pretas.collidepoint(event.pos):
                        jogador_brancas = False
                        engine.start()
                        selecionado = None
                        aguardando_ia = False
                        estado_atual = ESTADO_JOGANDO
                        if engine.board.turn == chess.WHITE:
                            move = movimento_aleatorio(engine.board)
                            if move:
                                engine.board.push(move)

            # --- Lógica de Input de Nome ---
            elif estado_atual == ESTADO_INPUT_NOME:
                resultado = input_nome.handle_event(event)
                if resultado == 'submit':
                    # Salva e vai para o Ranking
                    score_manager.save_score(input_nome.text, pontuacao_final, f"{tempo_decorrido//60:02d}:{tempo_decorrido%60:02d}")
                    estado_atual = ESTADO_RANKING

            # --- Lógica do Jogo ---
            elif estado_atual == ESTADO_JOGANDO and not aguardando_ia:
                # Só permite jogada do jogador se for a vez da sua cor
                if (engine.board.turn == (chess.WHITE if jogador_brancas else chess.BLACK)):
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mouse_x, mouse_y = event.pos
                        col = mouse_x // display_board.sq_size
                        row = 7 - (mouse_y // display_board.sq_size)
                        square = chess.square(col, row)

                        if selecionado is None:
                            # Tenta selecionar peça do jogador (da cor escolhida)
                            piece = engine.board.piece_at(square)
                            if piece and piece.color == (chess.WHITE if jogador_brancas else chess.BLACK):
                                selecionado = square
                        else:
                            # Tenta mover
                            move = chess.Move(selecionado, square)
                            # Verifica promoções (simples: promove para Rainha automaticamente)
                            if engine.board.piece_at(selecionado).piece_type == chess.PAWN and chess.square_rank(square) == (7 if jogador_brancas else 0):
                                move = chess.Move(selecionado, square, promotion=chess.QUEEN)

                            if move in engine.board.legal_moves and engine.board.piece_at(selecionado).color == (chess.WHITE if jogador_brancas else chess.BLACK):
                                engine.board.push(move)
                                selecionado = None
                                aguardando_ia = True # Passa a vez
                            else:
                                # Se clicou errado ou em outra peça sua, reseta/troca seleção
                                piece = engine.board.piece_at(square)
                                if piece and piece.color == (chess.WHITE if jogador_brancas else chess.BLACK):
                                    selecionado = square
                                else:
                                    selecionado = None

                    # Atalho para testar fim de jogo (ESPAÇO)
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        engine.stop()
                        pontuacao_final = 1000 # Teste
                        estado_atual = ESTADO_INPUT_NOME

        # --- Atualizações de Lógica (IA e Estado) ---
        if estado_atual == ESTADO_JOGANDO:
            if engine.is_game_over():
                engine.stop()
                tempo_decorrido = engine.get_game_duration()
                vencedor_cor = engine.get_winner()
                venceu = (vencedor_cor == ('white' if jogador_brancas else 'black'))

                material = calcular_material(engine.board, jogador_brancas)
                pontuacao_final = score_manager.calcular_pontuacao(venceu, material, tempo_decorrido)

                if score_manager.check_is_highscore(pontuacao_final):
                    input_nome.text = ""
                    input_nome.active = True
                    estado_atual = ESTADO_INPUT_NOME
                else:
                    estado_atual = ESTADO_RANKING
            # IA Joga (cor oposta ao jogador)
            elif aguardando_ia:
                move = movimento_aleatorio(engine.board)
                if move:
                    engine.board.push(move)
                aguardando_ia = False

        # --- Renderização ---
        screen.fill((40, 40, 40)) # Fundo cinza escuro

        if estado_atual == ESTADO_MENU:
            fonte = pygame.font.SysFont("arial", 40)
            screen.fill((40, 40, 40))
            titulo = fonte.render("PyChess Desktop", True, (255, 255, 255))
            screen.blit(titulo, (220, 120))
            fonte2 = pygame.font.SysFont("arial", 28)
            # Botão Novo Jogo
            pygame.draw.rect(screen, (80, 120, 60), btn_novo, border_radius=12)
            opt1 = fonte2.render("Novo Jogo", True, (255, 255, 255))
            screen.blit(opt1, (btn_novo.x + 60, btn_novo.y + 10))
            # Botão Pontuações
            pygame.draw.rect(screen, (120, 80, 60), btn_pont, border_radius=12)
            opt2 = fonte2.render("Pontuações", True, (255, 255, 255))
            screen.blit(opt2, (btn_pont.x + 60, btn_pont.y + 10))
        elif estado_atual == ESTADO_ESCOLHA_COR:
            fonte = pygame.font.SysFont("arial", 32)
            screen.fill((40, 40, 40))
            msg = fonte.render("Escolha sua cor:", True, (255, 255, 255))
            screen.blit(msg, (270, 170))
            fonte2 = pygame.font.SysFont("arial", 28)
            # Botão Brancas
            pygame.draw.rect(screen, (220, 220, 220), btn_brancas, border_radius=12)
            txt_b = fonte2.render("Brancas", True, (60, 60, 60))
            screen.blit(txt_b, (btn_brancas.x + 40, btn_brancas.y + 10))
            # Botão Pretas
            pygame.draw.rect(screen, (40, 40, 40), btn_pretas, border_radius=12)
            pygame.draw.rect(screen, (200, 200, 200), btn_pretas, 2, border_radius=12)
            txt_p = fonte2.render("Pretas", True, (220, 220, 220))
            screen.blit(txt_p, (btn_pretas.x + 50, btn_pretas.y + 10))
        elif estado_atual == ESTADO_JOGANDO:
            display_board.draw(engine.board)
            # Destaque opcional para peça selecionada
            if selecionado is not None:
                x = chess.square_file(selecionado) * 80
                y = (7 - chess.square_rank(selecionado)) * 80
                s = pygame.Surface((80, 80))
                s.set_alpha(100)
                s.fill((255, 255, 0)) # Amarelo transparente
                screen.blit(s, (x, y))
                # Dicas de movimentos válidos
                display_board.draw_valid_moves(engine.board, selecionado)

            # --- Painel lateral ---
            def draw_side_panel():
                panel_x = 640
                panel_w = 200
                # Fundo do painel lateral: tom de madeira escura
                WOOD_PANEL = (160, 110, 60)
                WOOD_CEMETERY_LIGHT = (222, 184, 135)  # igual ao WOOD_LIGHT
                WOOD_CEMETERY_DARK = (139, 69, 19)     # igual ao WOOD_DARK
                pygame.draw.rect(screen, WOOD_PANEL, (panel_x, 0, panel_w, 640))
                fonte = pygame.font.SysFont("arial", 24)
                # Vez do jogador
                vez = "Brancas" if engine.board.turn == chess.WHITE else "Pretas"
                cor = (255,255,255) if engine.board.turn == chess.WHITE else (0,0,0)
                label = fonte.render(f"Vez: {vez}", True, cor)
                screen.blit(label, (panel_x + 30, 30))

                def get_captures(board, color):
                    initial = {chess.PAWN:8, chess.KNIGHT:2, chess.BISHOP:2, chess.ROOK:2, chess.QUEEN:1}
                    current = {chess.PAWN:0, chess.KNIGHT:0, chess.BISHOP:0, chess.ROOK:0, chess.QUEEN:0}
                    for sq in chess.SQUARES:
                        piece = board.piece_at(sq)
                        if piece and piece.color == color and piece.piece_type in current:
                            current[piece.piece_type] += 1
                    return {ptype: initial[ptype] - current[ptype] for ptype in initial}

                capt_b = get_captures(engine.board, chess.BLACK)
                capt_p = get_captures(engine.board, chess.WHITE)

                img_y = 80
                img_size = 40
                # Cemitério Pretas (peças brancas capturadas)
                pygame.draw.rect(screen, WOOD_CEMETERY_DARK, (panel_x+10, img_y-5, 180, img_size+30))
                screen.blit(fonte.render("Cemitério Pretas:", True, (255,255,255)), (panel_x+20, img_y))
                img_y += 30
                for ptype, count in capt_p.items():
                    if count > 0:
                        img = display_board.images.get((ptype, chess.BLACK))
                        if img:
                            img_small = pygame.transform.scale(img, (img_size, img_size))
                            for i in range(count):
                                screen.blit(img_small, (panel_x+20+i*img_size, img_y))
                img_y += img_size + 20

                # Cemitério Brancas (peças pretas capturadas)
                pygame.draw.rect(screen, WOOD_CEMETERY_LIGHT, (panel_x+10, img_y-5, 180, img_size+30))
                screen.blit(fonte.render("Cemitério Brancas:", True, (0,0,0)), (panel_x+20, img_y))
                img_y += 30
                for ptype, count in capt_b.items():
                    if count > 0:
                        img = display_board.images.get((ptype, chess.WHITE))
                        if img:
                            img_small = pygame.transform.scale(img, (img_size, img_size))
                            for i in range(count):
                                screen.blit(img_small, (panel_x+20+i*img_size, img_y))

            draw_side_panel()

        elif estado_atual == ESTADO_INPUT_NOME:
            # Texto explicativo
            fonte = pygame.font.SysFont("arial", 24)
            msg = fonte.render(f"NOVO RECORDE! Pontos: {pontuacao_final}", True, (255, 255, 255))
            screen.blit(msg, (170, 250))
            input_nome.update(dt)
            input_nome.draw(screen)

        elif estado_atual == ESTADO_RANKING:
            scores = score_manager.load_scores()
            view = LeaderboardView(pygame.font.SysFont("consolas", 20), scores)
            view.draw(screen, pos=(150, 100))

            # Instrução para voltar ao menu
            fonte_small = pygame.font.SysFont("arial", 16)
            hint = fonte_small.render("Pressione M para voltar ao menu", True, (150, 150, 150))
            screen.blit(hint, (220, 500))

            # Lógica simples de voltar ao menu
            keys = pygame.key.get_pressed()
            if keys[pygame.K_m]:
                engine.start()
                estado_atual = ESTADO_MENU

        pygame.display.flip()

if __name__ == "__main__":
    main()