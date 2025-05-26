"""
CLI para rodar o backend do conversor PlantUML para Python.

Uso:
    python back_end/main_cli.py [--input caminho/arquivo.puml] [--output pasta_saida]
    
    Se não for especificado um arquivo de entrada, será usado o exemplo_diagrama.plantuml
    da pasta diagramas.
"""

import argparse
import os
import sys
import traceback

# Verificar se o script está sendo executado do diretório correto
current_dir = os.getcwd()
expected_dir = '/home/lucas/Documentos/PlantUMLToPythonConverter/PlantUMLToPythonConverter'
if os.path.basename(current_dir) == 'PlantUMLToPythonConverter' and not current_dir.endswith('PlantUMLToPythonConverter/PlantUMLToPythonConverter'):
    print("\nAVISO: Você parece estar no diretório incorreto.")
    print(f"Diretório atual: {current_dir}")
    print("Execute o script como:")
    print("  python back_end/main_cli.py")
    print("Ou navegue para o diretório correto:")
    print("  cd /home/lucas/Documentos/PlantUMLToPythonConverter/PlantUMLToPythonConverter")
    print("  python back_end/main_cli.py")
    sys.exit(1)

# Verificar se o ply está instalado
try:
    import ply
except ImportError:
    print("Erro: biblioteca 'ply' não instalada. Execute 'pip install ply'")
    sys.exit(1)

# Adiciona o diretório raiz do projeto ao path do Python
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)

# Importa os módulos necessários
try:
    from back_end.plantuml_parser.parser import PlantUMLParser
    from back_end.python_generator.main_generator import MainCodeGenerator
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Execute: python back_end/main_cli.py")
    sys.exit(1)

def main():
    # Parser de argumentos com mensagens de ajuda
    parser = argparse.ArgumentParser(
        description="Conversor PlantUML para Python",
        epilog="Se não for especificado um arquivo de entrada, será usado o exemplo_diagrama.plantuml"
    )
    parser.add_argument('--input', '-i', help='Arquivo PlantUML de entrada')
    parser.add_argument('--output', '-o', default='output_generated_code', help='Diretório de saída')
    args = parser.parse_args()
    
    # Se não for especificado um arquivo de entrada, usa o exemplo
    if not args.input:
        # Tenta encontrar o arquivo de exemplo em diferentes locais
        possible_paths = [
            os.path.join(project_root, 'diagramas', 'exemplo_diagrama.plantuml'),
            os.path.join(project_root, 'diagramas', 'exemplo_diagrama.puml'),
        ]
        
        for path in possible_paths:
            if os.path.isfile(path):
                args.input = path
                print(f"Usando exemplo: {path}")
                break
        
        if not args.input:
            print("Erro: Especifique um arquivo de entrada com --input")
            sys.exit(1)

    # Verificação do arquivo de entrada
    if not os.path.isfile(args.input):
        print(f"Erro: Arquivo não encontrado: {args.input}")
        sys.exit(1)

    # Leitura do arquivo
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
            
        print(f"Convertendo {args.input}...")
        # Processamento do diagrama
        parser_backend = PlantUMLParser()
        diagrama = parser_backend.parse(plantuml_code)
        
        generator = MainCodeGenerator(diagrama, args.output)
        arquivos_gerados = generator.generate_files()
        
        if arquivos_gerados:
            print(f"Arquivos gerados em '{os.path.abspath(args.output)}':")
            for arq in sorted(arquivos_gerados):
                print(f"  - {arq}")
        else:
            print("Nenhum arquivo foi gerado.")

    except SyntaxError as e:
        print(f"Erro de sintaxe: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Erro: {e}")
        traceback.print_exc()
        sys.exit(1)

    return 0

if __name__ == "__main__":
    sys.exit(main())