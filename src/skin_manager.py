import os
import json

class SkinManager:
    def __init__(self, base_folder="skins"):
        self.base_folder = base_folder
        # Garante que a pasta existe
        os.makedirs(self.base_folder, exist_ok=True)
        self.skins = {} # Dicionário { 'nome_da_skin': dados_da_skin }
        self.reload_skins()

    def reload_skins(self):
        """Escaneia a pasta skins em busca de subpastas válidas."""
        self.skins = {}
        
        # 1. Adiciona a skin padrão (Default) para garantir que o jogo nunca quebre
        self.skins['default'] = {
            'name': 'Padrão (Madeira)',
            'light': (240, 217, 181),
            'dark': (181, 136, 99),
            'path': 'assets/images/pieces' # Caminho interno original
        }

        # 2. Procura pastas novas
        if not os.path.exists(self.base_folder): return

        for item in os.listdir(self.base_folder):
            skin_path = os.path.join(self.base_folder, item)
            
            # Verifica se é uma pasta e se tem o arquivo de configuração
            if os.path.isdir(skin_path):
                config_file = os.path.join(skin_path, 'config.json')
                if os.path.exists(config_file):
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                            # Validação básica
                            self.skins[item] = {
                                'name': data.get('name', item),
                                'light': tuple(data.get('light_color', (255, 255, 255))),
                                'dark': tuple(data.get('dark_color', (0, 0, 0))),
                                'path': skin_path # Onde estão as imagens
                            }
                    except Exception as e:
                        print(f"Erro ao carregar skin {item}: {e}")

    def get_skin_data(self, skin_id):
        return self.skins.get(skin_id, self.skins['default'])

    def get_skin_names(self):
        # Retorna lista de (id, nome_bonito)
        return [(k, v['name']) for k, v in self.skins.items()]

    def save_new_skin(self, name, light_rgb, dark_rgb):
        """Cria uma nova pasta de skin com as cores escolhidas."""
        # Remove caracteres perigosos do nome da pasta
        folder_name = "".join([c for c in name if c.isalnum() or c in (' ', '_')]).strip()
        if not folder_name: folder_name = "CustomSkin"
        
        full_path = os.path.join(self.base_folder, folder_name)
        os.makedirs(full_path, exist_ok=True)
        
        data = {
            "name": name,
            "light_color": light_rgb,
            "dark_color": dark_rgb
        }
        
        # Salva o config.json
        with open(os.path.join(full_path, "config.json"), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        self.reload_skins() # Atualiza a lista para aparecer no menu
        return folder_name # Retorna o ID da nova skin
