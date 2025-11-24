
import random


def movimento_aleatorio(board):
    """Retorna um movimento aleatório legal para o jogador da vez (Branco ou Preto)."""
    moves = list(board.legal_moves)
    if moves:
        return random.choice(moves)
    return None
