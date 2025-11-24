
import json
import os
from typing import List, Dict

class ScoreManager:
	def __init__(self, scores_path=None):
		if scores_path is None:
			base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
			scores_path = os.path.join(base_dir, 'data', 'scores.json')
		self.scores_path = scores_path

	def calcular_pontuacao(self, vencedor: bool, material_restante: int, tempo_gasto: int) -> int:
		"""
		Calcula a pontuação final.
		vencedor: True se ganhou, False se perdeu (derrota = 0 pontos)
		material_restante: soma dos valores das peças vivas (Peão=1, Bispo=3, Torre=5, Rainha=9)
		tempo_gasto: tempo em segundos
		"""
		if not vencedor:
			return 0
		pontos = 1000 + (material_restante * 50) - (tempo_gasto * 2)
		return max(pontos, 0)

	def load_scores(self) -> List[Dict]:
		"""Carrega e retorna a lista de recordes ordenada por score decrescente."""
		if not os.path.exists(self.scores_path):
			return []
		with open(self.scores_path, 'r', encoding='utf-8') as f:
			try:
				scores = json.load(f)
			except Exception:
				scores = []
		scores.sort(key=lambda x: x['score'], reverse=True)
		return scores

	def save_score(self, player_name: str, score: int, time_str: str):
		"""Salva um novo recorde e mantém apenas o Top 10."""
		scores = self.load_scores()
		scores.append({
			'name': player_name,
			'score': score,
			'time': time_str
		})
		scores.sort(key=lambda x: x['score'], reverse=True)
		scores = scores[:10]
		with open(self.scores_path, 'w', encoding='utf-8') as f:
			json.dump(scores, f, ensure_ascii=False, indent=2)

	def check_is_highscore(self, score: int) -> bool:
		"""Verifica se a pontuação entra no Top 10 atual."""
		scores = self.load_scores()
		if len(scores) < 10:
			return True
		return any(score > s['score'] for s in scores)
