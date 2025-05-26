"""
Pacote com as estruturas de dados do PlantUML.

Define as classes que representam os elementos do diagrama, como atributos,
métodos, relacionamentos, pacotes, etc.
"""

from .plantuml_parametro import PlantUMLParametro
from .plantuml_atributo import PlantUMLAtributo
from .plantuml_metodo import PlantUMLMetodo
from .plantuml_estrutura_base import PlantUMLEstruturaBase
from .plantuml_classe import PlantUMLClasse
from .plantuml_enum import PlantUMLEnum
from .plantuml_interface import PlantUMLInterface
from .plantuml_relacionamento import PlantUMLRelacionamento
from .plantuml_pacote import PlantUMLPacote
from .plantuml_diagrama import PlantUMLDiagrama

__all__ = [
    "PlantUMLParametro",
    "PlantUMLAtributo",
    "PlantUMLMetodo",
    "PlantUMLEstruturaBase",
    "PlantUMLClasse",
    "PlantUMLEnum",
    "PlantUMLInterface",
    "PlantUMLRelacionamento",
    "PlantUMLPacote",
    "PlantUMLDiagrama",
]