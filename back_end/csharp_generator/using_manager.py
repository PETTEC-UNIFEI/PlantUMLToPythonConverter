from typing import Set, List, Optional, Union, TYPE_CHECKING, Any as TypingAny
# from .utils import to_pascal_case, sanitize_name_for_python_module
import os 
import re 

from back_end.plantuml_parser import data_structures
from back_end.plantuml_parser.data_structures import PlantUMLClasse, PlantUMLEnum, PlantUMLInterface

class UsingManager:
    def __init__(self):
        pass

    def calculate_relative_using_path(self):
        pass

    def colected_using_for_structure(self):
        pass