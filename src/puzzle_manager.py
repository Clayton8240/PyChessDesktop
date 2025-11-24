import json
import os
import random
import chess

class PuzzleManager:
    def __init__(self, filepath="data/puzzles.json"):
        self.filepath = filepath
        self.puzzles = []
        self.current_puzzle = None
        self.puzzle_moves = [] # Lista de strings UCI ['e2e4', 'e7e5']
        self.move_index = 0
        self.load_puzzles()

    def load_puzzles(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.puzzles = json.load(f)
        else:
            print("Arquivo de puzzles não encontrado!")

    def get_random_puzzle(self):
        if not self.puzzles: return None
        self.current_puzzle = random.choice(self.puzzles)
        self.puzzle_moves = self.current_puzzle['moves']
        self.move_index = 0
        return self.current_puzzle

    def check_move(self, move):
        """
        Verifica se o movimento feito pelo jogador é o correto.
        move: objeto chess.Move
        Retorna: (Correto?, Acabou?)
        """
        if self.move_index >= len(self.puzzle_moves):
            return False, True # Já acabou

        expected_uci = self.puzzle_moves[self.move_index]
        
        if move.uci() == expected_uci:
            self.move_index += 1
            is_finished = (self.move_index >= len(self.puzzle_moves))
            return True, is_finished
        
        return False, False

    def get_next_opponent_move(self):
        """Retorna o próximo lance da sequência (resposta do oponente) como chess.Move"""
        if self.move_index < len(self.puzzle_moves):
            uci = self.puzzle_moves[self.move_index]
            self.move_index += 1
            return chess.Move.from_uci(uci)
        return None

    def get_solution_move(self):
        """Retorna o próximo movimento correto (chess.Move) para dar a dica."""
        if self.move_index < len(self.puzzle_moves):
            uci = self.puzzle_moves[self.move_index]
            return chess.Move.from_uci(uci)
        return None