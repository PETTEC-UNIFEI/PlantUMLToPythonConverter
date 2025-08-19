"""
Este arquivo cobre o parsing de classes, atributos e métodos,
garantindo que o parser extrai corretamente as informações do diagrama PlantUML.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from back_end.plantuml_parser.parser import PlantUMLParser
from back_end.plantuml_parser.data_structures.plantuml_classe import PlantUMLClasse

EXEMPLO_DIAGRAMA = """
@startuml TesteParser
class Pessoa {
  -nome: str
  +get_nome(): str
}
@enduml
"""

def test_parse_classe():
    parser = PlantUMLParser()
    diagrama = parser.parse(EXEMPLO_DIAGRAMA)
    pessoa = next((e for e in diagrama.elementos if isinstance(e, PlantUMLClasse) and e.nome == "Pessoa"), None)
    assert pessoa is not None
    assert any(a.nome == "nome" for a in pessoa.atributos)
    assert any(m.nome == "get_nome" for m in pessoa.metodos)

def test_parse_metodo_tipo():
    parser = PlantUMLParser()
    diagrama = parser.parse(EXEMPLO_DIAGRAMA)
    pessoa = next((e for e in diagrama.elementos if isinstance(e, PlantUMLClasse) and e.nome == "Pessoa"), None)
    metodo = next((m for m in pessoa.metodos if m.nome == "get_nome"), None)
    assert metodo is not None
    assert metodo.tipo_retorno == "str"
