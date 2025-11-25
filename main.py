import sys
import os
import subprocess
import pygame
import chess
import tkinter as tk
from tkinter import filedialog
from src.config import *
from src.ui import TextInput, LeaderboardView, DisplayBoard, EvaluationBar, Slider
from src.engine import Engine
from src.scoring import ScoreManager
from src.ai import get_best_move, evaluate_board
from src.sound import SoundManager
from src.pgn_manager import PGNManager
from src.puzzle_manager import PuzzleManager
from src.skin_manager import SkinManager

from src.config_manager import ConfigManager
from src.tutorial_manager import TutorialManager

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
ESTADO_PUZZLE = 8
ESTADO_EDITOR = 9
ESTADO_CONFIG = 10 # Novo ID de estado
ESTADO_GAME_OVER = 11 
ESTADO_TUTORIAL = 12 # Novo ID 
ESTADO_CREDITOS = 13 # <--- NOVO

WHITE = (255, 255, 255)

def desenhar_texto_quebrado(screen, text, color, rect, font, aa=True, bkg=None):
    """Desenha texto quebrando linhas automaticamente dentro de um retângulo."""
    y = rect.top
    lineSpacing = -2

    # Pega a altura da fonte
    fontHeight = font.size("Tg")[1]

    while text:
        i = 1
        # Determina se a linha inteira cabe na largura
        if y + fontHeight > rect.bottom:
            break

        # Tenta encaixar palavra por palavra
        while font.size(text[:i])[0] < rect.width and i < len(text):
            i += 1

        # Se o texto não couber, volta para o último espaço
        if i < len(text): 
            i = text.rfind(" ", 0, i) + 1

        # Renderiza a linha
        if bkg:
            image = font.render(text[:i], 1, color, bkg)
            image.set_colorkey(bkg)
        else:
            image = font.render(text[:i], aa, color)

        screen.blit(image, (rect.left, y))
        y += fontHeight + lineSpacing

        # Remove o texto já desenhado
        text = text[i:]
        
    return text

def main():
    pygame.init()
    
    config_manager = ConfigManager()
    
    # --- INICIALIZAÇÃO SEGURA (Safe Boot) ---
    # 1. Cria a janela em modo "windowed" primeiro com SCALED (garante que a janela exista)
    flags = pygame.SCALED 
    # vsync=1 é importante para suavidade
    screen = pygame.display.set_mode((840, 640), flags, vsync=1)

    # 2. Se a configuração salva pedir Fullscreen, alternamos agora
    # Isso evita o travamento de "boot direto" em drivers sensíveis
    if config_manager.get("fullscreen"):
        pygame.display.toggle_fullscreen()
    
    pygame.display.set_caption("My Chess")

    # --- ÍCONE DA JANELA (NOVO) ---
    try:
        # Caminho para o Rei Branco
        icon_path = os.path.join("assets", "images", "pieces", "w_k.png")
        
        # Carrega e define
        if os.path.exists(icon_path):
            icon_surface = pygame.image.load(icon_path)
            pygame.display.set_icon(icon_surface)
    except Exception as e:
        print(f"Aviso: Não foi possível carregar o ícone. {e}")
    # ------------------------------

    clock = pygame.time.Clock()

    # Inicialização
    engine = Engine()
    engine.start()
    score_manager = ScoreManager()
    sound_manager = SoundManager()

    # Configura som inicial
    vol_inicial = config_manager.get("volume_master")
    sound_manager.set_volume(vol_inicial)
    
    # UI Components
    skin_manager = SkinManager() # Escaneia as pastas
    current_skin_id = 'default'
    
    # Passa os dados da skin inicial
    display_board = DisplayBoard(screen, tamanho_quadrado=80, skin_data=skin_manager.get_skin_data('default'))
    eval_bar = EvaluationBar(pygame.Rect(640, 0, 20, 640))
    input_nome = TextInput(pygame.font.SysFont("consolas", 30), rect=pygame.Rect(170, 300, 300, 50))
    
    # Sliders para Casas Claras (R, G, B) e Escuras (R, G, B)
    sliders_editor = [
        # Claras
        Slider(250, 150, 200, 15, "R", 240/255, (200, 50, 50), display_mode='val'),
        Slider(250, 190, 200, 15, "G", 217/255, (50, 200, 50), display_mode='val'),
        Slider(250, 230, 200, 15, "B", 181/255, (50, 50, 255), display_mode='val'),
        # Escuras
        Slider(250, 320, 200, 15, "R", 181/255, (200, 50, 50), display_mode='val'),
        Slider(250, 360, 200, 15, "G", 136/255, (50, 200, 50), display_mode='val'),
        Slider(250, 400, 200, 15, "B", 99/255, (50, 50, 255), display_mode='val')
    ]
    editor_nome_input = TextInput(pygame.font.SysFont("consolas", 24), max_length=15, rect=pygame.Rect(250, 480, 300, 40))
    editor_nome_input.text = "Meu Tema"
    
    # Componentes da Tela de Config
    slider_volume = Slider(270, 200, 300, 20, "Volume Geral", initial_pct=vol_inicial)
    
    # Fontes
    fonte_titulo = pygame.font.SysFont("arial", 40, bold=True)
    fonte_btn = pygame.font.SysFont("arial", 28)
    fonte_small = pygame.font.SysFont("arial", 20)

    estado_atual = ESTADO_MENU

    # Variáveis para a tela de Game Over
    texto_fim_jogo = ""
    subtexto_fim_jogo = ""
    cor_fim_jogo = (255, 255, 255)

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
    tutorial_manager = TutorialManager()
    tutorial_concluido = False # Para mostrar mensagem de sucesso
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

    # --- Botões do Menu (definidos uma vez) ---
    btn_x = 480
    btn_w = 280
    btn_h = 55
    spacing = 65
    start_y = 100
    btn_novo   = pygame.Rect(btn_x, start_y + 0*spacing, btn_w, btn_h)
    btn_replay = pygame.Rect(btn_x, start_y + 1*spacing, btn_w, btn_h)
    btn_puzzle = pygame.Rect(btn_x, start_y + 2*spacing, btn_w, btn_h)
    btn_tema   = pygame.Rect(btn_x, start_y + 3*spacing, btn_w, btn_h)
    btn_pont   = pygame.Rect(btn_x, start_y + 4*spacing, btn_w, btn_h)
    btn_opcoes = pygame.Rect(btn_x, start_y + 5*spacing, btn_w, btn_h)
    btn_tutorial = pygame.Rect(btn_x, start_y + 6*spacing, btn_w, btn_h) # NOVO
    btn_som    = pygame.Rect(780, 20, 40, 40)

    def toggle_fullscreen():
        # 1. Salva o estado atual
        is_full = not config_manager.get("fullscreen")
        config_manager.set("fullscreen", is_full)
        
        # 2. Define as flags
        # IMPORTANTE: Sempre usamos SCALED para manter a proporção 840x640
        flags = pygame.SCALED 
        if is_full:
            flags |= pygame.FULLSCREEN
        
        # 3. Recria a janela de forma segura
        try:
            # Atualiza a variável 'screen' do escopo de main
            nonlocal screen 
            
            # Pequeno delay para o SO processar a mudança anterior se houver spam de F11
            pygame.time.wait(100) 
            
            screen = pygame.display.set_mode((840, 640), flags, vsync=1)
            
            # Força um evento de resize para garantir que o conteúdo se ajuste
            pygame.event.post(pygame.event.Event(pygame.VIDEORESIZE, size=(840, 640), w=840, h=640))
            
        except Exception as e:
            print(f"Erro ao trocar tela: {e}")
            # Fallback de emergência: volta para janela normal
            screen = pygame.display.set_mode((840, 640), pygame.SCALED)
            config_manager.set("fullscreen", False)

        return is_full

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

            # --- ATALHO F11 (Tela Cheia) ---
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                toggle_fullscreen()
            # -------------------------------

            # Atalho Global M para Menu
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m and estado_atual != ESTADO_INPUT_NOME:
                engine.start()
                estado_atual = ESTADO_MENU
                sound_manager.play('menu')
                continue

            # --- ESTADO: MENU ---
            if estado_atual == ESTADO_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_novo.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_ESCOLHA_COR
                    elif btn_replay.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_PGN_SELECT
                    elif btn_puzzle.collidepoint(event.pos):
                        p = puzzle_manager.get_random_puzzle()
                        if p:
                            engine.board.set_fen(p['fen'])
                            display_board.set_flip(not engine.board.turn)
                            puzzle_info = f"{p['description']} (Rating: {p['rating']})"
                            feedback_puzzle = "Encontre o melhor lance!"
                            estado_atual = ESTADO_PUZZLE
                            sound_manager.play('menu')
                    elif btn_tema.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_TEMA
                    elif btn_pont.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_RANKING
                    elif btn_opcoes.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_CONFIG
                    elif btn_tutorial.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_TUTORIAL
                        lesson = tutorial_manager.get_current_lesson()
                        if lesson:
                            engine.board.set_fen(lesson['fen'])
                            # Força visão das brancas para tutorial
                            display_board.set_flip(False) 
                    elif btn_som.collidepoint(event.pos):
                        sound_manager.enabled = not sound_manager.enabled
                        if sound_manager.enabled: sound_manager.play('menu')

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
                        pygame.Rect(670, 220, 30, 30), # << (Reset)
                        pygame.Rect(700, 220, 30, 30), # < (Prev)
                        pygame.Rect(730, 220, 40, 30), # Play/Pause
                        pygame.Rect(770, 220, 30, 30), # > (Next)
                        pygame.Rect(800, 220, 30, 30), # >> (End)
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
                                realizar_jogada(engine, move, display_board, sound_manager)

            elif estado_atual == ESTADO_TUTORIAL:
                # Navegação Manual
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    
                    # Botões de Navegação (Definidos visualmente abaixo)
                    btn_prev = pygame.Rect(670, 550, 40, 40)
                    btn_next = pygame.Rect(720, 550, 40, 40)
                    btn_menu = pygame.Rect(770, 550, 40, 40)
                    
                    if btn_menu.collidepoint(mx, my):
                        estado_atual = ESTADO_MENU
                        sound_manager.play('menu')
                    elif btn_next.collidepoint(mx, my):
                        l = tutorial_manager.next_lesson()
                        if l: 
                            engine.board.set_fen(l['fen'])
                            tutorial_concluido = False
                        sound_manager.play('move')
                    elif btn_prev.collidepoint(mx, my):
                        l = tutorial_manager.prev_lesson()
                        if l: 
                            engine.board.set_fen(l['fen'])
                            tutorial_concluido = False
                        sound_manager.play('move')

                    # Lógica de Movimento (Similar ao Puzzle)
                    if mx < 640 and not tutorial_concluido:
                        c = mx // 80
                        r = my // 80
                        if display_board.is_flipped: c, r = 7-c, 7-r
                        if 0 <= c <= 7 and 0 <= r <= 7:
                            square = chess.square(c, 7 - r)
                            
                            if selecionado is None:
                                p = engine.board.piece_at(square)
                                if p and p.color == engine.board.turn:
                                    selecionado = square
                                    sound_manager.play('move')
                            else:
                                move = chess.Move(selecionado, square)
                                # Promoção automática para Rainha em puzzles para simplificar
                                piece = engine.board.piece_at(selecionado)
                                if piece and piece.piece_type == chess.PAWN and chess.square_rank(square) in [0, 7]:
                                    move.promotion = chess.QUEEN

                                if move in engine.board.legal_moves:
                                   # A função check_move deve retornar um booleano simples.
                                   # Se retornasse uma tupla (ex: (True, False)), `if (True, False)` em Python é True.
                                   # Garantimos que estamos checando o resultado booleano.
                                   is_correct = tutorial_manager.check_move(move)
                                   if isinstance(is_correct, tuple): # Medida de segurança se a função retornar tupla
                                       is_correct = is_correct[0]

                                   if is_correct:
                                       realizar_jogada(engine, move, display_board, sound_manager)
                                       tutorial_concluido = True
                                       sound_manager.play('game_over') # Sucesso
                                   else:
                                       sound_manager.play('defeat') # Errou o que o tutorial pediu
                                       selecionado = None # Deseleciona
                                else:
                                    p = engine.board.piece_at(square)
                                    if p and p.color == engine.board.turn: # Clicar em outra peça sua
                                        selecionado = square
                                        sound_manager.play('move')
                                    else:
                                        selecionado = None # Clicar em casa vazia ou peça inimiga

            elif estado_atual == ESTADO_TEMA:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    skins_disponiveis = skin_manager.get_skin_names()
                    y_start = 120
                    
                    # Checa clique na lista
                    for i, (skin_id, skin_name) in enumerate(skins_disponiveis):
                        if i > 5: break
                        rect = pygame.Rect(220, y_start + i*70, 400, 50)
                        if rect.collidepoint(event.pos):
                            current_skin_id = skin_id
                            # Carrega os dados e aplica no tabuleiro
                            dados = skin_manager.get_skin_data(skin_id)
                            display_board.set_skin(dados)
                            sound_manager.play('menu')

                    # Botão Voltar
                    btn_voltar = pygame.Rect(430, 550, 190, 40)
                    if btn_voltar.collidepoint(event.pos):
                        estado_atual = ESTADO_MENU
                        sound_manager.play('menu')
                        
                    # Botão Abrir Pasta (Quality of Life)
                    btn_folder = pygame.Rect(220, 550, 190, 40)
                    if btn_folder.collidepoint(event.pos):
                        folder_path = skin_manager.base_folder
                        try:
                            if sys.platform == "win32":
                                os.startfile(folder_path)
                            elif sys.platform == "darwin":
                                subprocess.run(["open", folder_path])
                            else: # linux
                                subprocess.run(["xdg-open", folder_path])
                        except FileNotFoundError:
                            print(f"Could not open folder '{folder_path}'. Command not found.")
                        except Exception as e:
                            print(f"Error opening folder: {e}")

                    # Adicione um botão "CRIAR NOVO"
                    btn_criar = pygame.Rect(630, 550, 150, 40)
                    if btn_criar.collidepoint(event.pos):
                        estado_atual = ESTADO_EDITOR
                        sound_manager.play('menu')
            
            elif estado_atual == ESTADO_EDITOR:
                editor_nome_input.handle_event(event)
                for sl in sliders_editor:
                    sl.handle_event(event)
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    btn_salvar = pygame.Rect(300, 550, 240, 50)
                    btn_cancelar = pygame.Rect(50, 550, 150, 50)
                    
                    if btn_salvar.collidepoint(event.pos):
                        # Pega valores
                        l_rgb = (int(sliders_editor[0].pct*255), int(sliders_editor[1].pct*255), int(sliders_editor[2].pct*255))
                        d_rgb = (int(sliders_editor[3].pct*255), int(sliders_editor[4].pct*255), int(sliders_editor[5].pct*255))
                        nome = editor_nome_input.text
                        
                        # Salva
                        new_id = skin_manager.save_new_skin(nome, l_rgb, d_rgb)
                        
                        # Aplica e volta
                        display_board.set_skin(skin_manager.get_skin_data(new_id))
                        current_skin_id = new_id
                        estado_atual = ESTADO_TEMA
                        sound_manager.play('game_over') # Sucesso
                        
                    elif btn_cancelar.collidepoint(event.pos):
                        estado_atual = ESTADO_TEMA
                        sound_manager.play('menu')

            # --- ESTADO: CONFIGURAÇÕES ---
            elif estado_atual == ESTADO_CONFIG:
                # Slider
                if slider_volume.handle_event(event):
                    # Se mexeu no slider, atualiza volume em tempo real
                    new_vol = slider_volume.pct
                    config_manager.set("volume_master", new_vol)
                    sound_manager.set_volume(new_vol) # Implementar no SoundManager depois
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Checkbox Fullscreen (Simulado com rect)
                    chk_full_rect = pygame.Rect(270, 280, 30, 30)
                    if chk_full_rect.collidepoint(event.pos):
                        toggle_fullscreen() # Usa a função unificada
                        sound_manager.play('menu')

                    # Checkbox AUTO-SAVE (NOVO)
                    chk_save_rect = pygame.Rect(270, 330, 30, 30) # Um pouco abaixo do fullscreen
                    if chk_save_rect.collidepoint(event.pos):
                        val = not config_manager.get("auto_save")
                        config_manager.set("auto_save", val)
                        sound_manager.play('menu')

                    # BOTÃO RESETAR STATS (NOVO)
                    btn_reset_rect = pygame.Rect(270, 400, 300, 45)
                    if btn_reset_rect.collidepoint(event.pos):
                        score_manager.reset_stats()
                        sound_manager.play('defeat') # Um som de impacto/aviso
                        
                        # Feedback Visual (Toast)
                        aviso_texto = "Estatísticas Zeradas!"
                        aviso_timer = pygame.time.get_ticks() + 2000

                    # BOTÃO IR PARA CRÉDITOS (NOVO)
                    # Vamos posicionar acima do Reset ou ao lado
                    btn_creditos_rect = pygame.Rect(600, 550, 150, 40) # Canto inferior direito
                    if btn_creditos_rect.collidepoint(event.pos):
                        sound_manager.play('menu')
                        estado_atual = ESTADO_CREDITOS

                    # Botão Voltar
                    btn_voltar = pygame.Rect(320, 550, 200, 40)
                    if btn_voltar.collidepoint(event.pos):
                        estado_atual = ESTADO_MENU
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

            # --- ESTADO: GAME OVER (NOVO) ---
            elif estado_atual == ESTADO_GAME_OVER:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Botão Continuar
                    btn_cont = pygame.Rect(320, 400, 200, 50)
                    if btn_cont.collidepoint(event.pos):
                        sound_manager.play('menu')
                        # Agora sim verifica se é Highscore
                        if score_manager.check_is_highscore(pontuacao_final):
                            input_nome.text = ""
                            input_nome.active = True
                            estado_atual = ESTADO_INPUT_NOME
                        else:
                            estado_atual = ESTADO_RANKING

            # --- ESTADO: CRÉDITOS ---
            elif estado_atual == ESTADO_CREDITOS:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        estado_atual = ESTADO_CONFIG
                        sound_manager.play('menu')

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    btn_voltar = pygame.Rect(320, 550, 200, 40)
                    if btn_voltar.collidepoint(event.pos):
                        estado_atual = ESTADO_CONFIG
                        sound_manager.play('menu')

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
                                piece = engine.board.piece_at(selecionado)
                                if piece and piece.piece_type == chess.PAWN and chess.square_rank(square) in [0, 7]:
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
        # --- CHECAGEM DE FIM DE JOGO ---
        if estado_atual == ESTADO_JOGANDO and engine.is_game_over():
            engine.stop()
            v = engine.get_winner()
            
            # Lógica para definir resultado
            cor_jogador = 'white' if jogador_brancas else 'black'
            
            resultado_tipo = 'loss' # Padrão
            if v == 'draw':
                resultado_tipo = 'draw'
            elif v == cor_jogador:
                resultado_tipo = 'win'
            
            # Atualiza Stats
            score_manager.update_stats(resultado_tipo)
            
            # Define Textos para a tela de Game Over
            if resultado_tipo == 'win':
                texto_fim_jogo = "VITÓRIA!"
                cor_fim_jogo = (50, 200, 50)
                sound_manager.play('game_over')
            elif resultado_tipo == 'draw':
                texto_fim_jogo = "EMPATE"
                cor_fim_jogo = (100, 100, 200)
                sound_manager.play('game_over') # Ou um som neutro
            else:
                texto_fim_jogo = "DERROTA"
                cor_fim_jogo = (200, 50, 50)
                sound_manager.play('defeat')

            # Define Subtexto (Motivo)
            if engine.winner_on_time: subtexto_fim_jogo = "Tempo Esgotado"
            elif engine.board.is_checkmate(): subtexto_fim_jogo = "Xeque-mate"
            elif engine.board.is_stalemate(): subtexto_fim_jogo = "Afogamento"
            else: subtexto_fim_jogo = "Fim de Partida"

            # --- CÁLCULO DA PONTUAÇÃO (ATUALIZADO) ---
            pontuacao_final = score_manager.calcular_pontuacao(
                resultado_tipo, 
                calcular_material(engine.board, jogador_brancas), 
                engine.get_game_duration(),
                dificuldade
            )
            # -----------------------------------------

            # Auto-Save (Lógica existente)
            if config_manager.get("auto_save"):
                nome_arquivo = pgn_manager.save_game(
                    engine.board, 
                    "Jogador" if jogador_brancas else "Computador",
                    "Computador" if jogador_brancas else "Jogador",
                    engine.board.result()
                )
                aviso_texto = "PGN Salvo Automaticamente!"
                aviso_timer = pygame.time.get_ticks() + 3000

            estado_atual = ESTADO_GAME_OVER

        # -------------------------------------------------
        # --- RENDERIZAÇÃO (DESENHO) ---
        # -------------------------------------------------
        screen.fill((40, 40, 40))

        if estado_atual == ESTADO_MENU:
            mouse_pos = pygame.mouse.get_pos()
            # 1. Fundo Decorativo (Padrão de Xadrez Sutil)
            screen.fill((20, 20, 25)) # Fundo quase preto
            
            # Desenha quadrados grandes sutis no fundo
            bg_tile_size = 120
            for y in range(0, 640, bg_tile_size):
                for x in range(0, 840, bg_tile_size):
                    if (x // bg_tile_size + y // bg_tile_size) % 2 == 0:
                        pygame.draw.rect(screen, (30, 30, 35), (x, y, bg_tile_size, bg_tile_size))
            
            # 2. Efeito de Vinheta (Escurece as bordas)
            # Opcional, mas dá um toque de cinema
            # (Se ficar pesado, pode remover)
            
            # 3. Lado Esquerdo: Identidade do Jogo
            # Desenha uma peça decorativa grande (Rei)
            img_decor = display_board.images.get((chess.KING, chess.WHITE))
            if img_decor:
                # Aumenta a imagem para enfeite
                img_big = pygame.transform.smoothscale(img_decor, (200, 200))
                # Desenha com transparência (alpha)
                img_big.set_alpha(50) 
                screen.blit(img_big, (100, 250))

            # Título Principal
            fonte_logo = pygame.font.SysFont("segoe ui", 70, bold=True)
            fonte_sub = pygame.font.SysFont("segoe ui", 24)
            
            # Sombra do texto
            txt_sombra = fonte_logo.render("My Chess", True, (0, 0, 0))
            screen.blit(txt_sombra, (83, 103))
            
            txt_logo = fonte_logo.render("My Chess", True, (220, 220, 220))
            screen.blit(txt_logo, (80, 100))
            
            txt_desc = fonte_sub.render("Desktop Edition", True, (100, 200, 100)) # Verde suave
            screen.blit(txt_desc, (85, 185))

            # 4. Lado Direito: Botões Modernos
            # Lista de botões com suas ações/textos
            # (Note que a lógica de clique continua no loop de eventos, aqui é só visual)
            # Precisamos garantir que as posições visuais batam com as do evento de clique.
            
            start_y = 100
            spacing = 65
            
            botoes_info = [
                (btn_novo, "Novo Jogo", (60, 120, 180)),   # Azul
                (btn_replay, "Replay / PGN", (100, 60, 140)), # Roxo
                (btn_puzzle, "Treino Tático", (180, 100, 60)),# Laranja
                (btn_tema, "Temas", (80, 80, 80)),         # Cinza
                (btn_pont, "Pontuações", (80, 80, 80)),    # Cinza
                (btn_opcoes, "Opções", (60, 60, 60)),       # Escuro
                (btn_tutorial, "Aprender", (60, 140, 60)) # Verde
            ]
            
            for i, (rect, texto, cor_base) in enumerate(botoes_info):
                # Atualiza a posição do Rect para o novo layout (Alinha à direita)
                rect.x = btn_x
                rect.y = start_y + (i * spacing)
                rect.width = btn_w
                rect.height = btn_h
                
                # Efeito Hover
                is_hover = rect.collidepoint(mouse_pos)
                
                if is_hover:
                    # Clareia a cor
                    cor_final = (min(255, cor_base[0]+30), min(255, cor_base[1]+30), min(255, cor_base[2]+30))
                    # Deslocamento visual (botão "sobe" 2 pixels)
                    draw_rect = pygame.Rect(rect.x, rect.y - 2, rect.width, rect.height)
                    # Sombra
                    pygame.draw.rect(screen, (0,0,0), (rect.x+2, rect.y+5, rect.width, rect.height), border_radius=12)
                else:
                    cor_final = cor_base
                    draw_rect = rect
                
                # Desenha Botão
                pygame.draw.rect(screen, cor_final, draw_rect, border_radius=12)
                pygame.draw.rect(screen, (255, 255, 255), draw_rect, 1, border_radius=12) # Borda fina branca
                
                # Texto do Botão
                txt_surf = fonte_btn.render(texto, True, (255, 255, 255))
                screen.blit(txt_surf, (draw_rect.centerx - txt_surf.get_width()//2, draw_rect.centery - txt_surf.get_height()//2))

            # 5. Botão de Som (Discreto no canto)
            # btn_som (já definido no loop de eventos)
            btn_som.x = 780
            btn_som.y = 20
            icon_color = (100, 255, 100) if sound_manager.enabled else (255, 100, 100)
            pygame.draw.circle(screen, (40, 40, 40), btn_som.center, 20) # Fundo circular
            pygame.draw.circle(screen, icon_color, btn_som.center, 20, 2) # Borda
            
            txt_som = fonte_small.render("S" if sound_manager.enabled else "X", True, icon_color)
            screen.blit(txt_som, (btn_som.centerx - txt_som.get_width()//2, btn_som.centery - txt_som.get_height()//2))

            # 6. Rodapé (Stats)
            s = score_manager.load_stats()
            rate = score_manager.get_win_rate()
            msg = f"Partidas: {s['games_played']}  |  Vitórias: {s['wins']}  |  Win Rate: {rate:.1f}%"
            
            # Barra de status inferior
            pygame.draw.rect(screen, (20, 20, 20), (0, 610, 840, 30))
            pygame.draw.line(screen, (50, 50, 50), (0, 610), (840, 610))
            
            txt_stats = fonte_small.render(msg, True, (100, 100, 100))
            screen.blit(txt_stats, (10, 615))
            
            # Versão
            txt_ver = fonte_small.render("v1.0.0 | Dev: Clayton Almeida", True, (60, 60, 60))
            screen.blit(txt_ver, (550, 615))

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

        elif estado_atual == ESTADO_TUTORIAL:
            display_board.draw(engine.board)
            
            lesson = tutorial_manager.get_current_lesson()
            
            # Desenha seta de instrução
            arrow_move = tutorial_manager.get_arrow_move()
            if arrow_move and not tutorial_concluido:
                display_board.draw_arrow(arrow_move, color=(0, 200, 255), width=8)

            # Painel Lateral
            painel_rect = pygame.Rect(660, 0, 180, 640)
            pygame.draw.rect(screen, (40, 40, 45), painel_rect) # Fundo escuro suave
            
            if lesson:
                # Título
                lbl_title = fonte_btn.render(lesson['title'], True, (255, 215, 0))
                # Centraliza o título
                screen.blit(lbl_title, (660 + (180 - lbl_title.get_width())//2, 30))
                
                # Texto Explicativo com Quebra de Linha
                fonte_tutorial = pygame.font.SysFont("arial", 18) # Fonte levemente menor para leitura
                texto_completo = " ".join(lesson['text']) # Junta as linhas do JSON num texto só
                
                # Define a área onde o texto pode aparecer
                area_texto = pygame.Rect(670, 80, 160, 400) # x=670 (margem), w=160 (largura útil)
                
                desenhar_texto_quebrado(screen, texto_completo, (220, 220, 220), area_texto, fonte_tutorial)
                
                # Status
                if tutorial_concluido:
                    pygame.draw.rect(screen, (50, 150, 50), (670, 450, 160, 40), border_radius=8)
                    lbl_ok = fonte_small.render("Muito Bem!", True, WHITE)
                    screen.blit(lbl_ok, (670 + (160 - lbl_ok.get_width())//2, 460))
                    
                    lbl_next = pygame.font.SysFont("arial", 14).render("Clique > para avançar", True, (150, 255, 150))
                    screen.blit(lbl_next, (670 + (160 - lbl_next.get_width())//2, 500))

            # Botões de Navegação
            btn_prev = pygame.Rect(670, 550, 40, 40)
            btn_next = pygame.Rect(720, 550, 40, 40)
            btn_menu = pygame.Rect(770, 550, 40, 40)
            
            # Cores dos botões
            pygame.draw.rect(screen, (80, 80, 100), btn_prev, border_radius=8)
            pygame.draw.rect(screen, (80, 120, 80), btn_next, border_radius=8) # Verde para o Próximo
            pygame.draw.rect(screen, (120, 60, 60), btn_menu, border_radius=8) # Vermelho para Sair
            
            # Ícones
            screen.blit(fonte_btn.render("<", True, WHITE), (btn_prev.centerx-8, btn_prev.centery-12))
            screen.blit(fonte_btn.render(">", True, WHITE), (btn_next.centerx-8, btn_next.centery-12))
            screen.blit(fonte_small.render("X", True, WHITE), (btn_menu.centerx-6, btn_menu.centery-10))
            
        elif estado_atual == ESTADO_SIMULACAO:
            display_board.draw(engine.board)
            # Desenha seta do movimento atual do replay
            if sim_index > 0 and sim_index <= len(sim_moves):
                move = sim_moves[sim_index-1]
                display_board.draw_arrow(move, color=(255,140,0,180), width=12)
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
                ("<<", 670, 220), ("<", 700, 220),
                ("||" if sim_auto else ">", 730, 220),
                (">", 770, 220), (">>", 800, 220)
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
            screen.fill((30, 30, 40))
            lbl = fonte_titulo.render("Escolha a Skin", True, (255,255,255))
            screen.blit(lbl, (840//2 - lbl.get_width()//2, 50))
            
            # Pega a lista de skins disponíveis (ID, Nome)
            skins_disponiveis = skin_manager.get_skin_names()
            
            # Paginação simples (se tiver muitas skins, mostra as primeiras 5)
            y_start = 120
            for i, (skin_id, skin_name) in enumerate(skins_disponiveis):
                if i > 5: break # Limite para não estourar tela por enquanto
                
                rect = pygame.Rect(220, y_start + i*70, 400, 50)
                
                # Destaca a selecionada
                cor = (60, 150, 100) if current_skin_id == skin_id else (80, 80, 80)
                
                # Desenha botão
                pygame.draw.rect(screen, cor, rect, border_radius=10)
                
                # Texto do nome
                txt = fonte_btn.render(skin_name, True, (255,255,255))
                screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
                
                # Lógica de Clique (aqui dentro ou no loop de eventos separado)
                # Para simplificar a resposta, vou colocar a detecção aqui se você estiver usando 
                # a estrutura "desenho separado". Se for a estrutura "eventos separados", mova isso:
            
            # Botão "Abrir Pasta de Skins" (Para ajudar o usuário)
            btn_folder = pygame.Rect(220, 550, 190, 40)
            pygame.draw.rect(screen, (100, 100, 150), btn_folder, border_radius=8)
            screen.blit(fonte_small.render("Abrir Pasta", True, WHITE), (btn_folder.x+50, btn_folder.y+10))

            btn_voltar = pygame.Rect(430, 550, 190, 40)
            pygame.draw.rect(screen, (150, 50, 50), btn_voltar, border_radius=8)
            screen.blit(fonte_small.render("Voltar", True, WHITE), (btn_voltar.x+70, btn_voltar.y+10))
            
            btn_criar = pygame.Rect(630, 550, 150, 40)
            pygame.draw.rect(screen, (50, 150, 50), btn_criar, border_radius=8)
            screen.blit(fonte_small.render("Criar Novo", True, WHITE), (btn_criar.x+40, btn_criar.y+10))

        elif estado_atual == ESTADO_EDITOR:
            screen.fill((30, 30, 35))
            lbl = fonte_titulo.render("Criador de Temas", True, WHITE)
            screen.blit(lbl, (280, 30))
            
            # Recupera cores atuais dos sliders para preview
            cor_clara = (int(sliders_editor[0].pct*255), int(sliders_editor[1].pct*255), int(sliders_editor[2].pct*255))
            cor_escura = (int(sliders_editor[3].pct*255), int(sliders_editor[4].pct*255), int(sliders_editor[5].pct*255))
            
            # Preview (Desenha um mini tabuleiro 2x2)
            prev_rect = pygame.Rect(550, 150, 200, 200)
            pygame.draw.rect(screen, (255, 255, 255), prev_rect, 4) # Borda
            pygame.draw.rect(screen, cor_clara, (550, 150, 100, 100))
            pygame.draw.rect(screen, cor_escura, (650, 150, 100, 100))
            pygame.draw.rect(screen, cor_escura, (550, 250, 100, 100))
            pygame.draw.rect(screen, cor_clara, (650, 250, 100, 100))
            
            # Desenha Peças de exemplo no preview (opcional)
            ex_pawn = display_board.images.get((chess.PAWN, chess.WHITE))
            if ex_pawn: screen.blit(ex_pawn, (560, 160))
            
            # Labels das seções
            screen.blit(fonte_btn.render("Cor Casas Claras", True, cor_clara), (250, 110))
            screen.blit(fonte_btn.render("Cor Casas Escuras", True, cor_escura), (250, 280))
            
            # Desenha Sliders
            for sl in sliders_editor:
                sl.draw(screen, fonte_small)
                
            # Input Nome
            screen.blit(fonte_small.render("Nome do Tema:", True, (200, 200, 200)), (250, 450))
            editor_nome_input.draw(screen)
            
            # Botões
            btn_salvar = pygame.Rect(300, 550, 240, 50)
            pygame.draw.rect(screen, (50, 200, 100), btn_salvar, border_radius=10)
            ls = fonte_btn.render("Salvar Tema", True, WHITE)
            screen.blit(ls, (btn_salvar.centerx - ls.get_width()//2, btn_salvar.centery - ls.get_height()//2))
            
            btn_cancelar = pygame.Rect(50, 550, 150, 50)
            pygame.draw.rect(screen, (200, 50, 50), btn_cancelar, border_radius=10)
            lc = fonte_btn.render("Cancelar", True, WHITE)
            screen.blit(lc, (btn_cancelar.centerx - lc.get_width()//2, btn_cancelar.centery - lc.get_height()//2))

        elif estado_atual == ESTADO_CONFIG:
            screen.fill((35, 35, 40))
            lbl = fonte_titulo.render("Opções", True, WHITE)
            screen.blit(lbl, (840//2 - lbl.get_width()//2, 50))
            
            # Slider Volume
            slider_volume.draw(screen, fonte_small)
            
            # Checkbox Fullscreen
            is_full = config_manager.get("fullscreen")
            chk_rect = pygame.Rect(270, 280, 30, 30)
            pygame.draw.rect(screen, (80, 80, 80), chk_rect, border_radius=5)
            if is_full:
                pygame.draw.rect(screen, (100, 200, 100), chk_rect.inflate(-6, -6), border_radius=3)
            
            lbl_full = fonte_btn.render("Tela Cheia", True, WHITE)
            screen.blit(lbl_full, (320, 280))
            
            # Checkbox AUTO-SAVE (NOVO)
            is_auto = config_manager.get("auto_save")
            chk_save_rect = pygame.Rect(270, 330, 30, 30)
            pygame.draw.rect(screen, (80, 80, 80), chk_save_rect, border_radius=5)
            if is_auto:
                pygame.draw.rect(screen, (100, 200, 100), chk_save_rect.inflate(-6, -6), border_radius=3)
            
            lbl_save = fonte_btn.render("Gravar PGN Auto", True, WHITE)
            screen.blit(lbl_save, (320, 330))
            
            # --- BOTÃO RESETAR STATS (NOVO) ---
            btn_reset_rect = pygame.Rect(270, 400, 300, 45)
            
            # Cor vermelha escura para indicar cuidado, clara se passar o mouse
            mouse_pos = pygame.mouse.get_pos()
            cor_btn = (200, 60, 60) if btn_reset_rect.collidepoint(mouse_pos) else (150, 40, 40)
            
            pygame.draw.rect(screen, cor_btn, btn_reset_rect, border_radius=8)
            pygame.draw.rect(screen, (255, 150, 150), btn_reset_rect, 2, border_radius=8) # Borda
            
            lbl_reset = fonte_btn.render("Resetar Estatísticas", True, (255, 255, 255))
            screen.blit(lbl_reset, (btn_reset_rect.centerx - lbl_reset.get_width()//2, btn_reset_rect.centery - lbl_reset.get_height()//2))

            # BOTÃO CRÉDITOS (NOVO)
            btn_creditos_rect = pygame.Rect(600, 550, 150, 40)
            pygame.draw.rect(screen, (60, 100, 160), btn_creditos_rect, border_radius=8) # Azul
            lbl_cred = fonte_btn.render("Créditos", True, WHITE)
            # Centraliza texto (ajuste fino se necessário)
            screen.blit(lbl_cred, (btn_creditos_rect.centerx - lbl_cred.get_width()//2, btn_creditos_rect.centery - lbl_cred.get_height()//2))

            # Botão Voltar
            btn_voltar = pygame.Rect(320, 550, 200, 40)
            pygame.draw.rect(screen, (150, 50, 50), btn_voltar, border_radius=8)
            l = fonte_btn.render("Voltar", True, WHITE)
            screen.blit(l, (btn_voltar.centerx - l.get_width()//2, btn_voltar.y+5))

        elif estado_atual == ESTADO_CREDITOS:
            screen.fill((25, 25, 30)) # Fundo escuro
            
            # Título
            lbl = fonte_titulo.render("Sobre o Jogo", True, (255, 255, 255))
            screen.blit(lbl, (840//2 - lbl.get_width()//2, 50))
            
            # Informações do Desenvolvedor
            y_start = 120
            linhas = [
                ("My Chess - Desktop Edition", (100, 200, 255)),
                ("Versão 1.0.0", (150, 150, 150)),
                ("", (0,0,0)), # Espaço
                ("Desenvolvido por:", (200, 200, 200)),
                ("Clayton Almeida", (255, 215, 0)), # Dourado (Troque pelo seu nome)
                ("", (0,0,0)),
                ("Bibliotecas Utilizadas:", (200, 200, 200)),
                ("Python 3 + Pygame-ce", (180, 180, 180)),
                ("python-chess (Lógica)", (180, 180, 180)),
                ("", (0,0,0)),
                ("Obrigado por jogar!", (100, 255, 100))
            ]
            
            fonte_creditos = pygame.font.SysFont("arial", 22)
            fonte_destaque = pygame.font.SysFont("arial", 28, bold=True)
            
            for texto, cor in linhas:
                if texto == "Clayton Almeida": # Destaque para o nome
                    surf = fonte_destaque.render(texto, True, cor)
                else:
                    surf = fonte_creditos.render(texto, True, cor)
                
                screen.blit(surf, (840//2 - surf.get_width()//2, y_start))
                y_start += 35

            # Botão Voltar
            btn_voltar = pygame.Rect(320, 550, 200, 40)
            pygame.draw.rect(screen, (150, 50, 50), btn_voltar, border_radius=8)
            l = fonte_btn.render("Voltar", True, WHITE)
            screen.blit(l, (btn_voltar.centerx - l.get_width()//2, btn_voltar.y+5))

        elif estado_atual == ESTADO_GAME_OVER:
            # 1. Desenha o jogo no fundo (congelado) para contexto
            display_board.draw(engine.board)
            
            # 2. Camada escura semi-transparente (Overlay)
            overlay = pygame.Surface((840, 640))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            # 3. Caixa de Mensagem
            box_rect = pygame.Rect(220, 150, 400, 350)
            pygame.draw.rect(screen, (40, 40, 45), box_rect, border_radius=20)
            pygame.draw.rect(screen, cor_fim_jogo, box_rect, 4, border_radius=20) # Borda colorida (Verde/Vermelha)
            
            # Texto Principal (VITÓRIA/DERROTA)
            txt_big = pygame.font.SysFont("arial", 60, bold=True).render(texto_fim_jogo, True, cor_fim_jogo)
            screen.blit(txt_big, (box_rect.centerx - txt_big.get_width()//2, box_rect.y + 50))
            
            # Subtexto (Motivo)
            txt_sub = fonte_btn.render(subtexto_fim_jogo, True, (200, 200, 200))
            screen.blit(txt_sub, (box_rect.centerx - txt_sub.get_width()//2, box_rect.y + 130))
            
            # Pontuação Final
            if pontuacao_final > 0:
                txt_pts = fonte_btn.render(f"Pontuação: {pontuacao_final}", True, (255, 215, 0)) # Dourado
                screen.blit(txt_pts, (box_rect.centerx - txt_pts.get_width()//2, box_rect.y + 180))
            
            # Botão Continuar
            btn_cont = pygame.Rect(320, 400, 200, 50)
            pygame.draw.rect(screen, cor_fim_jogo, btn_cont, border_radius=10)
            lbl_cont = fonte_btn.render("Continuar", True, (255, 255, 255))
            screen.blit(lbl_cont, (btn_cont.centerx - lbl_cont.get_width()//2, btn_cont.centery - lbl_cont.get_height()//2))

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
                ("F11 - Tela Cheia", (180, 180, 180)),
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
                    display_board.draw_arrow(ultima_dica_move, color=(0,180,255,160), width=10)
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
            
            # Destaque da seleção
            if selecionado is not None:
                c = chess.square_file(selecionado)
                r = 7 - chess.square_rank(selecionado)
                if display_board.is_flipped: c, r = 7-c, 7-r
                s = pygame.Surface((80, 80)); s.set_alpha(100); s.fill((255, 255, 0))
                screen.blit(s, (c*80, r*80))
            
            # Painel Lateral do Puzzle
            # Fundo escuro para destacar o texto
            painel_rect = pygame.Rect(660, 0, 180, 640)
            pygame.draw.rect(screen, (50, 45, 60), painel_rect) 
            
            # Título
            lbl = fonte_btn.render("Puzzle", True, (255, 255, 255))
            # Centraliza no painel (660 + 90 = 750 é o centro)
            screen.blit(lbl, (750 - lbl.get_width()//2, 30))
            
            # --- DESCRIÇÃO (Usando Quebra de Linha Automática) ---
            # Define a área útil para o texto (com margem de 10px)
            area_desc = pygame.Rect(670, 80, 160, 200)
            # Usa uma fonte levemente menor para caber mais texto
            fonte_desc = pygame.font.SysFont("arial", 18)
            
            # Desenha o texto quebrado
            desenhar_texto_quebrado(screen, puzzle_info, (200, 200, 200), area_desc, fonte_desc)

            # --- FEEDBACK (Centralizado e Colorido) ---
            cor_feed = (100, 255, 100) if "Correto" in feedback_puzzle or "RESOLVIDO" in feedback_puzzle else (255, 80, 80)
            if "Encontre" in feedback_puzzle: cor_feed = (255, 255, 255)
            
            # Vamos usar a quebra de linha aqui também para garantir que não corte
            area_feed = pygame.Rect(670, 300, 160, 100)
            fonte_feed = pygame.font.SysFont("arial", 20, bold=True)
            
            desenhar_texto_quebrado(screen, feedback_puzzle, cor_feed, area_feed, fonte_feed)

            # Botão Próximo Puzzle (Só aparece se resolver)
            if "RESOLVIDO" in feedback_puzzle:
                btn_prox = pygame.Rect(670, 450, 160, 50)
                pygame.draw.rect(screen, (100, 180, 100), btn_prox, border_radius=8)
                pygame.draw.rect(screen, (255, 255, 255), btn_prox, 2, border_radius=8) # Borda
                
                l = fonte_btn.render("Próximo", True, (255,255,255))
                screen.blit(l, (btn_prox.centerx - l.get_width()//2, btn_prox.centery - l.get_height()//2))
                
                # Hack rápido de clique (se preferir manter a lógica separada, ignore esta parte e use o evento lá em cima)
                if pygame.mouse.get_pressed()[0]:
                    mx, my = pygame.mouse.get_pos()
                    if btn_prox.collidepoint(mx, my):
                        p = puzzle_manager.get_random_puzzle()
                        if p:
                            engine.board.set_fen(p['fen'])
                            display_board.set_flip(not engine.board.turn)
                            puzzle_info = f"{p['description']} ({p['rating']})"
                            feedback_puzzle = "Encontre o melhor lance!"
                            puzzle_hint_move = None
                            pygame.time.wait(200)
            
            # Botão Voltar/Sair (Rodapé)
            btn_sair = pygame.Rect(670, 550, 160, 40)
            pygame.draw.rect(screen, (80, 60, 80), btn_sair, border_radius=8)
            lbl_sair = fonte_small.render("Voltar (ESC)", True, (200, 200, 200))
            screen.blit(lbl_sair, (btn_sair.centerx - lbl_sair.get_width()//2, btn_sair.centery - lbl_sair.get_height()//2))

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