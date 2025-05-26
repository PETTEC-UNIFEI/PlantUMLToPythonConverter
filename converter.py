#!/usr/bin/env python3
"""
Script wrapper para executar o conversor PlantUML para Python
usando o Python correto (do ambiente virtual atual).

Este script garante que o conversor seja executado com o Python
que tem todas as dependências instaladas.

Uso:
    python converter.py [--input caminho/arquivo.puml] [--output pasta_saida]
"""
import os
import sys
import subprocess

def main():
    # Usa o Python que está sendo usado para executar este script
    python_path = sys.executable
    
    # Configura o PYTHONPATH para incluir o diretório atual
    current_dir = os.path.abspath(os.path.dirname(__file__))
    env = os.environ.copy()
    env['PYTHONPATH'] = current_dir + os.pathsep + env.get('PYTHONPATH', '')
    
    # Chama o módulo back_end.main_cli em vez do script diretamente
    cmd = [python_path, "-m", "back_end.main_cli"] + sys.argv[1:]
    
    # Executa o comando e passa o controle para o processo filho
    try:
        print(f"Executando: {' '.join(cmd)}")
        result = subprocess.run(cmd, env=env)
        return result.returncode
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        return 1
    except Exception as e:
        print(f"\nErro ao executar o conversor: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
