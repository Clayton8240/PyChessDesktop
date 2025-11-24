from PIL import Image, ImageDraw, ImageFont
import os
import sys

# Configurações
TAMANHO = 80  # Tamanho da imagem final (80x80)
COR_BRANCA = (250, 250, 250)
COR_PRETA = (20, 20, 20)
COR_BORDA = (0, 0, 0) # Opcional: Borda para destacar peças brancas

# Mapeamento: Nome do arquivo -> Caractere Unicode (Usamos as versões preenchidas)
# Nota: Usamos os caracteres "Black" (solidos) para ambas as cores, 
# e pintamos com a cor que queremos.
UNICODE_PIECES = {
    'p': '\u265F', # ♟ Peão
    'r': '\u265C', # ♜ Torre
    'n': '\u265E', # ♞ Cavalo
    'b': '\u265D', # ♝ Bispo
    'q': '\u265B', # ♛ Rainha
    'k': '\u265A', # ♚ Rei
}

def encontrar_fonte_sistema():
    """Tenta encontrar uma fonte que tenha símbolos de xadrez."""
    fontes_tentativa = [
        "seguisym.ttf",  # Windows (Segoe UI Symbol - Excelente)
        "arial.ttf",     # Windows (Padrão)
        "DejaVuSans.ttf",# Linux (Padrão)
        "FreeSerif.ttf", # Linux
        "AppleGothic.ttf"# Mac
    ]
    
    for nome_fonte in fontes_tentativa:
        try:
            # Tenta carregar com tamanho 90% da imagem para ocupar bem o espaço
            return ImageFont.truetype(nome_fonte, int(TAMANHO * 0.9))
        except OSError:
            continue
    
    print("AVISO: Nenhuma fonte boa encontrada. Usando padrão (pode ficar feio).")
    return ImageFont.load_default()

def gerar_pecas():
    base_dir = os.path.join('assets', 'images', 'pieces')
    os.makedirs(base_dir, exist_ok=True)
    
    fonte = encontrar_fonte_sistema()
    
    # Gera peças Brancas (w_) e Pretas (b_)
    for cor_nome, cor_rgb in [('w', COR_BRANCA), ('b', COR_PRETA)]:
        for peca_nome, char_unicode in UNICODE_PIECES.items():
            
            # Cria imagem transparente (RGBA)
            img = Image.new('RGBA', (TAMANHO, TAMANHO), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Centraliza o texto
            # (bbox obtém as coordenadas da caixa delimitadora do texto)
            left, top, right, bottom = fonte.getbbox(char_unicode)
            w_text = right - left
            h_text = bottom - top
            
            # Cálculo de posição (x, y)
            pos_x = (TAMANHO - w_text) / 2 - left
            # Ajuste fino vertical (fontes costumam ter baseline deslocada)
            pos_y = (TAMANHO - h_text) / 2 - top - (TAMANHO * 0.1)

            # Desenha uma "sombra/borda" para contraste (opcional, mas recomendado para o branco)
            if cor_nome == 'w':
                offset = 2
                draw.text((pos_x + offset, pos_y + offset), char_unicode, font=fonte, fill=(0,0,0,100))
            
            # Desenha a peça
            draw.text((pos_x, pos_y), char_unicode, font=fonte, fill=cor_rgb)
            
            # Salva
            nome_arquivo = f"{cor_nome}_{peca_nome}.png"
            caminho_final = os.path.join(base_dir, nome_arquivo)
            img.save(caminho_final)
            print(f"Gerado: {nome_arquivo}")

if __name__ == "__main__":
    try:
        gerar_pecas()
        print("\nSucesso! Peças geradas em assets/images/pieces/")
    except Exception as e:
        print(f"Erro: {e}")