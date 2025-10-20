import webview
import os
import subprocess
import tempfile
import re
import sys

# Força o PyWebView a usar Qt (que já está disponível)
os.environ['PYWEBVIEW_GUI'] = 'qt'

DATA_DIAGRAMAS_DIR = os.path.join(os.path.dirname(__file__), 'data', 'diagramas')
DATA_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'data', 'output_generated_code')

class Api:
    def convert_plantuml(self, code, language='python'):
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
            # Chama o backend via subprocess, passando o nome do diagrama e a linguagem
            # Usa o mesmo executável Python que está executando esta aplicação
            # Tenta primeiro como módulo, depois como script direto
            cmd = [
                sys.executable, '-m', 'back_end.main_cli',
                '--input', temp_file_path,
                '--output', DATA_OUTPUT_DIR,
                '--diagram-name', diagram_name,
                '--language', language  
            ]
            
            # Configura o ambiente para garantir que o Python path inclua o diretório atual
            env = os.environ.copy()
            current_dir = os.path.dirname(os.path.abspath(__file__))
            env['PYTHONPATH'] = current_dir + os.pathsep + env.get('PYTHONPATH', '')
            
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=current_dir)
            
            # Se falhar como módulo, tenta como script direto
            if result.returncode != 0 and "No module named" in (result.stderr or ''):
                print("[DEBUG] Tentativa como módulo falhou, tentando como script direto...")
                cmd = [
                    sys.executable, 'back_end/main_cli.py',
                    '--input', temp_file_path,
                    '--output', DATA_OUTPUT_DIR,
                    '--diagram-name', diagram_name,
                    '--language', language
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=current_dir)
            
            # Debug: Imprime informações sobre o comando executado
            print(f"[DEBUG] Comando executado: {' '.join(cmd)}")
            print(f"[DEBUG] Python utilizado: {sys.executable}")
            print(f"[DEBUG] Diretório de trabalho: {current_dir}")
            print(f"[DEBUG] Código de retorno: {result.returncode}")
            if result.stderr:
                print(f"[DEBUG] Stderr: {result.stderr}")
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                print(f"[DEBUG] Erro detalhado: {error_msg}")
                return f"Erro ao converter: {error_msg}"
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
        "PlantUML para Múltiplas Linguagens",
        url='front_end/interface.html',
        js_api=api,
        width=1200,  # largura diminuída
        height=700   # altura mantida
    )
    webview.start()
