
import json
import os
from src.config import get_user_data_dir  # <--- IMPORTANTE

class ConfigManager:
    def __init__(self, filepath=None):
        # Se nenhum caminho for passado, usa o AppData
        if filepath is None:
            self.filepath = os.path.join(get_user_data_dir(), "settings.json")
        else:
            self.filepath = filepath

        # Configurações Padrão
        self.defaults = {
            "volume_master": 0.5,  # 0.0 a 1.0
            "fullscreen": False,
            "last_skin": "default",
            "difficulty": 2,
            "show_hints": True,
            "auto_save": False
        }
        self.config = self.defaults.copy()
        self.load()

    def load(self):
        """Carrega as configurações do disco."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    saved = json.load(f)
                    # Atualiza apenas as chaves que existem (merge)
                    self.config.update(saved)
            except:
                print("Erro ao carregar settings.json, usando padrão.")

    def save(self):
        """Salva as configurações no disco."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get(self, key):
        return self.config.get(key, self.defaults.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save()
