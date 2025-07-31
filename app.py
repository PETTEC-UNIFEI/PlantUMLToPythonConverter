import webview
import os
import subprocess
import tempfile
import re

DATA_DIAGRAMAS_DIR = os.path.join(os.path.dirname(__file__), 'data', 'diagramas')
DATA_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'data', 'output_generated_code')

class Api:
    def convert_plantuml(self, code):
        try:
            # Extrai o nome do diagrama do código PlantUML
            match = re.search(r'@startuml\s+([\w\-\d_]+)', code)
            if match:
                diagram_name = match.group(1)
            else:
                diagram_name = 'Diagrama'
            # Garante que o diretório existe
            os.makedirs(DATA_DIAGRAMAS_DIR, exist_ok=True)
            os.makedirs(DATA_OUTPUT_DIR, exist_ok=True)
            # Salva o código em um arquivo com o nome do diagrama
            plantuml_filename = f"{diagram_name}.plantuml"
            plantuml_path = os.path.join(DATA_DIAGRAMAS_DIR, plantuml_filename)
            with open(plantuml_path, 'w', encoding='utf-8') as temp_file:
                temp_file.write(code)
            temp_file_path = plantuml_path
            # Chama o backend via subprocess, passando o nome do diagrama
            cmd = [
                'python', 'back_end/main_cli.py',
                '--input', temp_file_path,
                '--output', DATA_OUTPUT_DIR,
                '--diagram-name', diagram_name
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return f"Erro ao converter: {result.stderr or result.stdout}"
            # NOVO: Captura o caminho da pasta gerada a partir da saída do backend
            output_path = None
            for line in (result.stdout or '').splitlines():
                if line.startswith('[PASTA_GERADA]:'):
                    output_path = line.split(':', 1)[1].strip()
                    break
            if not output_path:
                return 'Nenhum diretório de saída encontrado.'
            print(f"[DEBUG] Pasta de saída retornada para o frontend: {output_path}")
            return output_path
        except Exception as e:
            return f"Erro inesperado: {str(e)}"

    def list_dir(self, dir_path):
        try:
            entries = []
            for entry in os.scandir(dir_path):
                entries.append({
                    'name': entry.name,
                    'is_dir': entry.is_dir(),
                    'path': entry.path
                })
            return entries
        except Exception as e:
            return [{"error": str(e)}]

    def read_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Erro ao ler arquivo: {str(e)}"

if __name__ == '__main__':
    api = Api()
    window = webview.create_window(
        "PlantUML para Python",
        url='front_end/interface.html',
        js_api=api,
        width=1200,  # largura diminuída
        height=700   # altura mantida
    )
    webview.start()
