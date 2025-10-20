"""
Este arquivo testa se o gerador converte um diagrama PlantUML em arquivos Python válidos, 
criando as classes e métodos esperados no local correto. O teste usa um exemplo simples e 
verifica se o arquivo gerado contém a estrutura esperada.
"""
import sys
import os
import shutil
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from back_end.python_generator.main_generator import gerar_codigo_python

EXEMPLO_DIAGRAMA = """
@startuml TesteGerador
class Pessoa {
  -nome: str
  +get_nome(): str
}
@enduml
"""

def test_geracao_codigo(tmp_path):
    output_dir = tmp_path / "saida"
    output_dir.mkdir()
    gerar_codigo_python(EXEMPLO_DIAGRAMA, str(output_dir))
    subpastas = [p for p in output_dir.iterdir() if p.is_dir()]
    assert subpastas, "Nenhuma subpasta foi criada pelo gerador"
    pasta_gerada = subpastas[0]
    pessoa_py = pasta_gerada / "pessoa.py"
    assert pessoa_py.exists(), f"Arquivo pessoa.py não foi gerado em {pasta_gerada}"
    conteudo = pessoa_py.read_text(encoding="utf-8")
    assert "class Pessoa" in conteudo
    assert "def get_nome" in conteudo
