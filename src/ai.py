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

def evaluate_board(board):
    if board.is_checkmate():
        if board.turn: return -99999
        else: return 99999
    
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    # Verifica se estamos no final do jogo (sem rainhas ou poucas peças)
    # No final, o Rei deve ir para o centro, não se esconder.
    is_endgame = len(board.pieces(chess.QUEEN, chess.WHITE)) == 0 and len(board.pieces(chess.QUEEN, chess.BLACK)) == 0

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
            # Se for final de jogo, não usamos a tabela de segurança, o rei vira peça de ataque
            if is_endgame:
                pst_value = 0 
            else:
                pst_value = king_mid_table[table_idx]

        if piece.color == chess.WHITE:
            score += (value + pst_value)
        else:
            score -= (value + pst_value)
            
    return score

# --- MINIMAX OTIMIZADO ---
def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    legal_moves = list(board.legal_moves)
    
    # OTIMIZAÇÃO DE ORDEM: Avalia capturas primeiro!
    # Isso faz o Alpha-Beta podar árvores ruins muito mais rápido.
    # Ordena movimentos que capturam peças para o início da lista
    legal_moves.sort(key=lambda move: 1 if board.is_capture(move) else 0, reverse=True)

    if maximizing_player:
        max_eval = -float('inf')
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha: break
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
        return min_eval

def get_best_move(board, difficulty):
    legal_moves = list(board.legal_moves)
    if not legal_moves: return None

    # Nível 1: Fácil (Aleatório)
    if difficulty == 1:
        return random.choice(legal_moves)
    
    # Nível 2: Médio (Depth 2 + PST)
    # Nível 3: Difícil (Depth 3 + PST)
    # Nível 4: Profissional (Depth 3 + PST + Move Ordering agressivo implícito no minimax)
    
    # Nota: Mantemos depth 3 para Profissional para não travar, 
    # mas a inteligência vem das tabelas (PST) novas que adicionamos acima.
    depth = 2
    if difficulty >= 3:
        depth = 3
    
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
