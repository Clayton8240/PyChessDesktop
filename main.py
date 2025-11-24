import sys
import pygame
import chess
from src.config import *
from src.ui import TextInput, LeaderboardView, DisplayBoard
from src.engine import Engine
from src.scoring import ScoreManager
from src.ai import get_best_move
from src.sound import SoundManager

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

# --- Função Auxiliar de Movimento Seguro ---
def realizar_jogada(engine, move, display_board, sound_manager):
    """Executa som, animação e lógica de uma vez só."""
    display_board.animate_move(move, engine.board)
    if engine.board.piece_at(move.to_square) is not None:
        tocar_som_acao(engine.board, move, sound_manager, acao='capture')
    else:
        tocar_som_acao(engine.board, move, sound_manager, acao='move')
    engine.board.push(move)

def tocar_som_acao(board, move, sound_manager, acao='move'):
    """Escolhe o som correto para a ação de acordo com a peça e tipo de jogada."""
    peca = None
    alvo = None
    if move is not None:
        peca = board.piece_at(move.from_square)
        alvo = board.piece_at(move.to_square)
    if acao == 'move':
        if peca:
            if peca.piece_type == chess.PAWN:
                sound_manager.play('pawn_move')
            elif peca.piece_type == chess.KING:
                sound_manager.play('king_move')
            else:
                sound_manager.play('move')
        else:
            sound_manager.play('move')
    elif acao == 'capture':
        if peca:
            if peca.piece_type == chess.PAWN:
                sound_manager.play('pawn_capture')
            elif peca.piece_type == chess.KING:
                sound_manager.play('king_capture')
            else:
                sound_manager.play('capture')
        else:
            sound_manager.play('capture')
    elif acao == 'hint':
        sound_manager.play('hint')
    elif acao == 'menu':
        sound_manager.play('menu')
    elif acao == 'undo':
        sound_manager.play('undo')
    elif acao == 'game_over':
        sound_manager.play('game_over')
    elif acao == 'defeat':
        sound_manager.play('defeat')

# Estados do Jogo
ESTADO_MENU = 0
ESTADO_ESCOLHA_COR = 1
ESTADO_JOGANDO = 2
ESTADO_INPUT_NOME = 3
ESTADO_RANKING = 4

def main():
    pygame.init()
    fonte2 = pygame.font.SysFont("arial", 32, bold=True)
    screen = pygame.display.set_mode((840, 640)) # 80px * 8 casas + painel lateral
    pygame.display.set_caption("PyChess Desktop")
    clock = pygame.time.Clock()

    # Inicialização
    engine = Engine()
    engine.start()

    score_manager = ScoreManager()
    display_board = DisplayBoard(screen, tamanho_quadrado=80)
    input_nome = TextInput(pygame.font.SysFont("consolas", 30), rect=pygame.Rect(170, 300, 300, 50))
    sound_manager = SoundManager()

    estado_atual = ESTADO_MENU

    # Variáveis de controle
    selecionado = None
    aguardando_ia = False
    pontuacao_final = 0
    tempo_decorrido = 0
    jogador_brancas = True  # True = jogador é brancas, False = jogador é pretas
    dificuldade = 2 # Começa no Médio por padrão

    # Variável para armazenar a última dica da IA
    ultima_dica_ia = None

    while True:
        dt = clock.tick(60)
        eventos = pygame.event.get()

        # --- Botões do menu ---
        btn_novo = pygame.Rect(260, 250, 320, 50)
        btn_pont = pygame.Rect(260, 320, 320, 50)
        btn_brancas = pygame.Rect(180, 250, 220, 50)
        btn_pretas = pygame.Rect(420, 250, 220, 50)
        btn_som = pygame.Rect(760, 20, 60, 40)  # Botão de som no canto superior direito

        for event in eventos:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # --- Menu Inicial ---
            if estado_atual == ESTADO_MENU:
                # --- BOTÃO DE SOM ---
                cor_som = (100, 200, 100) if sound_manager.enabled else (200, 100, 100)
                texto_som = "ON" if sound_manager.enabled else "OFF"
                pygame.draw.rect(screen, cor_som, btn_som, border_radius=5)
                pygame.draw.rect(screen, (200, 200, 200), btn_som, 2, border_radius=5)
                lbl_som = fonte2.render("Som", True, (200, 200, 200))
                txt_btn_som = pygame.font.SysFont("arial", 18, bold=True).render(texto_som, True, (255,255,255))
                screen.blit(lbl_som, (btn_som.x - 60, btn_som.y + 5))
                screen.blit(txt_btn_som, (btn_som.x + 15, btn_som.y + 10))
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
                        tocar_som_acao(engine.board, None, sound_manager, acao='menu')
                        estado_atual = ESTADO_ESCOLHA_COR
                    elif btn_pont.collidepoint(event.pos):
                        tocar_som_acao(engine.board, None, sound_manager, acao='menu')
                        estado_atual = ESTADO_RANKING
                    elif btn_som.collidepoint(event.pos):
                        sound_manager.enabled = not sound_manager.enabled
                        if sound_manager.enabled:
                            sound_manager.play('menu')

            # --- Tela de escolha de cor ---
            elif estado_atual == ESTADO_ESCOLHA_COR:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_b:
                        jogador_brancas = True
                        display_board.set_flip(False)
                        tocar_som_acao(engine.board, None, sound_manager, acao='menu')
                        estado_atual = ESTADO_JOGANDO
                    elif event.key == pygame.K_p:
                        jogador_brancas = False
                        display_board.set_flip(True)
                        tocar_som_acao(engine.board, None, sound_manager, acao='menu')
                        estado_atual = ESTADO_JOGANDO
                        if engine.board.turn == chess.WHITE:
                            move = get_best_move(engine.board, dificuldade)
                            if move:
                                engine.board.push(move)
                                tocar_som_acao(engine.board, move, sound_manager, acao='move')
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Botões de dificuldade (4 níveis)
                    w_btn = 90
                    gap = 10
                    start_x = 220
                    r_facil = pygame.Rect(start_x, 150, w_btn, 40)
                    r_medio = pygame.Rect(start_x + w_btn + gap, 150, w_btn, 40)
                    r_dificil = pygame.Rect(start_x + (w_btn + gap)*2, 150, w_btn, 40)
                    r_pro = pygame.Rect(start_x + (w_btn + gap)*3, 150, w_btn, 40)
                    if r_facil.collidepoint(event.pos):
                        dificuldade = 1
                        sound_manager.play('move')
                    elif r_medio.collidepoint(event.pos):
                        dificuldade = 2
                        sound_manager.play('move')
                    elif r_dificil.collidepoint(event.pos):
                        dificuldade = 3
                        sound_manager.play('move')
                    elif r_pro.collidepoint(event.pos):
                        dificuldade = 4
                        sound_manager.play('move')
                    # Botões de cor
                    # Corrige posição dos botões para garantir clique correto
                    btn_brancas.y = 300
                    btn_pretas.y = 300
                    if btn_brancas.collidepoint(event.pos):
                        jogador_brancas = True
                        display_board.set_flip(False)
                        engine.start()
                        selecionado = None
                        aguardando_ia = False
                        tocar_som_acao(engine.board, None, sound_manager, acao='menu')
                        estado_atual = ESTADO_JOGANDO
                    elif btn_pretas.collidepoint(event.pos):
                        jogador_brancas = False
                        display_board.set_flip(True)
                        engine.start()
                        selecionado = None
                        aguardando_ia = False
                        tocar_som_acao(engine.board, None, sound_manager, acao='menu')
                        estado_atual = ESTADO_JOGANDO
                        if engine.board.turn == chess.WHITE:
                            move = get_best_move(engine.board, dificuldade)
                            if move:
                                engine.board.push(move)
                                tocar_som_acao(engine.board, move, sound_manager, acao='move')

            # --- Lógica de Input de Nome ---
            elif estado_atual == ESTADO_INPUT_NOME:
                resultado = input_nome.handle_event(event)
                if resultado == 'submit':
                    # Salva e vai para o Ranking
                    score_manager.save_score(input_nome.text, pontuacao_final, f"{tempo_decorrido//60:02d}:{tempo_decorrido%60:02d}")
                    estado_atual = ESTADO_RANKING

            # --- Lógica do Jogo ---
            elif estado_atual == ESTADO_JOGANDO and not aguardando_ia:
                # --- NOVOS ATALHOS DE TECLADO ---
                if event.type == pygame.KEYDOWN:
                    # 1. DESFAZER (Ctrl + Z)
                    if event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        if len(engine.board.move_stack) >= 2:
                            display_board.active_animation = None
                            display_board.animating_dest_square = None
                            engine.board.pop()
                            engine.board.pop()
                            selecionado = None
                            tocar_som_acao(engine.board, None, sound_manager, acao='undo')
                    # 2. NOVO JOGO (F2)
                    elif event.key == pygame.K_F2:
                        engine.start()
                        selecionado = None
                        aguardando_ia = False
                        sound_manager.play('move')
                        estado_atual = ESTADO_ESCOLHA_COR
                    # 3. AJUDA / DICA (H)
                    elif event.key == pygame.K_h:
                        move = get_best_move(engine.board, dificuldade)
                        if move:
                            selecionado = move.from_square
                            tocar_som_acao(engine.board, move, sound_manager, acao='hint')
                            dica_str = f"Dica: {chess.square_name(move.from_square)} → {chess.square_name(move.to_square)}"
                            ultima_dica_ia = dica_str
                        else:
                            ultima_dica_ia = "Dica: Nenhum lance encontrado."
                    # 4. TOGGLE SOM (S)
                    elif event.key == pygame.K_s:
                        sound_manager.enabled = not sound_manager.enabled
                        print(f"Som {'Ativado' if sound_manager.enabled else 'Desativado'}")
                    # Atalho para testar fim de jogo (ESPAÇO)
                    elif event.key == pygame.K_SPACE:
                        engine.stop()
                        pontuacao_final = 1000
                        estado_atual = ESTADO_INPUT_NOME
                # --- FIM DOS ATALHOS ---

                # Só permite jogada do jogador se for a vez da sua cor (Código antigo continua aqui...)
                if (engine.board.turn == (chess.WHITE if jogador_brancas else chess.BLACK)):
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mouse_x, mouse_y = event.pos
                        # Corrige cálculo de linha/coluna se tabuleiro estiver flipado
                        if display_board.is_flipped:
                            col = 7 - (mouse_x // display_board.sq_size)
                            row = mouse_y // display_board.sq_size
                        else:
                            col = mouse_x // display_board.sq_size
                            row = 7 - (mouse_y // display_board.sq_size)
                        square = chess.square(col, row)

                        if selecionado is None:
                            # Tenta selecionar peça do jogador (da cor escolhida)
                            piece = engine.board.piece_at(square)
                            if piece and piece.color == (chess.WHITE if jogador_brancas else chess.BLACK):
                                selecionado = square
                                sound_manager.play('move')
                        else:
                            # Tenta mover
                            move = chess.Move(selecionado, square)
                            # Verifica promoções (simples: promove para Rainha automaticamente)
                            if engine.board.piece_at(selecionado).piece_type == chess.PAWN and chess.square_rank(square) == (7 if jogador_brancas else 0):
                                move = chess.Move(selecionado, square, promotion=chess.QUEEN)

                            if move in engine.board.legal_moves and engine.board.piece_at(selecionado).color == (chess.WHITE if jogador_brancas else chess.BLACK):
                                realizar_jogada(engine, move, display_board, sound_manager)
                                selecionado = None
                                aguardando_ia = True # Passa a vez
                            else:
                                # Se clicou errado ou em outra peça sua, reseta/troca seleção
                                piece = engine.board.piece_at(square)
                                if piece and piece.color == (chess.WHITE if jogador_brancas else chess.BLACK):
                                    selecionado = square
                                    sound_manager.play('move')
                                else:
                                    selecionado = None

        # --- Atualizações de Lógica (IA e Estado) ---
        if estado_atual == ESTADO_JOGANDO:
            if engine.is_game_over():
                engine.stop()
                tempo_decorrido = engine.get_game_duration()
                vencedor_cor = engine.get_winner()
                # Lógica para definir se o JOGADOR venceu, perdeu ou empatou
                cor_jogador = 'white' if jogador_brancas else 'black'
                resultado_stats = 'draw'
                if vencedor_cor == 'draw':
                    resultado_stats = 'draw'
                elif vencedor_cor == cor_jogador:
                    resultado_stats = 'win'
                else:
                    resultado_stats = 'loss'
                # --- NOVO: Atualiza Estatísticas ---
                score_manager.update_stats(resultado_stats)
                # -----------------------------------
                venceu = (resultado_stats == 'win')

                material = calcular_material(engine.board, jogador_brancas)
                pontuacao_final = score_manager.calcular_pontuacao(venceu, material, tempo_decorrido)

                if venceu:
                    tocar_som_acao(engine.board, None, sound_manager, acao='game_over')
                else:
                    tocar_som_acao(engine.board, None, sound_manager, acao='defeat')

                if score_manager.check_is_highscore(pontuacao_final):
                    input_nome.text = ""
                    input_nome.active = True
                    estado_atual = ESTADO_INPUT_NOME
                else:
                    estado_atual = ESTADO_RANKING
            # IA Joga (cor oposta ao jogador)
            elif aguardando_ia:
                move = get_best_move(engine.board, dificuldade)
                if move:
                    realizar_jogada(engine, move, display_board, sound_manager)
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

            # --- NOVO: Desenhar Estatísticas no Menu ---
            stats = score_manager.load_stats()
            win_rate = score_manager.get_win_rate()
            # Caixa de fundo no rodapé
            rect_stats = pygame.Rect(200, 450, 440, 100)
            pygame.draw.rect(screen, (50, 50, 50), rect_stats, border_radius=10)
            pygame.draw.rect(screen, (100, 100, 100), rect_stats, 2, border_radius=10)
            fonte_stats = pygame.font.SysFont("consolas", 18)
            fonte_big = pygame.font.SysFont("arial", 30, bold=True)
            # Textos
            txt_total = fonte_stats.render(f"Jogos: {stats['games_played']}", True, (200, 200, 200))
            txt_win   = fonte_stats.render(f"V: {stats['wins']}", True, (100, 255, 100)) # Verde
            txt_loss  = fonte_stats.render(f"D: {stats['losses']}", True, (255, 100, 100)) # Vermelho
            txt_draw  = fonte_stats.render(f"E: {stats['draws']}", True, (100, 100, 255)) # Azul
            # Porcentagem em destaque
            cor_rate = (255, 215, 0) if win_rate > 50 else (200, 200, 200)
            txt_rate  = fonte_big.render(f"{win_rate:.1f}%", True, cor_rate)
            lbl_rate  = fonte_stats.render("Aproveitamento", True, (150, 150, 150))
            # Posicionamento
            screen.blit(txt_total, (220, 460))
            screen.blit(txt_win,   (220, 490))
            screen.blit(txt_loss,  (300, 490))
            screen.blit(txt_draw,  (380, 490))
            # Lado direito da caixa (Aproveitamento)
            screen.blit(txt_rate, (500, 465))
            screen.blit(lbl_rate, (480, 500))
        elif estado_atual == ESTADO_ESCOLHA_COR:
            # Título
            fonte = pygame.font.SysFont("arial", 32)
            screen.fill((40, 40, 40))
            # --- DIFICULDADE ---
            fonte_peq = pygame.font.SysFont("arial", 24)
            lbl_dif = fonte.render("Dificuldade:", True, (255,255,255))
            screen.blit(lbl_dif, (200, 100))
            # Botões de Dificuldade (agora 4 níveis)
            colors_dif = [(100,100,100), (100,100,100), (100,100,100), (100,100,100)]
            if 1 <= dificuldade <= 4:
                colors_dif[dificuldade-1] = (0, 200, 0)
            w_btn = 90
            gap = 10
            start_x = 220
            btn_facil = pygame.Rect(start_x, 150, w_btn, 40)
            btn_medio = pygame.Rect(start_x + w_btn + gap, 150, w_btn, 40)
            btn_dificil = pygame.Rect(start_x + (w_btn + gap)*2, 150, w_btn, 40)
            btn_pro = pygame.Rect(start_x + (w_btn + gap)*3, 150, w_btn, 40)
            botoes = [btn_facil, btn_medio, btn_dificil, btn_pro]
            textos = ["Fácil", "Médio", "Difícil", "Pro"]
            for i, (btn, txt) in enumerate(zip(botoes, textos)):
                pygame.draw.rect(screen, colors_dif[i], btn, border_radius=5)
                font_btn = pygame.font.SysFont("arial", 20)
                lbl = font_btn.render(txt, True, (255,255,255))
                screen.blit(lbl, (btn.x + (btn.width - lbl.get_width())//2, btn.y + 8))
            # --- COR ---
            lbl_cor = fonte.render("Escolha sua cor:", True, (255,255,255))
            screen.blit(lbl_cor, (270, 250))
            btn_brancas.y = 300
            btn_pretas.y = 300
            pygame.draw.rect(screen, (220, 220, 220), btn_brancas, border_radius=12)
            txt_b = fonte2.render("Brancas", True, (60, 60, 60))
            screen.blit(txt_b, (btn_brancas.x + 40, btn_brancas.y + 10))
            pygame.draw.rect(screen, (40, 40, 40), btn_pretas, border_radius=12)
            pygame.draw.rect(screen, (200, 200, 200), btn_pretas, 2, border_radius=12)
            txt_p = fonte2.render("Pretas", True, (220, 220, 220))
            screen.blit(txt_p, (btn_pretas.x + 50, btn_pretas.y + 10))
        elif estado_atual == ESTADO_JOGANDO:
            display_board.draw(engine.board)
            # Destaque opcional para peça selecionada
            if selecionado is not None:
                col = chess.square_file(selecionado)
                row = 7 - chess.square_rank(selecionado)
                # Corrige para flip do tabuleiro
                if display_board.is_flipped:
                    draw_col = 7 - col
                    draw_row = 7 - row
                else:
                    draw_col = col
                    draw_row = row
                x = draw_col * 80
                y = draw_row * 80
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


                # --- DICA DA IA ---
                # Posiciona logo abaixo dos cemitérios, aproveitando o espaço vazio
                dica_y = img_y + img_size + 30
                if ultima_dica_ia:
                    fonte_dica = pygame.font.SysFont("arial", 18, bold=True)
                    cor_dica = (34, 180, 90)  # Verde agradável
                    dica_txt = fonte_dica.render(ultima_dica_ia, True, cor_dica)
                    screen.blit(dica_txt, (panel_x + 20, dica_y))

                # --- LEGENDA DE ATALHOS ---
                fonte_mini = pygame.font.SysFont("arial", 14)
                status_som = "ON" if sound_manager.enabled else "OFF"
                cor_som = (100, 255, 100) if sound_manager.enabled else (255, 100, 100)
                texto_ajuda = [
                    "H - Dica",
                    "Ctrl+Z - Desfazer",
                    "F2 - Reiniciar",
                    "M - Menu",
                    f"S - Som: {status_som}"
                ]
                y_ajuda = 640 - 100
                pygame.draw.line(screen, (100,100,100), (panel_x + 10, y_ajuda - 10), (panel_x + 190, y_ajuda - 10))
                for linha in texto_ajuda:
                    if "Som:" in linha:
                        txt = fonte_mini.render(linha, True, cor_som)
                    else:
                        txt = fonte_mini.render(linha, True, (180, 180, 180))
                    screen.blit(txt, (panel_x + 20, y_ajuda))
                    y_ajuda += 20

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

        # Atalho M para menu em qualquer estado (exceto já no menu)
        for event in eventos:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m and estado_atual != ESTADO_MENU:
                engine.start()
                estado_atual = ESTADO_MENU

        pygame.display.flip()

if __name__ == "__main__":
    main()