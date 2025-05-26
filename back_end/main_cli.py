"""
CLI para rodar o backend do conversor PlantUML para Python.

Uso:
    python3 -m back_end.main_cli --input caminho/arquivo.puml --output pasta_saida
"""

import argparse
import os
# Ajuste nos imports para refletir a estrutura de pacotes
from .plantuml_parser.parser import PlantUMLParser 
from .python_generator.main_generator import MainCodeGenerator

def main():
    parser = argparse.ArgumentParser(description="Conversor PlantUML para Python (backend CLI)")
    parser.add_argument('--input', '-i', required=True, help='Arquivo PlantUML de entrada (.plantuml)')
    parser.add_argument('--output', '-o', default='output_generated_code', help='Diretório de saída para os arquivos Python gerados')
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Arquivo de entrada não encontrado: {args.input}")
        exit(1)

    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
    except Exception as e:
        print(f"Erro ao ler o arquivo de entrada '{args.input}': {e}")
        exit(1)

    print(f"--- Iniciando conversão do arquivo '{args.input}' ---")
    
    try:
        parser_backend = PlantUMLParser()
        diagrama = parser_backend.parse(plantuml_code)
        print(f"--- Parsing concluído ---")
        # print(diagrama) # Para depurar o diagrama parseado

        generator = MainCodeGenerator(diagrama, args.output)
        arquivos_gerados = generator.generate_files()
        print(f"--- Geração de código concluída ---")

        if arquivos_gerados:
            print(f"\nArquivos Python gerados em '{os.path.abspath(args.output)}':")
            for arq in sorted(arquivos_gerados):
                print(f"  - {arq}")
        else:
            print("Nenhum arquivo Python foi gerado.")

    except SyntaxError as e:
        print(f"\nERRO DE SINTAXE no PARSER: {e}")
    except Exception as e:
        print(f"\nERRO INESPERADO DURANTE A CONVERSÃO: {e}")

    print("\n--- Conversão concluída ---")

if __name__ == "__main__":
    main()