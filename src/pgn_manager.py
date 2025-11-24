import chess
import chess.pgn
import os
from datetime import datetime

class PGNManager:
    def __init__(self, data_dir="data/pgn"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def save_game(self, board, white_name="Jogador", black_name="Computador", result="*"):
        """Salva o histórico do tabuleiro atual em um arquivo PGN."""
        game = chess.pgn.Game()
        
        # Cabeçalhos obrigatórios
        game.headers["Event"] = "Partida Casual PyChess"
        game.headers["Site"] = "Local"
        game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        game.headers["Round"] = "1"
        game.headers["White"] = white_name
        game.headers["Black"] = black_name
        game.headers["Result"] = result

        # Reconstrói a árvore de movimentos a partir do move_stack do tabuleiro
        node = game
        for move in board.move_stack:
            node = node.add_variation(move)

        # Gera nome de arquivo único
        filename = f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pgn"
        filepath = os.path.join(self.data_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            print(game, file=f, end="\n\n")
        
        return filename

    def list_files(self):
        """Retorna lista de arquivos .pgn disponíveis."""
        if not os.path.exists(self.data_dir): return []
        return [f for f in os.listdir(self.data_dir) if f.endswith('.pgn')]

    def load_game_moves(self, filename):
        """Lê um PGN e retorna uma LISTA de objetos chess.Move para simulação."""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            game = chess.pgn.read_game(f)
        
        # Extrai todos os movimentos da partida principal
        moves = []
        for move in game.mainline_moves():
            moves.append(move)
            
        return moves, game.headers # Retorna movimentos e cabeçalhos (nomes, data)