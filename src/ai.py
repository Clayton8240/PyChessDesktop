# --- Transposition Table (Hash de posições) ---
transpo_table = {}
import chess
import random

# Valores Materiais
piece_values = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# --- TABELAS POSICIONAIS (PST) ---
# Valores positivos incentivam a peça a ir para aquela casa.
# A lógica é espelhada para as pretas automaticamente.

# Peões: Incentiva avançar, mas pune peões centrais muito adiantados sem apoio
pawns_table = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]

# Cavalos: Amam o centro, odeiam as bordas
knights_table = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

# Bispos: Gostam de diagonais longas e odeiam cantos presos
bishops_table = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

# Torres: Gostam da 7ª fila e colunas centrais
rooks_table = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
]

# Rainha: Quase igual ao Bispo, mas com cuidado para não sair cedo demais
queens_table = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

# Rei (Meio Jogo): Esconda-se atrás dos peões! (Roque)
king_mid_table = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]

# Rei (Final de Jogo): Centralize o Rei!
king_end_table = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

# --- Função de Ordenação MVV-LVA ---
def score_move(move, board):
    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        victim_val = piece_values.get(victim.piece_type, 0) if victim else 0
        aggressor = board.piece_at(move.from_square)
        aggressor_val = piece_values.get(aggressor.piece_type, 0) if aggressor else 0
        return 10000 + victim_val - aggressor_val
    return 0

# --- Busca de Quiescência ---
def quiescence(board, alpha, beta):
    stand_pat = evaluate_board(board)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat
    capturas = [m for m in board.legal_moves if board.is_capture(m)]
    capturas.sort(key=lambda m: score_move(m, board), reverse=True)
    for move in capturas:
        board.push(move)
        score = -quiescence(board, -beta, -alpha)
        board.pop()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha

def evaluate_board(board):
    if board.is_checkmate():
        if board.turn: return -99999
        else: return 99999
    
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    # Detecta final de jogo: sem rainhas ou material muito reduzido
    num_queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
    num_minors = sum(len(board.pieces(pt, chess.WHITE)) + len(board.pieces(pt, chess.BLACK)) for pt in [chess.BISHOP, chess.KNIGHT])
    is_endgame = num_queens == 0 or (num_queens == 2 and (len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.ROOK, chess.BLACK)) + num_minors) <= 1)

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece: continue

        # Valor Material Base
        value = piece_values.get(piece.piece_type, 0)

        # Valor Posicional (PST)
        pst_value = 0
        
        # Espelha o índice se for peça preta (para usar a mesma tabela)
        table_idx = square if piece.color == chess.WHITE else chess.square_mirror(square)

        if piece.piece_type == chess.PAWN:
            pst_value = pawns_table[table_idx]
        elif piece.piece_type == chess.KNIGHT:
            pst_value = knights_table[table_idx]
        elif piece.piece_type == chess.BISHOP:
            pst_value = bishops_table[table_idx]
        elif piece.piece_type == chess.ROOK:
            pst_value = rooks_table[table_idx]
        elif piece.piece_type == chess.QUEEN:
            pst_value = queens_table[table_idx]
        elif piece.piece_type == chess.KING:
            # Usa tabela de finais para o Rei se for endgame
            if is_endgame:
                pst_value = king_end_table[table_idx]
            else:
                pst_value = king_mid_table[table_idx]

        if piece.color == chess.WHITE:
            score += (value + pst_value)
        else:
            score -= (value + pst_value)
            
    return score

# --- MINIMAX OTIMIZADO ---
def minimax(board, depth, alpha, beta, maximizing_player):
    # Transposition Table Lookup
    key = (board.transposition_key(), depth, maximizing_player)
    if key in transpo_table:
        return transpo_table[key]

    if depth == 0 or board.is_game_over():
        val = quiescence(board, alpha, beta)
        transpo_table[key] = val
        return val

    legal_moves = list(board.legal_moves)
    # Ordenação MVV-LVA
    legal_moves.sort(key=lambda m: score_move(m, board), reverse=True)

    if maximizing_player:
        max_eval = -float('inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha: break
        transpo_table[key] = max_eval
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha: break
        transpo_table[key] = min_eval
        return min_eval

def get_best_move(board, difficulty):
    legal_moves = list(board.legal_moves)
    if not legal_moves: return None

    # Nível 1: Fácil (Aleatório)
    if difficulty == 1:
        return random.choice(legal_moves)

    # Profundidade adaptativa por dificuldade
    # 2 = fácil, 3 = médio, 4 = difícil, 5+ = profissional
    if difficulty == 2:
        depth = 2
    elif difficulty == 3:
        depth = 3
    elif difficulty == 4:
        depth = 5
    else:
        depth = 6
    
    maximizing = (board.turn == chess.WHITE)
    best_value = -float('inf') if maximizing else float('inf')
    best_move = None
    
    # Embaralha para variar jogos iguais, mas ordena capturas primeiro
    random.shuffle(legal_moves)
    legal_moves.sort(key=lambda move: 1 if board.is_capture(move) else 0, reverse=True)

    for move in legal_moves:
        board.push(move)
        board_value = minimax(board, depth - 1, -float('inf'), float('inf'), not maximizing)
        board.pop()
        
        if maximizing:
            if board_value > best_value:
                best_value = board_value
                best_move = move
        else:
            if board_value < best_value:
                best_value = board_value
                best_move = move
                
    return best_move if best_move else random.choice(legal_moves)
import chess
import random

# Valores das peças para a IA calcular trocas
piece_values = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# Tabela de Posição (Simplificada): Incentiva controle do centro
# Peças ganham bônus se estiverem nas casas centrais (valores maiores no meio da matriz)
pawn_table = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]

def evaluate_board(board):
    """Calcula a pontuação estática do tabuleiro do ponto de vista das BRANCAS."""
    if board.is_checkmate():
        if board.turn: return -99999 # Brancas levaram mate (turn=True)
        else: return 99999 # Pretas levaram mate
    score = 0
    # Material
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece: continue
        value = piece_values.get(piece.piece_type, 0)
        # Adiciona bônus posicional simples para peões (incentiva avançar)
        if piece.piece_type == chess.PAWN:
            # Espelha a tabela para as pretas
            idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
            value += pawn_table[idx]
        if piece.color == chess.WHITE:
            score += value
        else:
            score -= value
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    """Algoritmo recursivo para prever jogadas."""
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)
    if maximizing_player: # Vez das Brancas (querem pontuação positiva)
        max_eval = -float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha: break # Poda
        return max_eval
    else: # Vez das Pretas (querem pontuação negativa)
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha: break # Poda
        return min_eval

def get_best_move(board, difficulty):
    """
    difficulty 1: Aleatório (Fácil)
    difficulty 2: Profundidade 2 (Médio)
    difficulty 3: Profundidade 3 (Difícil)
    """
    legal_moves = list(board.legal_moves)
    if not legal_moves: return None
    # Nível Fácil: Joga qualquer coisa
    if difficulty == 1:
        return random.choice(legal_moves)
    # Níveis Médio/Difícil: Usa Minimax
    best_move = None
    depth = 2 if difficulty == 2 else 3
    # Se for vez das Brancas, queremos maximizar. Se Pretas, minimizar.
    maximizing = (board.turn == chess.WHITE)
    best_value = -float('inf') if maximizing else float('inf')
    # Embaralha movimentos para não ser previsível em posições iguais
    random.shuffle(legal_moves)
    for move in legal_moves:
        board.push(move)
        # Chama o minimax recursivo
        board_value = minimax(board, depth - 1, -float('inf'), float('inf'), not maximizing)
        board.pop()
        if maximizing:
            if board_value > best_value:
                best_value = board_value
                best_move = move
        else:
            if board_value < best_value:
                best_value = board_value
                best_move = move
    return best_move if best_move else random.choice(legal_moves)

import random


def movimento_aleatorio(board):
    """Retorna um movimento aleatório legal para o jogador da vez (Branco ou Preto)."""
    moves = list(board.legal_moves)
    if moves:
        return random.choice(moves)
    return None
