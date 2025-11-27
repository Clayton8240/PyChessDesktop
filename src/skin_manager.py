import zipfile
import tempfile
import os
import json



from src.config import get_user_data_dir
from src.utils.skin_utils import get_all_skin_folders

class SkinManager:
    def __init__(self, base_folder="skins"):
        self.base_folder = base_folder
        # Garante que a pasta local existe
        os.makedirs(self.base_folder, exist_ok=True)
        # Garante que a pasta AppData/skins existe
        self.user_skins_folder = os.path.join(get_user_data_dir(), "skins")
        os.makedirs(self.user_skins_folder, exist_ok=True)
        self.skins = {} # Dicionário { 'nome_da_skin': dados_da_skin }
        self.reload_skins()

    def importar_skin_zip(self, zip_path):
        """
        Importa uma skin a partir de um arquivo ZIP.
        O ZIP deve conter uma pasta com um config.json válido e, opcionalmente, imagens de peças/tabuleiro.
        A skin será importada para a pasta AppData/skins.
        """
        if not zipfile.is_zipfile(zip_path):
            raise ValueError("Arquivo não é um ZIP válido.")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extrai para uma pasta temporária
            with tempfile.TemporaryDirectory() as tmpdirname:
                zip_ref.extractall(tmpdirname)
                # Procura por uma pasta com config.json
                for root, dirs, files in os.walk(tmpdirname):
                    if 'config.json' in files:
                        # Nome da skin = nome da pasta onde está o config.json
                        skin_folder = os.path.basename(root)
                        dest_folder = os.path.join(self.user_skins_folder, skin_folder)
                        if os.path.exists(dest_folder):
                            raise FileExistsError(f"Já existe uma skin chamada '{skin_folder}'.")
                        # Copia tudo para a pasta de skins do usuário
                        import shutil
                        shutil.copytree(root, dest_folder)
                        # Se houver subpasta 'pieces' ou imagens soltas, move para dentro da skin
                        for sub in ['pieces', 'tabuleiro', 'board']:
                            sub_path = os.path.join(root, sub)
                            if os.path.isdir(sub_path):
                                dest_sub = os.path.join(dest_folder, sub)
                                shutil.move(sub_path, dest_sub)
                        # Também move imagens soltas (png/svg) para a pasta da skin
                        for f in files:
                            if f.lower().endswith(('.png', '.svg', '.jpg', '.jpeg')):
                                shutil.move(os.path.join(root, f), os.path.join(dest_folder, f))
                        self.reload_skins()
                        return skin_folder
                raise FileNotFoundError("Nenhum config.json encontrado no ZIP.")

    def reload_skins(self):
        """Escaneia as pastas de skins locais e AppData em busca de subpastas válidas."""
        self.skins = {}
        # 1. Adiciona a skin padrão (Default) para garantir que o jogo nunca quebre
        self.skins['default'] = {
            'name': 'Padrão (Madeira)',
            'light': (240, 217, 181),
            'dark': (181, 136, 99),
            'path': 'assets/images/pieces' # Caminho interno original
        }

        # 2. Procura pastas novas em ambos os diretórios
        for skin_path in get_all_skin_folders(self.base_folder):
            item = os.path.basename(skin_path)
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
