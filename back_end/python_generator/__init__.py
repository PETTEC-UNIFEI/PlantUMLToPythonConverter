"""
Pacote responsável por gerar código Python a partir das estruturas do PlantUML.
"""
from .main_generator import MainCodeGenerator # MUDANÇA AQUI
from .utils import sanitize_name_for_python_module, to_pascal_case
from .type_mapper import TypeMapper
from .import_manager import ImportManager
from .structure_generators import ClassGenerator, EnumGenerator, InterfaceGenerator


__all__ = [
    "MainCodeGenerator",
    "sanitize_name_for_python_module",
    "to_pascal_case",
    "TypeMapper",
    "ImportManager",
    "ClassGenerator",
    "EnumGenerator",
    "InterfaceGenerator",
]