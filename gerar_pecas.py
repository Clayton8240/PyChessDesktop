from PIL import Image, ImageDraw, ImageFont
import os

# Pasta onde as imagens serão salvas
dir_path = os.path.join('assets', 'images')
os.makedirs(dir_path, exist_ok=True)

# Tamanho da imagem e fonte
img_size = (80, 80)
font_size = 48

# Letras das peças e nomes dos arquivos
pecas = {
    'w_p': ('P', (255, 255, 255), (0, 0, 0)),   # Peão branco
    'b_p': ('P', (0, 0, 0), (255, 255, 255)),   # Peão preto
    'w_r': ('R', (255, 255, 255), (0, 0, 0)),   # Torre branca
    'b_r': ('R', (0, 0, 0), (255, 255, 255)),   # Torre preta
    'w_n': ('N', (255, 255, 255), (0, 0, 0)),   # Cavalo branco
    'b_n': ('N', (0, 0, 0), (255, 255, 255)),   # Cavalo preto
    'w_b': ('B', (255, 255, 255), (0, 0, 0)),   # Bispo branco
    'b_b': ('B', (0, 0, 0), (255, 255, 255)),   # Bispo preto
    'w_q': ('Q', (255, 255, 255), (0, 0, 0)),   # Rainha branca
    'b_q': ('Q', (0, 0, 0), (255, 255, 255)),   # Rainha preta
    'w_k': ('K', (255, 255, 255), (0, 0, 0)),   # Rei branco
    'b_k': ('K', (0, 0, 0), (255, 255, 255)),   # Rei preto
}

# Tenta carregar uma fonte padrão do sistema
try:
    font = ImageFont.truetype("arial.ttf", font_size)
except:
    font = ImageFont.load_default()

for nome, (letra, cor_fundo, cor_texto) in pecas.items():
    img = Image.new('RGB', img_size, color=cor_fundo)
    draw = ImageDraw.Draw(img)
    # Usar getbbox para calcular o tamanho do texto (compatível com Pillow >= 8.0)
    bbox = font.getbbox(letra)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pos = ((img_size[0] - w) // 2, (img_size[1] - h) // 2)
    draw.text(pos, letra, fill=cor_texto, font=font)
    img.save(os.path.join(dir_path, f"{nome}.png"))

print("Imagens das peças geradas em assets/images/")
