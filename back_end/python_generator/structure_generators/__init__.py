"""
Pacote structure_generators.

Este subpacote do python_generator contém classes dedicadas a gerar
o corpo de código específico para cada tipo de estrutura PlantUML
(classes, enums, interfaces).

Cada gerador de estrutura é responsável por traduzir os detalhes
de um objeto PlantUML (como PlantUMLClasse, PlantUMLEnum) para
as linhas de código Python correspondentes que definem atributos,
métodos, construtores, etc.
"""
from .class_generator import ClassGenerator
from .enum_generator import EnumGenerator
from .interface_generator import InterfaceGenerator

__all__ = [
    "ClassGenerator",
    "EnumGenerator",
    "InterfaceGenerator",
]