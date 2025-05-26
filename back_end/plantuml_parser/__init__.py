"""
Pacote principal para parsing de diagramas PlantUML.

Inclui o parser e as estruturas de dados necessárias para representar o diagrama.
"""

from .parser import PlantUMLParser
from . import data_structures

__all__ = [
    "PlantUMLParser",
    "data_structures",
]