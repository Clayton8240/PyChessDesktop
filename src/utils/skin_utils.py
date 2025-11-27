import os
from src.config import get_user_data_dir

def get_all_skin_folders(local_folder="skins"):
    """
    Retorna uma lista de caminhos de todas as pastas de skins disponíveis,
    tanto na pasta local quanto na pasta de dados do usuário (AppData).
    """
    skin_folders = []
    # Pasta local
    if os.path.exists(local_folder):
        for item in os.listdir(local_folder):
            path = os.path.join(local_folder, item)
            if os.path.isdir(path):
                skin_folders.append(path)
    # Pasta AppData
    user_skins = os.path.join(get_user_data_dir(), "skins")
    if os.path.exists(user_skins):
        for item in os.listdir(user_skins):
            path = os.path.join(user_skins, item)
            if os.path.isdir(path):
                skin_folders.append(path)
    return skin_folders
