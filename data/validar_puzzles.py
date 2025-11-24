import json
import chess
import os

def validar_puzzles():
    input_path = os.path.join('data', 'puzzles.json')
    output_path = os.path.join('data', 'puzzles_validos.json')

    if not os.path.exists(input_path):
        print(f"ERRO: Arquivo não encontrado em {input_path}")
        return

    print(f"--- Iniciando Validação de {input_path} ---")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        try:
            puzzles = json.load(f)
        except json.JSONDecodeError:
            print("ERRO: O arquivo JSON está mal formatado.")
            return

    validos = []
    invalidos = 0

    for i, p in enumerate(puzzles):
        pid = p.get('id', f'Index {i}')
        fen = p.get('fen', '')
        moves = p.get('moves', [])
        desc = p.get('description', '')

        # 1. Valida a FEN (Posição inicial)
        try:
            board = chess.Board(fen)
        except ValueError:
            print(f"[X] ID {pid}: FEN inválida -> {fen}")
            invalidos += 1
            continue

        if not board.is_valid():
            print(f"[X] ID {pid}: Tabuleiro em estado impossível (Reis faltando, etc)")
            invalidos += 1
            continue

        # 2. Valida a sequência de movimentos
        puzzle_ok = True
        for move_uci in moves:
            try:
                move = chess.Move.from_uci(move_uci)
                
                if move in board.legal_moves:
                    board.push(move)
                else:
                    print(f"[X] ID {pid} ({desc}): Movimento ILEGAL {move_uci}")
                    print(f"    Posição FEN: {board.fen()}")
                    puzzle_ok = False
                    break
            except ValueError:
                print(f"[X] ID {pid}: String de movimento inválida '{move_uci}'")
                puzzle_ok = False
                break
        
        if puzzle_ok:
            validos.append(p)
        else:
            invalidos += 1

    # Resumo
    print("-" * 40)
    print(f"Total Processado: {len(puzzles)}")
    print(f"Válidos: {len(validos)}")
    print(f"Inválidos (Removidos): {invalidos}")
    print("-" * 40)

    # Salva o arquivo limpo
    if validos:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(validos, f, indent=4, ensure_ascii=False)
        print(f"Sucesso! Arquivo limpo salvo em: {output_path}")
        print("Recomendação: Renomeie este arquivo para 'puzzles.json' para usar no jogo.")
    else:
        print("Nenhum puzzle válido encontrado.")

if __name__ == "__main__":
    validar_puzzles()