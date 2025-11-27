
# Configurações e constantes globais
import os
import sys

def get_user_data_dir():
	"""
	Retorna o caminho da pasta onde dados do usuário (saves, configs) devem ficar.
	Windows: %APPDATA%/My Chess
	Linux: ~/.local/share/My Chess
	"""
	app_name = "My Chess"
    
	if sys.platform == "win32":
		base_path = os.getenv('APPDATA')
	else:
		# Padrão Linux (XDG)
		base_path = os.path.expanduser("~/.local/share")
        
	full_path = os.path.join(base_path, app_name)
    
	# Garante que a pasta existe
	if not os.path.exists(full_path):
		os.makedirs(full_path)
        
	return full_path
