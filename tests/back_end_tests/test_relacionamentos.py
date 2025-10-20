"""
Este arquivo valida se todos os tipos de relacionamento entre classes
(associação, herança, implementação, etc.) são reconhecidos e classificados corretamente.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from back_end.plantuml_parser.parser import PlantUMLParser
from back_end.plantuml_parser.data_structures.plantuml_relacionamento import PlantUMLRelacionamento

EXEMPLOS_REL = [
    ("A -- B : 'associacao'", "associacao"),
    ("A <|-- B : 'heranca'", "heranca"),
    ("A <|.. B : 'implementacao'", "implementacao"),
    ("A *-- B : 'composicao'", "composicao"),
    ("A o-- B : 'agregacao'", "agregacao"),
    ("A ..> B : 'dependencia'", "dependencia"),
]

BASE = """
@startuml
class A {{}}
class B {{}}
{rel}
@enduml
"""

def test_todos_tipos_relacionamento():
    for rel_str, tipo_esperado in EXEMPLOS_REL:
        exemplo = BASE.format(rel=rel_str)
        parser = PlantUMLParser()
        diagrama = parser.parse(exemplo)
        rel = next((r for r in diagrama.relacionamentos if r.origem == "A" and r.destino == "B"), None)
        assert rel is not None, f"Relacionamento não encontrado para: {rel_str}"
        assert rel.tipo == tipo_esperado, f"Tipo esperado: {tipo_esperado}, obtido: {rel.tipo}"

def test_parse_relacionamento_associacao():
    exemplo = BASE.format(rel='A -- B : "relaciona"')
    parser = PlantUMLParser()
    diagrama = parser.parse(exemplo)
    rel = next((r for r in diagrama.relacionamentos if r.origem == "A" and r.destino == "B"), None)
    assert rel is not None
    assert rel.label == "relaciona"
    assert rel.tipo == "associacao"
