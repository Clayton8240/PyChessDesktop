import sys
import pygame
import chess
from src.config import *
from src.ui import TextInput, LeaderboardView, DisplayBoard, THEMES
from src.engine import Engine
from src.scoring import ScoreManager
from src.ai import get_best_move, evaluate_board
from src.sound import SoundManager
from src.pgn_manager import PGNManager

# Função auxiliar para calcular material
def calcular_material(board, is_white_player):
    valores = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
    pontos = 0
    cor_jogador = chess.WHITE if is_white_player else chess.BLACK
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == cor_jogador and piece.piece_type != chess.KING:
            pontos += valores.get(piece.piece_type, 0)
    return pontos

# Função auxiliar de movimento
def realizar_jogada(engine, move, display_board, sound_manager):
    display_board.animate_move(move, engine.board)
    if engine.board.piece_at(move.to_square) is not None:
        tocar_som_acao(engine.board, move, sound_manager, acao='capture')
    else:
        tocar_som_acao(engine.board, move, sound_manager, acao='move')
    engine.board.push(move)

def tocar_som_acao(board, move, sound_manager, acao='move'):
    peca = None
    if move is not None:
        peca = board.piece_at(move.from_square)
    
    if acao == 'move':
        if peca and peca.piece_type == chess.PAWN:
            sound_manager.play('pawn_move')
        elif peca and peca.piece_type == chess.KING:
            sound_manager.play('king_move')
        else:
            sound_manager.play('move')
    elif acao == 'capture':
        sound_manager.play('capture')
    elif acao in ['menu', 'undo', 'game_over', 'defeat', 'hint']:
        sound_manager.play(acao)

# Estados do Jogo
ESTADO_MENU = 0
ESTADO_ESCOLHA_COR = 1
ESTADO_JOGANDO = 2
ESTADO_INPUT_NOME = 3
ESTADO_RANKING = 4
ESTADO_TEMA = 5
ESTADO_PGN_SELECT = 6
ESTADO_SIMULACAO = 7

def main():
    pygame.init()
    screen = pygame.display.set_mode((840, 640))
    pygame.display.set_caption("PyChess Desktop")
    clock = pygame.time.Clock()


    # Inicialização
    engine = Engine()
    engine.start()
    score_manager = ScoreManager()
    sound_manager = SoundManager()

    # UI Components
    tema_atual = 'classico'
    display_board = DisplayBoard(screen, tamanho_quadrado=80, tema=tema_atual)

    # Importação local para evitar ciclo, ou mova EvaluationBar para ui.py completamente
    from src.ui import EvaluationBar 
    eval_bar = EvaluationBar(pygame.Rect(640, 0, 20, 640))

    input_nome = TextInput(pygame.font.SysFont("consolas", 30), rect=pygame.Rect(170, 300, 300, 50))

    # Fontes
    fonte_titulo = pygame.font.SysFont("arial", 40, bold=True)
    fonte_btn = pygame.font.SysFont("arial", 28)
    fonte_small = pygame.font.SysFont("arial", 20)

    estado_atual = ESTADO_MENU

    # Variáveis de controle
    selecionado = None
    aguardando_ia = False
    pontuacao_final = 0
    tempo_decorrido = 0
    jogador_brancas = True
    dificuldade = 2
    tempo_escolhido = 600
    ultima_dica_ia = None

    # Promoção
    promocao_pendente = False
    move_promocao_pendente = None
    cor_promocao_pendente = None
    quadrado_promocao = None

    # --- Replay/Simulação ---
    pgn_manager = PGNManager()
    sim_moves = []      # Lista de movimentos carregados
    sim_index = 0       # Em qual movimento estamos (0 = início)
    sim_auto = False    # Play/Pause
    sim_speed = 1000    # Delay em ms (1 segundo)
    sim_timer = 0       # Cronômetro interno
    sim_headers = {}    # Nomes dos jogadores

    while True:
        dt = clock.tick(60)
        
        # --- LÓGICA DE TEMPO ---
        if estado_atual == ESTADO_JOGANDO and not engine.is_game_over():
            engine.update_timer(dt / 1000.0)

        # --- PROCESSAMENTO DE EVENTOS ---
        eventos = pygame.event.get()
        for event in eventos:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Atalho Global M para Menu
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m and estado_atual != ESTADO_MENU:
                engine.start()
                estado_atual = ESTADO_MENU
                continue

            # ---------------- ESTADO: MENU ----------------
            if estado_atual == ESTADO_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Definição dos botões (apenas lógica de colisão)
                    btn_novo = pygame.Rect(260, 250, 320, 50)
                    btn_pont = pygame.Rect(260, 320, 320, 50)
                    btn_tema = pygame.Rect(260, 390, 320, 50)
                    btn_som = pygame.Rect(760, 20, 60, 40)

                    if btn_novo.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_ESCOLHA_COR
                    elif btn_pont.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_RANKING
                    elif btn_tema.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_TEMA
                    elif btn_som.collidepoint(event.pos):
                        sound_manager.enabled = not sound_manager.enabled
                        if sound_manager.enabled: sound_manager.play('menu')

            # ---------------- ESTADO: TEMAS ----------------
            elif estado_atual == ESTADO_TEMA:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Lógica de clique nos temas
                    temas_lista = ['classico', 'torneio', 'dark', 'retro']
                    btn_voltar = pygame.Rect(320, 520, 200, 44)
                    
                    if btn_voltar.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_MENU
                    
                    for i, tema in enumerate(temas_lista):
                        btn_rect = pygame.Rect(220, 180 + i*80, 400, 60)
                        if btn_rect.collidepoint(event.pos):
                            tema_atual = tema
                            display_board.set_tema(tema)
                            sound_manager.play('menu')

            # ---------------- ESTADO: ESCOLHA COR ----------------
            elif estado_atual == ESTADO_ESCOLHA_COR:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Botões
                    start_x = 220
                    # Dificuldade
                    for i in range(4):
                        r = pygame.Rect(start_x + i*105, 120, 95, 40)
                        if r.collidepoint(event.pos):
                            dificuldade = i + 1
                            sound_manager.play('move')
                    # Tempo
                    tempos_valores = [300, 600, None]
                    for i, val in enumerate(tempos_valores):
                        r = pygame.Rect(start_x + i*140, 220, 130, 40)
                        if r.collidepoint(event.pos):
                            tempo_escolhido = val
                            sound_manager.play('move')
                    # Cor
                    btn_brancas = pygame.Rect(180, 330, 220, 50)
                    btn_pretas = pygame.Rect(420, 330, 220, 50)
                    
                    if btn_brancas.collidepoint(event.pos):
                        jogador_brancas = True
                        display_board.set_flip(False)
                        eval_bar.set_flip(False)
                        engine.start(time_limit=tempo_escolhido)
                        sound_manager.play('menu')
                        estado_atual = ESTADO_JOGANDO
                    elif btn_pretas.collidepoint(event.pos):
                        jogador_brancas = False
                        display_board.set_flip(True)
                        eval_bar.set_flip(True)
                        engine.start(time_limit=tempo_escolhido)
                        sound_manager.play('menu')
                        estado_atual = ESTADO_JOGANDO
                        # IA joga primeiro se for brancas
                        if engine.board.turn == chess.WHITE:
                            move = get_best_move(engine.board, dificuldade)
                            if move:
                                engine.board.push(move)
                                tocar_som_acao(engine.board, move, sound_manager, acao='move')

            # ---------------- ESTADO: JOGANDO ----------------
            elif estado_atual == ESTADO_JOGANDO and not aguardando_ia:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        if len(engine.board.move_stack) >= 2:
                            display_board.active_animation = None
                            display_board.animating_dest_square = None
                            engine.board.pop(); engine.board.pop()
                            selecionado = None
                            sound_manager.play('undo')
                    elif event.key == pygame.K_h:
                        move = get_best_move(engine.board, dificuldade)
                        if move:
                            selecionado = move.from_square
                            ultima_dica_ia = f"Dica: {chess.square_name(move.from_square)} -> {chess.square_name(move.to_square)}"
                            sound_manager.play('hint')
                    elif event.key == pygame.K_s:
                        sound_manager.enabled = not sound_manager.enabled

                # Clique no tabuleiro
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Se tiver promoção pendente, checa clique no menu flutuante
                    if promocao_pendente:
                        # Lógica de botões de promoção
                        col = chess.square_file(quadrado_promocao)
                        row = 7 - chess.square_rank(quadrado_promocao)
                        if display_board.is_flipped: col, row = 7-col, 7-row
                        menu_x, menu_y = col * 80 + 10, row * 80 - 10
                        
                        pecas = [ (chess.QUEEN, 0), (chess.ROOK, 1), (chess.BISHOP, 2), (chess.KNIGHT, 3) ]
                        for ptype, idx in pecas:
                            btn_rect = pygame.Rect(menu_x + 5, menu_y + 10 + idx*50, 50, 45)
                            if btn_rect.collidepoint(event.pos):
                                move = chess.Move(move_promocao_pendente.from_square, move_promocao_pendente.to_square, promotion=ptype)
                                realizar_jogada(engine, move, display_board, sound_manager)
                                eval_bar.update(evaluate_board(engine.board))
                                selecionado = None
                                promocao_pendente = False
                                aguardando_ia = True
                        continue # Pula o resto da lógica de clique

                    # Lógica normal de movimento
                    mouse_x, mouse_y = event.pos
                    if mouse_x < 640: # Clique dentro do tabuleiro
                        c = mouse_x // 80
                        r = mouse_y // 80
                        if display_board.is_flipped: c, r = 7-c, 7-r # Ajuste visual no clique
                        
                        # Garante que r/c estão entre 0-7
                        if 0 <= c <= 7 and 0 <= r <= 7:
                            # IMPORTANTE: No Pygame Y cresce pra baixo (0 no topo), no Chess Rank 0 é em baixo.
                            # A fórmula "row = 7 - (mouse_y // 80)" inverte isso corretamente para a Engine.
                            # Mas se usarmos 'r' direto do mouse, precisamos converter.
                            # Engine espera: rank 0 (embaixo), rank 7 (topo)
                            # Mouse dá: 0 (topo), 7 (embaixo)
                            # Então: rank = 7 - r
                            square = chess.square(c, 7 - r)

                            if selecionado is None:
                                piece = engine.board.piece_at(square)
                                if piece and piece.color == (chess.WHITE if jogador_brancas else chess.BLACK):
                                    selecionado = square
                                    sound_manager.play('move')
                            else:
                                move = chess.Move(selecionado, square)
                                # Checa Promoção
                                if engine.board.piece_at(selecionado).piece_type == chess.PAWN and chess.square_rank(square) in [0, 7]:
                                    # Valida se é um movimento legal (mesmo sem saber a promoção ainda)
                                    move_test = chess.Move(selecionado, square, promotion=chess.QUEEN)
                                    if move_test in engine.board.legal_moves:
                                        promocao_pendente = True
                                        move_promocao_pendente = move
                                        cor_promocao_pendente = engine.board.piece_at(selecionado).color
                                        quadrado_promocao = square
                                        continue

                                if move in engine.board.legal_moves and engine.board.piece_at(selecionado).color == (chess.WHITE if jogador_brancas else chess.BLACK):
                                    realizar_jogada(engine, move, display_board, sound_manager)
                                    eval_bar.update(evaluate_board(engine.board))
                                    selecionado = None
                                    aguardando_ia = True
                                else:
                                    # Troca de seleção ou cancela
                                    piece = engine.board.piece_at(square)
                                    if piece and piece.color == (chess.WHITE if jogador_brancas else chess.BLACK):
                                        selecionado = square
                                        sound_manager.play('move')
                                    else:
                                        selecionado = None

            # ---------------- ESTADO: INPUT NOME ----------------
            elif estado_atual == ESTADO_INPUT_NOME:
                res = input_nome.handle_event(event)
                if res == 'submit':
                    score_manager.save_score(input_nome.text, pontuacao_final, "00:00")
                    estado_atual = ESTADO_RANKING

        # --- LÓGICA DE JOGO (IA e Fim) ---
        if estado_atual == ESTADO_JOGANDO:
            if engine.is_game_over():
                engine.stop()
                vencedor = engine.get_winner()
                eh_vitoria = (vencedor == ('white' if jogador_brancas else 'black'))
                score_manager.update_stats('win' if eh_vitoria else ('loss' if vencedor != 'draw' else 'draw'))
                
                pontuacao_final = score_manager.calcular_pontuacao(eh_vitoria, calcular_material(engine.board, jogador_brancas), engine.get_game_duration())
                
                if eh_vitoria: sound_manager.play('game_over')
                else: sound_manager.play('defeat')
                
                if score_manager.check_is_highscore(pontuacao_final):
                    input_nome.text = ""; input_nome.active = True
                    estado_atual = ESTADO_INPUT_NOME
                else:
                    estado_atual = ESTADO_RANKING
            
            elif aguardando_ia and not promocao_pendente:
                move = get_best_move(engine.board, dificuldade)
                if move:
                    realizar_jogada(engine, move, display_board, sound_manager)
                    eval_bar.update(evaluate_board(engine.board))
                aguardando_ia = False

        # --- DESENHO (RENDERIZAÇÃO) ---
        screen.fill((40, 40, 40))

        if estado_atual == ESTADO_MENU:
            titulo = fonte_titulo.render("PyChess Desktop", True, (255, 255, 255))
            screen.blit(titulo, (840//2 - titulo.get_width()//2, 120))

            # Botões
            btn_novo = pygame.Rect(260, 250, 320, 50)
            btn_pont = pygame.Rect(260, 320, 320, 50)
            btn_tema = pygame.Rect(260, 390, 320, 50)
            btn_replay = pygame.Rect(260, 460, 320, 50)
            btn_som = pygame.Rect(760, 20, 60, 40)

            for btn, texto in [(btn_novo, "Novo Jogo"), (btn_pont, "Pontuações"), (btn_tema, "Temas"), (btn_replay, "Replay")]:
                pygame.draw.rect(screen, (70, 130, 180), btn, border_radius=12)
                pygame.draw.rect(screen, (200, 200, 200), btn, 2, border_radius=12)
                txt = fonte_btn.render(texto, True, (255,255,255))
                screen.blit(txt, (btn.centerx - txt.get_width()//2, btn.centery - txt.get_height()//2))

            # Botão Som
            cor_som = (100, 200, 100) if sound_manager.enabled else (200, 100, 100)
            pygame.draw.rect(screen, cor_som, btn_som, border_radius=5)
            txt_som = pygame.font.SysFont("arial", 16, bold=True).render("SOM", True, (255,255,255))
            screen.blit(txt_som, (btn_som.centerx - txt_som.get_width()//2, btn_som.centery - txt_som.get_height()//2))

            # Stats
            stats = score_manager.load_stats()
            win_rate = score_manager.get_win_rate()
            msg = f"V: {stats['wins']}  D: {stats['losses']}  E: {stats['draws']}  ({win_rate:.1f}%)"
            screen.blit(fonte_small.render(msg, True, (150, 150, 150)), (280, 530))

            # Clique nos botões
            for event in eventos:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_novo.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_ESCOLHA_COR
                    elif btn_pont.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_RANKING
                    elif btn_tema.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_TEMA
                    elif btn_replay.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_PGN_SELECT
                    elif btn_som.collidepoint(event.pos):
                        sound_manager.enabled = not sound_manager.enabled
                        if sound_manager.enabled: sound_manager.play('menu')

        elif estado_atual == ESTADO_TEMA:
            screen.fill((30, 30, 40))
            lbl = fonte_titulo.render("Escolha o Tema", True, (255,255,255))
            screen.blit(lbl, (840//2 - lbl.get_width()//2, 80))
            
            temas_nomes = {'classico': 'Clássico', 'torneio': 'Torneio', 'dark': 'Dark Mode', 'retro': 'Retrô'}
            for i, tema in enumerate(['classico', 'torneio', 'dark', 'retro']):
                rect = pygame.Rect(220, 180 + i*80, 400, 60)
                cor = (60, 100, 160) if tema_atual == tema else (80, 80, 80)
                pygame.draw.rect(screen, cor, rect, border_radius=10)
                txt = fonte_btn.render(temas_nomes[tema], True, (255,255,255))
                screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
            
            # Botão Voltar
            btn_voltar = pygame.Rect(320, 520, 200, 44)
            pygame.draw.rect(screen, (150, 50, 50), btn_voltar, border_radius=10)
            txt_v = fonte_btn.render("Voltar", True, (255,255,255))
            screen.blit(txt_v, (btn_voltar.centerx - txt_v.get_width()//2, btn_voltar.centery - txt_v.get_height()//2))

        elif estado_atual == ESTADO_ESCOLHA_COR:
            screen.fill((40, 40, 40))
            # Desenhe aqui os botões de dificuldade, tempo e cor (copie do seu código anterior se precisar do visual específico)
            # Versão simplificada para garantir funcionamento:
            screen.blit(fonte_titulo.render("Configuração", True, (255,255,255)), (300, 50))
            
            # Dificuldade
            lbl_dif = fonte_small.render(f"Dificuldade: {dificuldade}", True, (255,255,255))
            screen.blit(lbl_dif, (350, 120))
            for i in range(4):
                r = pygame.Rect(220 + i*105, 150, 95, 40)
                c = (0, 200, 0) if dificuldade == i+1 else (100,100,100)
                pygame.draw.rect(screen, c, r, border_radius=5)
                screen.blit(fonte_small.render(str(i+1), True, (255,255,255)), (r.x+40, r.y+10))

            # Tempo
            lbl_time = fonte_small.render(f"Tempo: {tempo_escolhido}", True, (255,255,255))
            screen.blit(lbl_time, (350, 220))
            tempos = [300, 600, None]
            labels = ["5 min", "10 min", "Livre"]
            for i, val in enumerate(tempos):
                r = pygame.Rect(220 + i*140, 250, 130, 40)
                c = (0, 200, 0) if tempo_escolhido == val else (100,100,100)
                pygame.draw.rect(screen, c, r, border_radius=5)
                screen.blit(fonte_small.render(labels[i], True, (255,255,255)), (r.x+20, r.y+10))

            # Cor
            btn_brancas = pygame.Rect(180, 330, 220, 50)
            btn_pretas = pygame.Rect(420, 330, 220, 50)
            pygame.draw.rect(screen, (200, 200, 200), btn_brancas, border_radius=10)
            screen.blit(fonte_btn.render("Brancas", True, (0,0,0)), (230, 340))
            pygame.draw.rect(screen, (20, 20, 20), btn_pretas, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), btn_pretas, 2, border_radius=10)
            screen.blit(fonte_btn.render("Pretas", True, (255,255,255)), (480, 340))

        elif estado_atual == ESTADO_JOGANDO:
            # Atalho Ctrl+S para salvar PGN
            for event in eventos:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        result = engine.board.result()
                        nome_arquivo = pgn_manager.save_game(
                            engine.board, 
                            "Brancas" if jogador_brancas else "IA",
                            "IA" if jogador_brancas else "Pretas",
                            result
                        )
                        print(f"Salvo em: {nome_arquivo}")
                        sound_manager.play('menu')
                    # ---------------- ESTADO: SELEÇÃO DE PGN ----------------
                    elif estado_atual == ESTADO_PGN_SELECT:
                        screen.fill((40, 40, 40))
                        fonte_titulo2 = pygame.font.SysFont("arial", 30, bold=True)
                        screen.blit(fonte_titulo2.render("Selecione uma Partida", True, (255,255,255)), (280, 50))
                        arquivos = pgn_manager.list_files()
                        mouse_pos = pygame.mouse.get_pos()
                        click = False
                        for evt in eventos:
                            if evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1: click = True
                            if evt.type == pygame.KEYDOWN and evt.key == pygame.K_ESCAPE:
                                estado_atual = ESTADO_MENU
                        y_start = 120
                        fonte_arq = pygame.font.SysFont("consolas", 18)
                        if not arquivos:
                            screen.blit(fonte_arq.render("Nenhuma partida salva em data/pgn/", True, (150,150,150)), (250, 200))
                        for i, arq in enumerate(arquivos):
                            if i > 10: break
                            rect = pygame.Rect(220, y_start + i*45, 400, 40)
                            cor = (60, 80, 100)
                            if rect.collidepoint(mouse_pos):
                                cor = (80, 100, 120)
                                if click:
                                    sim_moves, sim_headers = pgn_manager.load_game_moves(arq)
                                    engine.board.reset()
                                    sim_index = 0
                                    sim_auto = False
                                    sim_timer = 0
                                    estado_atual = ESTADO_SIMULACAO
                                    sound_manager.play('menu')
                            pygame.draw.rect(screen, cor, rect, border_radius=5)
                            screen.blit(fonte_arq.render(arq, True, (255,255,255)), (rect.x + 10, rect.y + 10))
                        btn_voltar = pygame.Rect(320, 550, 200, 40)
                        pygame.draw.rect(screen, (150, 50, 50), btn_voltar, border_radius=8)
                        txt_v = fonte_btn.render("Voltar", True, (255,255,255))
                        screen.blit(txt_v, (btn_voltar.centerx - txt_v.get_width()//2, btn_voltar.y+5))
                        if click and btn_voltar.collidepoint(mouse_pos):
                            estado_atual = ESTADO_MENU

                    # ---------------- ESTADO: SIMULAÇÃO ----------------
                    elif estado_atual == ESTADO_SIMULACAO:
                        # 1. Lógica de Autoplay
                        if sim_auto:
                            sim_timer += dt
                            if sim_timer >= sim_speed:
                                sim_timer = 0
                                if sim_index < len(sim_moves):
                                    move = sim_moves[sim_index]
                                    realizar_jogada(engine, move, display_board, sound_manager)
                                    sim_index += 1
                                else:
                                    sim_auto = False
                        # 2. Eventos e Controles Manuais
                        for evt in eventos:
                            if evt.type == pygame.QUIT: pygame.quit(); sys.exit()
                            if evt.type == pygame.KEYDOWN:
                                if evt.key == pygame.K_RIGHT:
                                    if sim_index < len(sim_moves):
                                        move = sim_moves[sim_index]
                                        realizar_jogada(engine, move, display_board, sound_manager)
                                        sim_index += 1
                                        sim_auto = False
                                elif evt.key == pygame.K_LEFT:
                                    if sim_index > 0:
                                        engine.board.pop()
                                        sim_index -= 1
                                        sim_auto = False
                                        sound_manager.play('move')
                                elif evt.key == pygame.K_SPACE:
                                    sim_auto = not sim_auto
                                elif evt.key == pygame.K_ESCAPE:
                                    engine.start()
                                    estado_atual = ESTADO_PGN_SELECT
                        # 3. Renderização (Tabuleiro + Interface de Player)
                        display_board.draw(engine.board)
                        panel_rect = pygame.Rect(660, 0, 180, 640)
                        pygame.draw.rect(screen, (40, 40, 50), panel_rect)
                        fonte_info = pygame.font.SysFont("arial", 14)
                        y_info = 20
                        screen.blit(fonte_info.render(f"Brancas: {sim_headers.get('White','?')}", True, (200,200,200)), (670, y_info))
                        screen.blit(fonte_info.render(f"Pretas: {sim_headers.get('Black','?')}", True, (200,200,200)), (670, y_info+20))
                        screen.blit(fonte_info.render(f"Data: {sim_headers.get('Date','?')}", True, (150,150,150)), (670, y_info+45))
                        txt_move = pygame.font.SysFont("consolas", 30).render(f"{sim_index}/{len(sim_moves)}", True, (255,255,0))
                        screen.blit(txt_move, (670 + 90 - txt_move.get_width()//2, 150))
                        dicas = [
                            "SETAS: < > Navegar",
                            "ESPAÇO: Play/Pause",
                            "ESC: Voltar"
                        ]
                        for i, dica in enumerate(dicas):
                            screen.blit(fonte_info.render(dica, True, (150,150,150)), (670, 500 + i*25))
                        status_txt = "REPRODUZINDO >>" if sim_auto else "PAUSADO ||"
                        cor_status = (0, 255, 0) if sim_auto else (255, 100, 100)
                        screen.blit(fonte_btn.render(status_txt, True, cor_status), (670, 100))
            display_board.draw(engine.board)
            eval_bar.draw(screen)
            if selecionado is not None:
                # Desenha destaque da seleção
                c = chess.square_file(selecionado)
                r = 7 - chess.square_rank(selecionado)
                if display_board.is_flipped: c, r = 7-c, 7-r
                s = pygame.Surface((80, 80))
                s.set_alpha(100); s.fill((255, 255, 0))
                screen.blit(s, (c*80, r*80))
                display_board.draw_valid_moves(engine.board, selecionado)
            
            # Painel Lateral (código simplificado para caber)
            pygame.draw.rect(screen, (60, 60, 60), (660, 0, 180, 640))
            # Relógios
            def fmt_time(t): return "--:--" if engine.time_limit is None else f"{int(t)//60:02}:{int(t)%60:02}"
            
            # Preto (Topo)
            pygame.draw.rect(screen, (30, 30, 30), (670, 20, 160, 50), border_radius=5)
            screen.blit(fonte_btn.render(fmt_time(engine.black_time), True, (255,50,50) if engine.black_time<30 else (255,255,255)), (700, 30))
            
            # Branco (Baixo)
            pygame.draw.rect(screen, (200, 200, 200), (670, 400, 160, 50), border_radius=5)
            screen.blit(fonte_btn.render(fmt_time(engine.white_time), True, (0,0,0)), (700, 410))

            # Dica
            if ultima_dica_ia:
                screen.blit(fonte_small.render("Dica:", True, (100, 255, 100)), (670, 200))
                screen.blit(fonte_small.render(ultima_dica_ia.replace("Dica: ", ""), True, (200, 200, 200)), (670, 230))

            # Promoção Pendente (Menu Flutuante)
            if promocao_pendente and quadrado_promocao is not None:
                c = chess.square_file(quadrado_promocao)
                r = 7 - chess.square_rank(quadrado_promocao)
                if display_board.is_flipped: c, r = 7-c, 7-r
                
                # Fundo do menu
                menu_x, menu_y = c*80, r*80
                if menu_y > 400: menu_y -= 200 # Se for em baixo, joga menu pra cima
                pygame.draw.rect(screen, (50, 50, 50), (menu_x, menu_y, 80, 200))
                pygame.draw.rect(screen, (255, 255, 255), (menu_x, menu_y, 80, 200), 2)
                
                # Desenha ícones
                pecas = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
                for i, p in enumerate(pecas):
                    img = display_board.images.get((p, cor_promocao_pendente))
                    if img:
                        screen.blit(pygame.transform.scale(img, (60, 60)), (menu_x+10, menu_y + i*50))

        elif estado_atual == ESTADO_RANKING:
            scores = score_manager.load_scores()
            view = LeaderboardView(pygame.font.SysFont("consolas", 20), scores)
            view.draw(screen, pos=(150, 100))
            screen.blit(fonte_small.render("Pressione M para voltar", True, (150,150,150)), (280, 550))

        elif estado_atual == ESTADO_INPUT_NOME:
            msg = fonte_btn.render(f"Recorde! Pontos: {pontuacao_final}", True, (255,255,255))
            screen.blit(msg, (200, 200))
            input_nome.draw(screen)

        pygame.display.flip()

if __name__ == "__main__":
    main()