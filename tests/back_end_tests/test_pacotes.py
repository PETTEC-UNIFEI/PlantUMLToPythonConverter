"""
Este arquivo testa se o parser identifica pacotes e suas classes internas corretamente,
como seria esperado em projetos organizados por módulos.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from back_end.plantuml_parser.parser import PlantUMLParser
from back_end.plantuml_parser.data_structures.plantuml_pacote import PlantUMLPacote

# Diagrama de exemplo com um pacote chamado PacoteExemplo e uma classe interna ClassePacote.
EXEMPLO_PACOTE = """
@startuml
package "PacoteExemplo" {
  class ClassePacote {}
}
@enduml
"""

def test_parse_pacote():
    parser = PlantUMLParser()
    diagrama = parser.parse(EXEMPLO_PACOTE)
    pacote = next((e for e in diagrama.elementos if isinstance(e, PlantUMLPacote) and e.nome == "PacoteExemplo"), None)
    assert pacote is not None
    assert any(getattr(c, "nome", None) == "ClassePacote" for c in pacote.elementos)
