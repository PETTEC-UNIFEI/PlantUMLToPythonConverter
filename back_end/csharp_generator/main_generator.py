from typing import List, Set, Optional, Union, Any, Tuple, Dict, Callable, TYPE_CHECKING
import os
import re

from back_end.plantuml_parser.data_structures import (
    PlantUMLDiagrama, PlantUMLClasse, PlantUMLEnum, PlantUMLInterface, PlantUMLPacote
)

from .type_mapper import TypeMapper
from .using_manager import UsingManager
from .structure_generators import ClassGenerator, EnumGenerator, InterfaceGenerator

class MainCodeGenerator:
    def __init(self):
        pass

    def collected_all_structure_names(self):
        pass

    def _map_structure_module_paths(self):
        pass

    def _generate_file_for_structure(self):
        pass

    def _create_package_init(self):
        pass

    def generate_files(self):
        pass