"""
Este arquivo testa se o parser reconhece corretamente interfaces e seus métodos em diagramas PlantUML.
Ele utiliza um exemplo simples de interface e verifica se o método esperado é identificado na estrutura Python.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from back_end.plantuml_parser.parser import PlantUMLParser
from back_end.plantuml_parser.data_structures.plantuml_interface import PlantUMLInterface

EXEMPLO_INTERFACE = """
@startuml
interface IExemplo {
  +metodo()
}
@enduml
"""

def test_parse_interface():
    parser = PlantUMLParser()
    diagrama = parser.parse(EXEMPLO_INTERFACE)
    interface = next((e for e in diagrama.elementos if isinstance(e, PlantUMLInterface) and e.nome == "IExemplo"), None)
    assert interface is not None
    assert any(m.nome == "metodo" for m in interface.metodos)
