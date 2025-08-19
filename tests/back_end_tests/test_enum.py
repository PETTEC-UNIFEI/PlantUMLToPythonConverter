"""
Este arquivo testa se o parser reconhece corretamente enums definidos em PlantUML
e se os valores declarados aparecem na estrutura Python gerada.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from back_end.plantuml_parser.parser import PlantUMLParser
from back_end.plantuml_parser.data_structures.plantuml_enum import PlantUMLEnum

EXEMPLO_ENUM = """
@startuml
enum Status {
  ATIVO
  INATIVO
}
@enduml
"""

def test_parse_enum():
    parser = PlantUMLParser()
    diagrama = parser.parse(EXEMPLO_ENUM)
    enum = next((e for e in diagrama.elementos if isinstance(e, PlantUMLEnum) and e.nome == "Status"), None)
    assert enum is not None
    assert "ATIVO" in enum.valores_enum
    assert "INATIVO" in enum.valores_enum
