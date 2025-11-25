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

    def get_random_puzzle(self, min_rating=0, max_rating=9999):
        if not self.puzzles: return None
        
        # 1. CRIA UMA LISTA FILTRADA NA HORA
        # Seleciona apenas os puzzles que estão dentro da faixa de rating pedida
        candidatos = [
            p for p in self.puzzles 
            if min_rating <= int(p.get('rating', 0)) <= max_rating
        ]
        
        if not candidatos:
            print(f"Nenhum puzzle encontrado na faixa {min_rating}-{max_rating}")
            return None
        
        # 2. Tenta achar um puzzle válido dentro dos candidatos filtrados
        for _ in range(20): # Aumentei as tentativas para garantir
            candidate = random.choice(candidatos)
            
            # Validação Rápida (igual ao anterior)
            board = chess.Board(candidate['fen'])
            try:
                move_uci = candidate['moves'][0]
                move = chess.Move.from_uci(move_uci)
                
                if move in board.legal_moves:
                    self.current_puzzle = candidate
                    self.puzzle_moves = candidate['moves']
                    self.move_index = 0
                    return self.current_puzzle
            except:
                pass
        
        return None

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