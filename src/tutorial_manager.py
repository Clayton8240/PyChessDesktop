import json
import os
import chess

class TutorialManager:
    def __init__(self, filepath="data/tutorial.json"):
        self.filepath = filepath
        self.lessons = []
        self.current_lesson_index = 0
        self.load_lessons()

    def load_lessons(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.lessons = json.load(f)
        else:
            self.lessons = []

    def get_current_lesson(self):
        if not self.lessons: return None
        return self.lessons[self.current_lesson_index]

    def next_lesson(self):
        if self.current_lesson_index < len(self.lessons) - 1:
            self.current_lesson_index += 1
            return self.get_current_lesson()
        return None # Fim do tutorial

    def prev_lesson(self):
        if self.current_lesson_index > 0:
            self.current_lesson_index -= 1
            return self.get_current_lesson()
        return None

    def check_move(self, move):
        """Verifica se o jogador fez o movimento que a lição pede."""
        lesson = self.get_current_lesson()
        if not lesson: return False
        
        # Compara strings UCI (ex: 'e2e4')
        return move.uci() == lesson['expected_move']

    def get_arrow_move(self):
        """Retorna um objeto chess.Move para desenhar a seta de ajuda."""
        lesson = self.get_current_lesson()
        if not lesson or 'arrow' not in lesson: return None
        
        start = chess.parse_square(lesson['arrow'][0])
        end = chess.parse_square(lesson['arrow'][1])
        return chess.Move(start, end)
