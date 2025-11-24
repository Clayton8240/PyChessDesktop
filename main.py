import sys
import pygame
import chess
import tkinter as tk
from tkinter import filedialog
from src.config import *
from src.ui import TextInput, LeaderboardView, DisplayBoard, THEMES, EvaluationBar
from src.engine import Engine
from src.scoring import ScoreManager
from src.ai import get_best_move, evaluate_board
from src.sound import SoundManager
from src.pgn_manager import PGNManager
from src.puzzle_manager import PuzzleManager # <--- Adicione isto

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
ESTADO_PUZZLE = 8 # <--- Novo Estado

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
    ultima_dica_move = None  # Guarda o movimento sugerido para desenhar seta

    # --- Notificações ---
    aviso_texto = ""
    aviso_timer = 0

    # Promoção
    promocao_pendente = False
    move_promocao_pendente = None
    cor_promocao_pendente = None
    quadrado_promocao = None

    # Replay/Simulação
    pgn_manager = PGNManager()
    puzzle_manager = PuzzleManager()
    puzzle_ativo = False
    puzzle_info = "" # Texto para mostrar na tela (ex: "Mate em 1")
    feedback_puzzle = "" # "Correto!" ou "Tente Novamente"
    puzzle_hint_move = None # <--- NOVO: Guarda o movimento da dica
    feedback_timer = 0
    sim_moves = []
    sim_index = 0
    sim_auto = False
    sim_speed = 1000
    sim_timer = 0
    sim_headers = {}

    while True:
        dt = clock.tick(60)
        
        # --- LÓGICA DE TEMPO E UPDATE ---
        if estado_atual == ESTADO_JOGANDO and not engine.is_game_over():
            engine.update_timer(dt / 1000.0)
        
        if estado_atual == ESTADO_SIMULACAO and sim_auto:
            sim_timer += dt
            if sim_timer >= sim_speed:
                sim_timer = 0
                if sim_index < len(sim_moves):
                    move = sim_moves[sim_index]
                    realizar_jogada(engine, move, display_board, sound_manager)
                    sim_index += 1
                else:
                    sim_auto = False

        # --- PROCESSAMENTO DE EVENTOS ---
        eventos = pygame.event.get()
        for event in eventos:
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # Atalho Global M para Menu
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m and estado_atual != ESTADO_INPUT_NOME:
                engine.start()
                estado_atual = ESTADO_MENU
                sound_manager.play('menu')
                continue

            # --- ESTADO: MENU ---
            if estado_atual == ESTADO_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    btn_novo = pygame.Rect(260, 250, 320, 50)
                    btn_pont = pygame.Rect(260, 320, 320, 50)
                    btn_tema = pygame.Rect(260, 390, 320, 50)
                    btn_replay = pygame.Rect(260, 460, 320, 50)
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
                    elif btn_replay.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_PGN_SELECT
                    elif btn_som.collidepoint(event.pos):
                        sound_manager.enabled = not sound_manager.enabled
                        if sound_manager.enabled: sound_manager.play('menu')

                    btn_puzzle = pygame.Rect(260, 530, 320, 50) # Embaixo dos outros, ajuste o Y se precisar
                    if btn_puzzle.collidepoint(event.pos):
                        # INICIAR PUZZLE
                        p = puzzle_manager.get_random_puzzle()
                        if p:
                            engine.board.set_fen(p['fen'])
                            # Vira o tabuleiro se for a vez das Pretas jogarem
                            display_board.set_flip(not engine.board.turn)
                            puzzle_info = f"{p['description']} (Rating: {p['rating']})"
                            feedback_puzzle = "Encontre o melhor lance!"
                            estado_atual = ESTADO_PUZZLE
                            sound_manager.play('menu')

            # --- ESTADO: PGN SELECT ---
            elif estado_atual == ESTADO_PGN_SELECT:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos
                    arquivos = pgn_manager.list_files()
                    y_start = 120
                    
                    # Clique na lista
                    for i, arq in enumerate(arquivos):
                        if i > 10: break
                        rect = pygame.Rect(220, y_start + i*45, 400, 40)
                        if rect.collidepoint(mouse_pos):
                            sim_moves, sim_headers = pgn_manager.load_game_moves(arq)
                            engine.board.reset()
                            sim_index = 0
                            sim_auto = False
                            sim_timer = 0
                            if sim_moves:
                                estado_atual = ESTADO_SIMULACAO
                                sound_manager.play('menu')

                    # Botões inferiores
                    btn_abrir = pygame.Rect(220, 500, 200, 40)
                    btn_voltar = pygame.Rect(440, 500, 200, 40)

                    if btn_voltar.collidepoint(mouse_pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_MENU
                    elif btn_abrir.collidepoint(mouse_pos):
                        try:
                            root = tk.Tk()
                            root.withdraw()
                            root.attributes('-topmost', True)
                            file_path = filedialog.askopenfilename(title="Selecione PGN", filetypes=[("PGN", "*.pgn"), ("All", "*.*")])
                            root.destroy()
                            if file_path:
                                f = open(file_path, "r", encoding="utf-8")
                                game = chess.pgn.read_game(f)
                                if game:
                                    sim_moves = [m for m in game.mainline_moves()]
                                    sim_headers = dict(game.headers)
                                    f.close()
                                    if sim_moves:
                                        engine.board.reset()
                                        sim_index = 0
                                        sim_auto = False
                                        estado_atual = ESTADO_SIMULACAO
                                        sound_manager.play('menu')
                        except Exception as e:
                            print(f"Erro: {e}")

            # --- ESTADO: SIMULAÇÃO ---
            elif estado_atual == ESTADO_SIMULACAO:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        if sim_index < len(sim_moves):
                            move = sim_moves[sim_index]
                            realizar_jogada(engine, move, display_board, sound_manager)
                            sim_index += 1
                            sim_auto = False
                    elif event.key == pygame.K_LEFT:
                        if sim_index > 0:
                            engine.board.pop()
                            sim_index -= 1
                            sim_auto = False
                            sound_manager.play('move')
                    elif event.key == pygame.K_SPACE:
                        sim_auto = not sim_auto
                    elif event.key == pygame.K_ESCAPE:
                        engine.start()
                        estado_atual = ESTADO_PGN_SELECT

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    # Botões do player
                    btns = [
                        pygame.Rect(670, 220, 30, 30), # <<
                        pygame.Rect(710, 220, 30, 30), # <
                        pygame.Rect(750, 220, 40, 30), # Play
                        pygame.Rect(800, 220, 30, 30), # >
                        pygame.Rect(840, 220, 30, 30), # >>
                        pygame.Rect(670, 260, 160, 30) # Speed
                    ]
                    if btns[0].collidepoint(mx, my): # Reset
                        while sim_index > 0: engine.board.pop(); sim_index -= 1
                        sim_auto = False; sound_manager.play('move')
                    elif btns[1].collidepoint(mx, my): # Prev
                        if sim_index > 0: engine.board.pop(); sim_index -= 1; sim_auto = False; sound_manager.play('move')
                    elif btns[2].collidepoint(mx, my): # Pause
                        sim_auto = not sim_auto
                    elif btns[3].collidepoint(mx, my): # Next
                        if sim_index < len(sim_moves):
                            move = sim_moves[sim_index]
                            realizar_jogada(engine, move, display_board, sound_manager)
                            sim_index += 1; sim_auto = False
                    elif btns[4].collidepoint(mx, my): # End
                        while sim_index < len(sim_moves):
                            realizar_jogada(engine, sim_moves[sim_index], display_board, sound_manager)
                            sim_index += 1
                        sim_auto = False
                    elif btns[5].collidepoint(mx, my): # Speed
                        if sim_speed <= 200: sim_speed = 1000
                        else: sim_speed = 200

            # --- ESTADO: ESCOLHA COR ---
            elif estado_atual == ESTADO_ESCOLHA_COR:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    start_x = 220
                    # Dificuldade
                    for i in range(4):
                        r = pygame.Rect(start_x + i*105, 150, 95, 40)
                        if r.collidepoint(event.pos):
                            dificuldade = i + 1
                            sound_manager.play('move')
                    # Tempo
                    tempos_valores = [300, 600, None]
                    for i, val in enumerate(tempos_valores):
                        r = pygame.Rect(start_x + i*140, 250, 130, 40)
                        if r.collidepoint(event.pos):
                            tempo_escolhido = val
                            sound_manager.play('move')
                    # Botões Jogar
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
                        if engine.board.turn == chess.WHITE:
                            move = get_best_move(engine.board, dificuldade)
                            if move:
                                engine.board.push(move)
                                tocar_som_acao(engine.board, move, sound_manager, acao='move')

            # --- ESTADO: TEMA ---
            elif estado_atual == ESTADO_TEMA:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    btn_voltar = pygame.Rect(320, 520, 200, 44)
                    if btn_voltar.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_MENU
                    
                    temas_lista = ['classico', 'torneio', 'dark', 'retro']
                    for i, tema in enumerate(temas_lista):
                        btn_rect = pygame.Rect(220, 180 + i*80, 400, 60)
                        if btn_rect.collidepoint(event.pos):
                            tema_atual = tema
                            display_board.set_tema(tema)
                            sound_manager.play('menu')

            # --- ESTADO: JOGANDO ---
            elif estado_atual == ESTADO_JOGANDO and not aguardando_ia:
                # Atalhos
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        if len(engine.board.move_stack) >= 2:
                            display_board.active_animation = None
                            engine.board.pop(); engine.board.pop()
                            selecionado = None; sound_manager.play('undo')
                    elif event.key == pygame.K_h:
                        move = get_best_move(engine.board, dificuldade)
                        if move:
                            selecionado = move.from_square
                            ultima_dica_ia = f"Dica: {chess.square_name(move.from_square)}->{chess.square_name(move.to_square)}"
                            ultima_dica_move = move
                            sound_manager.play('hint')
                    elif event.key == pygame.K_s:
                        if (pygame.key.get_mods() & pygame.KMOD_CTRL): # Ctrl+S = Salvar
                            result = engine.board.result()
                            nome = pgn_manager.save_game(engine.board, "Brancas" if jogador_brancas else "IA", "IA" if jogador_brancas else "Pretas", result)
                            
                            # --- CÓDIGO NOVO ---
                            aviso_texto = "Partida Salva com Sucesso!"
                            aviso_timer = pygame.time.get_ticks() + 2500 # Mostra por 2.5 segundos
                            # -------------------
                            
                            print(f"Salvo: {nome}")
                            sound_manager.play('menu')
                        else: # S = Som
                            sound_manager.enabled = not sound_manager.enabled

                # Cliques do Jogo
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Lógica de Promoção
                    if promocao_pendente and quadrado_promocao is not None:
                        # ... (lógica de botões de promoção simplificada)
                        col = chess.square_file(quadrado_promocao)
                        row = 7 - chess.square_rank(quadrado_promocao)
                        if display_board.is_flipped: col, row = 7-col, 7-row
                        menu_x, menu_y = col * 80, row * 80
                        if menu_y > 400: menu_y -= 200
                        
                        pecas = [(chess.QUEEN, 0), (chess.ROOK, 1), (chess.BISHOP, 2), (chess.KNIGHT, 3)]
                        for ptype, idx in pecas:
                            r = pygame.Rect(menu_x+10, menu_y + idx*50, 60, 50)
                            if r.collidepoint(event.pos):
                                move = chess.Move(move_promocao_pendente.from_square, move_promocao_pendente.to_square, promotion=ptype)
                                realizar_jogada(engine, move, display_board, sound_manager)
                                eval_bar.update(evaluate_board(engine.board))
                                selecionado = None; promocao_pendente = False; aguardando_ia = True
                        continue

                    # Lógica de Movimento
                    mouse_x, mouse_y = event.pos
                    if mouse_x < 640:
                        c = mouse_x // 80
                        r = mouse_y // 80
                        if display_board.is_flipped: c, r = 7-c, 7-r
                        if 0 <= c <= 7 and 0 <= r <= 7:
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
                                    if chess.Move(selecionado, square, promotion=chess.QUEEN) in engine.board.legal_moves:
                                        promocao_pendente = True
                                        move_promocao_pendente = move
                                        cor_promocao_pendente = engine.board.piece_at(selecionado).color
                                        quadrado_promocao = square
                                        continue
                                
                                if move in engine.board.legal_moves:
                                    realizar_jogada(engine, move, display_board, sound_manager)
                                    eval_bar.update(evaluate_board(engine.board))
                                    selecionado = None; aguardando_ia = True
                                    ultima_dica_move = None  # Limpa seta de dica após jogada
                                else:
                                    p = engine.board.piece_at(square)
                                    if p and p.color == (chess.WHITE if jogador_brancas else chess.BLACK):
                                        selecionado = square; sound_manager.play('move')
                                    else:
                                        selecionado = None

            # --- ESTADO: INPUT NOME ---
            elif estado_atual == ESTADO_INPUT_NOME:
                res = input_nome.handle_event(event)
                if res == 'submit':
                    score_manager.save_score(input_nome.text, pontuacao_final, "00:00")
                    estado_atual = ESTADO_RANKING

            # --- ESTADO: PUZZLE ---
            elif estado_atual == ESTADO_PUZZLE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        estado_atual = ESTADO_MENU
                        engine.start()
                        puzzle_hint_move = None # Limpa dica ao sair
                    
                    # --- DICA (H) ---
                    elif event.key == pygame.K_h:
                        puzzle_hint_move = puzzle_manager.get_solution_move()
                        sound_manager.play('hint')

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Se o jogador clicar para tentar mover, limpe a dica para não poluir
                    puzzle_hint_move = None 
                    
                    # ... (Copie a lógica de clique do ESTADO_JOGANDO aqui, mas com validação diferente) ...
                    mouse_x, mouse_y = event.pos
                    if mouse_x < 640:
                        c = mouse_x // 80
                        r = mouse_y // 80
                        if display_board.is_flipped: c, r = 7-c, 7-r
                        if 0 <= c <= 7 and 0 <= r <= 7:
                            square = chess.square(c, 7 - r)
                            
                            if selecionado is None:
                                p = engine.board.piece_at(square)
                                if p and p.color == engine.board.turn: # Só pode selecionar a cor da vez
                                    selecionado = square
                                    sound_manager.play('move')
                            else:
                                move = chess.Move(selecionado, square)
                                # Promoção automática para Rainha em puzzles para simplificar
                                if engine.board.piece_at(selecionado).piece_type == chess.PAWN and chess.square_rank(square) in [0, 7]:
                                    move.promotion = chess.QUEEN

                                if move in engine.board.legal_moves:
                                    # --- VALIDAÇÃO DO PUZZLE ---
                                    correto, acabou = puzzle_manager.check_move(move)
                                    
                                    if correto:
                                        # Lance Certo!
                                        realizar_jogada(engine, move, display_board, sound_manager)
                                        selecionado = None
                                        
                                        if acabou:
                                            feedback_puzzle = "PUZZLE RESOLVIDO!"
                                            sound_manager.play('game_over')
                                            # Aqui você pode carregar outro puzzle automaticamente após 2s
                                        else:
                                            feedback_puzzle = "Correto! Continue..."
                                            # Oponente responde instantaneamente
                                            resp = puzzle_manager.get_next_opponent_move()
                                            if resp:
                                                realizar_jogada(engine, resp, display_board, sound_manager)
                                    else:
                                        # Lance Errado!
                                        feedback_puzzle = "Errado. Tente de novo."
                                        sound_manager.play('defeat')
                                        selecionado = None
                                else:
                                    selecionado = None

        # --- IA ---
        if estado_atual == ESTADO_JOGANDO and aguardando_ia and not promocao_pendente:
            if not engine.is_game_over():
                move = get_best_move(engine.board, dificuldade)
                if move:
                    realizar_jogada(engine, move, display_board, sound_manager)
                    eval_bar.update(evaluate_board(engine.board))
                aguardando_ia = False

        # --- CHECAGEM DE FIM DE JOGO ---
        if estado_atual == ESTADO_JOGANDO and engine.is_game_over():
            engine.stop()
            v = engine.get_winner()
            eh_vitoria = (v == ('white' if jogador_brancas else 'black'))
            score_manager.update_stats('win' if eh_vitoria else ('loss' if v != 'draw' else 'draw'))
            pontuacao_final = score_manager.calcular_pontuacao(eh_vitoria, calcular_material(engine.board, jogador_brancas), engine.get_game_duration())
            if eh_vitoria: sound_manager.play('game_over')
            else: sound_manager.play('defeat')
            
            if score_manager.check_is_highscore(pontuacao_final):
                input_nome.text = ""; input_nome.active = True
                estado_atual = ESTADO_INPUT_NOME
            else:
                estado_atual = ESTADO_RANKING

        # -------------------------------------------------
        # --- RENDERIZAÇÃO (DESENHO) ---
        # -------------------------------------------------
        screen.fill((40, 40, 40))

        if estado_atual == ESTADO_MENU:
            lbl = fonte_titulo.render("PyChess Desktop", True, (255,255,255))
            screen.blit(lbl, (840//2 - lbl.get_width()//2, 120))
            
            # Botões
            btn_novo = pygame.Rect(260, 250, 320, 50)
            btn_pont = pygame.Rect(260, 320, 320, 50)
            btn_tema = pygame.Rect(260, 390, 320, 50)
            btn_replay = pygame.Rect(260, 460, 320, 50)
            btn_som = pygame.Rect(760, 20, 60, 40)
            
            for btn, txt in [(btn_novo, "Novo Jogo"), (btn_pont, "Pontuações"), (btn_tema, "Temas"), (btn_replay, "Replay")]:
                pygame.draw.rect(screen, (70, 130, 180), btn, border_radius=12)
                pygame.draw.rect(screen, (200, 200, 200), btn, 2, border_radius=12)
                lbl = fonte_btn.render(txt, True, (255,255,255))
                screen.blit(lbl, (btn.centerx - lbl.get_width()//2, btn.centery - lbl.get_height()//2))

            btn_puzzle = pygame.Rect(260, 530, 320, 50) # Embaixo dos outros, ajuste o Y se precisar
            pygame.draw.rect(screen, (150, 100, 200), btn_puzzle, border_radius=12) # Roxo
            pygame.draw.rect(screen, (200, 200, 200), btn_puzzle, 2, border_radius=12)
            lbl_puzz = fonte_btn.render("Treino Tático", True, (255,255,255))
            screen.blit(lbl_puzz, (btn_puzzle.centerx - lbl_puzz.get_width()//2, btn_puzzle.centery - lbl_puzz.get_height()//2))
            
            # Som
            cor = (100,200,100) if sound_manager.enabled else (200,100,100)
            pygame.draw.rect(screen, cor, btn_som, border_radius=5)
            screen.blit(fonte_small.render("SOM", True, (255,255,255)), (btn_som.x+10, btn_som.y+10))
            
            # Stats
            s = score_manager.load_stats()
            rate = score_manager.get_win_rate()
            msg = f"V: {s['wins']}  D: {s['losses']}  E: {s['draws']} ({rate:.1f}%)"
            screen.blit(fonte_small.render(msg, True, (150,150,150)), (280, 530))

        elif estado_atual == ESTADO_PGN_SELECT:
            lbl = fonte_titulo.render("Selecione uma Partida", True, (255,255,255))
            screen.blit(lbl, (280, 50))
            
            arquivos = pgn_manager.list_files()
            y_start = 120
            if not arquivos:
                screen.blit(fonte_small.render("Nenhum arquivo em data/pgn/", True, (150,150,150)), (250, 200))
            
            mouse_pos = pygame.mouse.get_pos()
            for i, arq in enumerate(arquivos):
                if i > 10: break
                rect = pygame.Rect(220, y_start + i*45, 400, 40)
                cor = (80, 100, 120) if rect.collidepoint(mouse_pos) else (60, 80, 100)
                pygame.draw.rect(screen, cor, rect, border_radius=5)
                screen.blit(fonte_small.render(arq, True, (255,255,255)), (rect.x+10, rect.y+10))
            
            btn_abrir = pygame.Rect(220, 500, 200, 40)
            pygame.draw.rect(screen, (60, 120, 60), btn_abrir, border_radius=8)
            lbl = fonte_btn.render("Abrir Arquivo", True, (255,255,255))
            screen.blit(lbl, (btn_abrir.centerx - lbl.get_width()//2, btn_abrir.y+5))

            btn_voltar = pygame.Rect(440, 500, 200, 40)
            pygame.draw.rect(screen, (150, 50, 50), btn_voltar, border_radius=8)
            lbl = fonte_btn.render("Voltar", True, (255,255,255))
            screen.blit(lbl, (btn_voltar.centerx - lbl.get_width()//2, btn_voltar.y+5))

        elif estado_atual == ESTADO_SIMULACAO:
            display_board.draw(engine.board)
            # Desenha seta do movimento atual do replay
            if sim_index > 0 and sim_index <= len(sim_moves):
                move = sim_moves[sim_index-1]
                display_board.draw_arrow(move.from_square, move.to_square, color=(255,140,0,180), width=12)
            eval_bar.draw(screen)
            
            # Painel Lateral de Simulação
            pygame.draw.rect(screen, (50, 50, 60), (660, 0, 180, 640))
            y_info = 20
            screen.blit(fonte_small.render(f"Brancas: {sim_headers.get('White','?')}", True, (200,200,200)), (670, y_info))
            screen.blit(fonte_small.render(f"Pretas: {sim_headers.get('Black','?')}", True, (200,200,200)), (670, y_info+25))
            screen.blit(fonte_small.render(f"Res: {sim_headers.get('Result','*')}", True, (255,200,100)), (670, y_info+50))
            
            # Contador
            lbl_move = pygame.font.SysFont("consolas", 30).render(f"{sim_index}/{len(sim_moves)}", True, (255,255,0))
            screen.blit(lbl_move, (670 + 90 - lbl_move.get_width()//2, 150))
            
            # Botões Player
            bts = [
                ("<<", 670, 220), ("<", 710, 220),
                ("||" if sim_auto else ">", 750, 220),
                (">", 800, 220), (">>", 840, 220)
            ]
            for txt, bx, by in bts:
                cor = (80, 180, 80) if txt=="||" else (80, 80, 120)
                r = pygame.Rect(bx, by, 30 if txt!="||" and txt!=">" else 40, 30)
                pygame.draw.rect(screen, cor, r, border_radius=5)
                lbl = pygame.font.SysFont("arial", 18, bold=True).render(txt, True, (255,255,255))
                screen.blit(lbl, (r.centerx-lbl.get_width()//2, r.centery-lbl.get_height()//2))
            
            # Speed
            pygame.draw.rect(screen, (60,60,100), (670, 260, 160, 30), border_radius=5)
            screen.blit(fonte_small.render(f"Velocidade: {sim_speed/1000:.1f}s", True, (255,255,255)), (680, 265))
            
            # Status
            st = "REPRODUZINDO" if sim_auto else "PAUSADO"
            c = (0,255,0) if sim_auto else (255,100,100)
            screen.blit(fonte_btn.render(st, True, c), (670, 100))

        elif estado_atual == ESTADO_TEMA:
            lbl = fonte_titulo.render("Escolha o Tema", True, (255,255,255))
            screen.blit(lbl, (840//2 - lbl.get_width()//2, 80))
            temas = ['classico', 'torneio', 'dark', 'retro']
            labels = ['Clássico', 'Torneio', 'Dark Mode', 'Retrô']
            for i, t in enumerate(temas):
                r = pygame.Rect(220, 180 + i*80, 400, 60)
                c = (60, 100, 160) if tema_atual == t else (80, 80, 80)
                pygame.draw.rect(screen, c, r, border_radius=10)
                lbl = fonte_btn.render(labels[i], True, (255,255,255))
                screen.blit(lbl, (r.centerx-lbl.get_width()//2, r.centery-lbl.get_height()//2))
            
            btn_voltar = pygame.Rect(320, 520, 200, 44)
            pygame.draw.rect(screen, (150, 50, 50), btn_voltar, border_radius=10)
            screen.blit(fonte_btn.render("Voltar", True, (255,255,255)), (380, 525))

        elif estado_atual == ESTADO_ESCOLHA_COR:
            # Configuração
            lbl = fonte_titulo.render("Configuração", True, (255,255,255))
            screen.blit(lbl, (300, 50))
            
            # Dificuldade
            screen.blit(fonte_small.render(f"Dificuldade: {dificuldade}", True, (255,255,255)), (350, 120))
            start_x = 220
            for i in range(4):
                r = pygame.Rect(start_x + i*105, 150, 95, 40)
                c = (0, 200, 0) if dificuldade == i+1 else (100,100,100)
                pygame.draw.rect(screen, c, r, border_radius=5)
                screen.blit(fonte_small.render(str(i+1), True, (255,255,255)), (r.x+40, r.y+10))
            
            # Tempo
            screen.blit(fonte_small.render(f"Tempo: {tempo_escolhido}", True, (255,255,255)), (350, 220))
            tls = ["5 min", "10 min", "Livre"]
            for i, val in enumerate([300, 600, None]):
                r = pygame.Rect(start_x + i*140, 250, 130, 40)
                c = (0, 200, 0) if tempo_escolhido == val else (100,100,100)
                pygame.draw.rect(screen, c, r, border_radius=5)
                screen.blit(fonte_small.render(tls[i], True, (255,255,255)), (r.x+20, r.y+10))
            
            # Jogar
            b1 = pygame.Rect(180, 330, 220, 50)
            b2 = pygame.Rect(420, 330, 220, 50)
            pygame.draw.rect(screen, (200, 200, 200), b1, border_radius=10)
            screen.blit(fonte_btn.render("Brancas", True, (0,0,0)), (230, 340))
            pygame.draw.rect(screen, (20, 20, 20), b2, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), b2, 2, border_radius=10)
            screen.blit(fonte_btn.render("Pretas", True, (255,255,255)), (480, 340))

        elif estado_atual == ESTADO_JOGANDO:
            display_board.draw(engine.board)
            eval_bar.draw(screen)
            if selecionado is not None:
                c = chess.square_file(selecionado)
                r = 7 - chess.square_rank(selecionado)
                if display_board.is_flipped: c, r = 7-c, 7-r
                s = pygame.Surface((80, 80)); s.set_alpha(100); s.fill((255, 255, 0))
                screen.blit(s, (c*80, r*80))
                display_board.draw_valid_moves(engine.board, selecionado)
            
            # Painel Lateral Jogo
            pygame.draw.rect(screen, (60, 60, 60), (660, 0, 180, 640))
            def fmt(t): return "--:--" if engine.time_limit is None else f"{int(t)//60:02}:{int(t)%60:02}"
            
            # Relógios
            pygame.draw.rect(screen, (30, 30, 30), (670, 20, 160, 50), border_radius=5)
            screen.blit(fonte_btn.render(fmt(engine.black_time), True, (255,50,50) if engine.black_time<30 else (255,255,255)), (700, 30))
            pygame.draw.rect(screen, (200, 200, 200), (670, 400, 160, 50), border_radius=5)
            screen.blit(fonte_btn.render(fmt(engine.white_time), True, (0,0,0)), (700, 410))
            
            # --- CÓDIGO NOVO: LEGENDA DE ATALHOS ---
            y_legenda = 500
            fonte_legenda = pygame.font.SysFont("arial", 14)
            
            # Verifica cor do som dinamicamente
            status_som = "ON" if sound_manager.enabled else "OFF"
            cor_som = (100, 255, 100) if sound_manager.enabled else (255, 100, 100)

            atalhos = [
                ("H - Dica da IA", (180, 180, 180)),
                ("Ctrl+Z - Desfazer", (180, 180, 180)),
                ("Ctrl+S - Salvar PGN", (180, 180, 180)),
                ("M - Menu Principal", (180, 180, 180)),
                (f"S - Som: {status_som}", cor_som)
            ]

            # Linha divisória sutil
            pygame.draw.line(screen, (100, 100, 100), (670, 480), (830, 480), 1)

            for texto, cor in atalhos:
                surf = fonte_legenda.render(texto, True, cor)
                screen.blit(surf, (670, y_legenda))
                y_legenda += 22 # Espaçamento entre linhas
            # ---------------------------------------

            # Dica e Menu Promoção
            if ultima_dica_ia:
                screen.blit(fonte_small.render("Dica IA:", True, (100,255,100)), (670, 200))
                screen.blit(fonte_small.render(ultima_dica_ia.replace("Dica: ",""), True, (200,200,200)), (670, 230))
                # Desenha seta de dica
                if ultima_dica_move:
                    display_board.draw_arrow(ultima_dica_move.from_square, ultima_dica_move.to_square, color=(0,180,255,160), width=10)
                    # Limpa a dica se sair do estado jogando
                    if estado_atual != ESTADO_JOGANDO:
                        ultima_dica_move = None
            
            if promocao_pendente and quadrado_promocao is not None:
                c = chess.square_file(quadrado_promocao)
                r = 7 - chess.square_rank(quadrado_promocao)
                if display_board.is_flipped: c, r = 7-c, 7-r
                mx, my = c*80, r*80
                if my > 400: my -= 200
                pygame.draw.rect(screen, (50, 50, 50), (mx, my, 80, 200))
                pygame.draw.rect(screen, (255,255,255), (mx, my, 80, 200), 2)
                pecas = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
                for i, p in enumerate(pecas):
                    img = display_board.images.get((p, cor_promocao_pendente))
                    if img: screen.blit(pygame.transform.scale(img, (60,60)), (mx+10, my + i*50))

        elif estado_atual == ESTADO_PUZZLE:
            display_board.draw(engine.board)
            
            # --- DESENHA A DICA ---
            if puzzle_hint_move:
                display_board.draw_arrow(puzzle_hint_move, color=(0, 255, 0))
            # ----------------------
            
            # Destaque da seleção (igual ao jogo)
            if selecionado is not None:
                c = chess.square_file(selecionado)
                r = 7 - chess.square_rank(selecionado)
                if display_board.is_flipped: c, r = 7-c, 7-r
                s = pygame.Surface((80, 80)); s.set_alpha(100); s.fill((255, 255, 0))
                screen.blit(s, (c*80, r*80))
            
            # Painel Lateral do Puzzle
            pygame.draw.rect(screen, (60, 50, 70), (660, 0, 180, 640)) # Um roxo escuro para diferenciar
            
            # Título
            lbl = fonte_btn.render("Puzzle", True, (255, 255, 255))
            screen.blit(lbl, (670 + 90 - lbl.get_width()//2, 30))
            
            # Info
            # Quebra de linha simples para descrição
            palavras = puzzle_info.split()
            y_txt = 80
            linha = ""
            for p in palavras:
                if len(linha + p) > 20: # Limite manual simples
                    screen.blit(fonte_small.render(linha, True, (200, 200, 200)), (670, y_txt))
                    y_txt += 25
                    linha = p + " "
                else:
                    linha += p + " "
            screen.blit(fonte_small.render(linha, True, (200, 200, 200)), (670, y_txt))

            # Feedback (Grande e colorido)
            cor_feed = (100, 255, 100) if "Correto" in feedback_puzzle or "RESOLVIDO" in feedback_puzzle else (255, 100, 100)
            if "Encontre" in feedback_puzzle: cor_feed = (255, 255, 255)
            
            lbl_feed = fonte_small.render(feedback_puzzle, True, cor_feed)
            screen.blit(lbl_feed, (670, 300))

            # Botão Próximo Puzzle (Só aparece se resolver)
            if "RESOLVIDO" in feedback_puzzle:
                btn_prox = pygame.Rect(670, 400, 160, 50)
                pygame.draw.rect(screen, (100, 200, 100), btn_prox, border_radius=8)
                l = fonte_btn.render("Próximo", True, (255,255,255))
                screen.blit(l, (btn_prox.centerx - l.get_width()//2, btn_prox.centery - l.get_height()//2))
                
                # Detecta clique aqui mesmo (hack rápido para não criar evento lá em cima só pra isso)
                if pygame.mouse.get_pressed()[0]:
                    mx, my = pygame.mouse.get_pos()
                    if btn_prox.collidepoint(mx, my):
                        # Carrega novo puzzle
                        p = puzzle_manager.get_random_puzzle()
                        if p:
                            engine.board.set_fen(p['fen'])
                            display_board.set_flip(not engine.board.turn)
                            puzzle_info = f"{p['description']} ({p['rating']})"
                            feedback_puzzle = "Encontre o melhor lance!"
                            pygame.time.wait(200) # Evita clique duplo

        elif estado_atual == ESTADO_RANKING:
            scores = score_manager.load_scores()
            view = LeaderboardView(pygame.font.SysFont("consolas", 20), scores)
            view.draw(screen, pos=(150, 100))
            screen.blit(fonte_small.render("Pressione M para voltar", True, (150,150,150)), (280, 550))

        elif estado_atual == ESTADO_INPUT_NOME:
            msg = fonte_btn.render(f"Recorde! Pontos: {pontuacao_final}", True, (255,255,255))
            screen.blit(msg, (200, 200))
            input_nome.draw(screen)

        # --- RENDERIZAÇÃO DE AVISOS (TOAST) ---
        if aviso_texto and pygame.time.get_ticks() < aviso_timer:
            # Cria uma superfície para o fundo (para poder usar transparência/alpha)
            largura_box = 400
            altura_box = 60
            s = pygame.Surface((largura_box, altura_box))
            s.set_alpha(220) # 0-255 (Transparência)
            s.fill((30, 30, 30)) # Fundo escuro
            
            # Posiciona no centro superior da tela
            x_pos = 840 // 2 - largura_box // 2
            y_pos = 100
            
            screen.blit(s, (x_pos, y_pos))
            
            # Borda Verde Elegante
            pygame.draw.rect(screen, (50, 200, 100), (x_pos, y_pos, largura_box, altura_box), 2, border_radius=5)
            
            # Ícone ou Símbolo (Opcional, usando texto simples aqui)
            txt_surf = fonte_btn.render(aviso_texto, True, (255, 255, 255))
            screen.blit(txt_surf, (x_pos + (largura_box - txt_surf.get_width()) // 2, y_pos + (altura_box - txt_surf.get_height()) // 2))
            
        elif pygame.time.get_ticks() >= aviso_timer:
            aviso_texto = "" # Limpa a memória quando o tempo acaba

        pygame.display.flip()

if __name__ == "__main__":
    main()