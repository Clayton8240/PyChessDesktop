
import json
import os
from typing import List, Dict
from src.config import get_user_data_dir # <--- ADICIONE ISTO

class ScoreManager:
	def _get_stats_path(self):
		# Cria o caminho para stats.json na mesma pasta do scores.json
		return os.path.join(os.path.dirname(self.scores_path), 'stats.json')

	def load_stats(self):
		"""Carrega estatísticas globais: vitórias, derrotas, empates."""
		stats_path = self._get_stats_path()
		if not os.path.exists(stats_path):
			return {"wins": 0, "losses": 0, "draws": 0, "games_played": 0}
		try:
			with open(stats_path, 'r', encoding='utf-8') as f:
				return json.load(f)
		except Exception:
			return {"wins": 0, "losses": 0, "draws": 0, "games_played": 0}

	def update_stats(self, result):
		"""
		result: 'win', 'loss', ou 'draw'
		"""
		stats = self.load_stats()
		if result == 'win':
			stats['wins'] += 1
		elif result == 'loss':
			stats['losses'] += 1
		elif result == 'draw':
			stats['draws'] += 1
		stats['games_played'] += 1
		# Salva
		with open(self._get_stats_path(), 'w', encoding='utf-8') as f:
			json.dump(stats, f, indent=4)

	def get_win_rate(self):
		stats = self.load_stats()
		total = stats['games_played']
		if total == 0:
			return 0.0
		return (stats['wins'] / total) * 100

	def reset_stats(self):
		"""Zera as estatísticas globais."""
		stats = {"wins": 0, "losses": 0, "draws": 0, "games_played": 0}
		# Salva o arquivo zerado
		try:
			with open(self._get_stats_path(), 'w', encoding='utf-8') as f:
				json.dump(stats, f, indent=4)
		except Exception as e:
			print(f"Erro ao resetar stats: {e}")
			
	def __init__(self, scores_path=None):
		if scores_path is None:
			scores_path = os.path.join(get_user_data_dir(), 'scores.json')
		self.scores_path = scores_path
		# Garante que a pasta existe (caso seja a primeira vez rodando)
		os.makedirs(os.path.dirname(self.scores_path), exist_ok=True)

	def calcular_pontuacao(self, resultado_tipo: str, material_restante: int, tempo_gasto: int, dificuldade: int = 2) -> int:
		"""
		Calcula pontuação granular.
		resultado_tipo: 'win', 'loss', ou 'draw'
		"""
		# 1. Pontuação Base (Define o patamar)
		if resultado_tipo == 'win':
			base = 5000
		elif resultado_tipo == 'draw':
			base = 2500
		else: # loss
			base = 1000
			
		# 2. Bônus de Material (Valoriza proteger suas peças)
		# Ex: Terminar com Rainha (9) e 2 Peões (2) = 11 * 50 = 550 pts
		bonus_material = material_restante * 50
		
		# 3. Penalidade de Tempo (Suave)
		# Perde 5 pontos a cada 10 segundos jogados
		penalidade_tempo = int(tempo_gasto * 0.5)
		
		# 4. Multiplicador de Dificuldade
		# Fácil(1)=x1.0, Médio(2)=x1.5, Difícil(3)=x2.0, Pro(4)=x3.0
		multiplicadores = {1: 1.0, 2: 1.5, 3: 2.0, 4: 3.0}
		fator = multiplicadores.get(dificuldade, 1.0)
		
		# Cálculo Final
		pontos_brutos = base + bonus_material - penalidade_tempo
		
		# Aplica o multiplicador
		pontos_finais = int(pontos_brutos * fator)
		
		# Garante pontuação mínima para não frustrar (ex: nunca negativo)
		return max(pontos_finais, 100)

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
