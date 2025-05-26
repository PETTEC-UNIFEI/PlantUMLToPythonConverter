"""
Classe para mapear tipos do PlantUML para type hints do Python.

Também identifica quais imports são necessários para cada tipo.
"""
from typing import Optional, Tuple, Set, List, Any as TypingAny # Renomeado para evitar conflito
import re
from .utils import to_pascal_case

class TypeMapper:
    """
    Responsável por converter tipos PlantUML em type hints Python e
    informar quais imports são necessários para cada caso.
    """
    def __init__(self, all_defined_structure_names: Set[str], structure_module_paths: dict[str, str]):
        """
        Inicializa uma nova instância do TypeMapper.

        Args:
            all_defined_structure_names: Um conjunto com todos os nomes originais
                                         de estruturas (classes, enums, interfaces)
                                         definidas no diagrama PlantUML.
            structure_module_paths: Um dicionário mapeando nomes originais de estruturas
                                    para seus caminhos de módulo Python (sanitizados e
                                    pontilhados).
        """
        self.all_defined_structure_names: Set[str] = all_defined_structure_names
        self.structure_module_paths: dict[str, str] = structure_module_paths
        self.type_mapping: dict[str, str] = {
            "String": "str", "string": "str", "Integer": "int", "int": "int", "float": "float",
            "Boolean": "bool", "boolean": "bool", "Date": "datetime.date", "void": "None"
        }
        self.typing_module_primitives: Set[str] = {"List", "Optional", "Dict", "Set", "Tuple", "Union", "Any", "Callable"}

    def get_python_type_hint_and_imports(self, plantuml_type: str, current_file_module_dot_path: str, for_heritage_list: bool = False):
        """
        Recebe um tipo PlantUML e retorna o type hint Python correspondente,
        além dos imports padrão e do módulo typing necessários.

        Args:
            plantuml_type: Tipo conforme definido no PlantUML.
            current_file_module_dot_path: Caminho do módulo Python atual.
            for_heritage_list: Se True, retorna o nome direto para herança.

        Returns:
            Tuple com o type hint, imports padrão e imports do typing.
        """
        standard_imports: Set[str] = set()
        typing_imports: Set[str] = set() 

        # Corrige o mapeamento para string
        if plantuml_type is None:
            typing_imports.add("Any")
            return "Any", set(), typing_imports
        type_str = str(plantuml_type).strip()
        # Corrige mapeamento de String para str (não importa do typing)
        if type_str.lower() == "string":
            return "str", set(), set()

        if not plantuml_type:
            typing_imports.add("Any")
            return "Any", standard_imports, typing_imports

        # Remove aspas extras do tipo antes de processar
        plantuml_type = plantuml_type.strip().replace("''", "").replace("'", "").replace('"', "")

        generic_match = re.match(r"(\w+)\s*<\s*([^>]+)\s*>", plantuml_type)
        if generic_match:
            outer_type_plantuml = generic_match.group(1)
            inner_types_plantuml_str = generic_match.group(2)
            
            python_outer_type = self.type_mapping.get(outer_type_plantuml, outer_type_plantuml)
            if outer_type_plantuml in self.typing_module_primitives:
                python_outer_type = outer_type_plantuml
                typing_imports.add(python_outer_type)
            elif outer_type_plantuml.lower() == "list":
                python_outer_type = "List"
                typing_imports.add("List")
            elif outer_type_plantuml.lower() == "map":
                python_outer_type = "Dict"
                typing_imports.add("Dict")

            inner_python_hints = []
            for inner_puml_type in inner_types_plantuml_str.split(','):
                inner_puml_type = inner_puml_type.strip()
                inner_hint, s_imps, t_imps = self.get_python_type_hint_and_imports(
                    inner_puml_type, current_file_module_dot_path, for_heritage_list
                )
                inner_python_hints.append(inner_hint)
                standard_imports.update(s_imps)
                typing_imports.update(t_imps)
            
            return f"{python_outer_type}[{', '.join(inner_python_hints)}]", standard_imports, typing_imports

        if plantuml_type in self.type_mapping:
            py_type = self.type_mapping[plantuml_type]
            if py_type == "datetime.date":
                standard_imports.add("import datetime")
            # Não adicionar "Date" ao typing_imports nunca
            return py_type, standard_imports, typing_imports

        if plantuml_type in self.typing_module_primitives:
            typing_imports.add(plantuml_type)
            return plantuml_type, standard_imports, typing_imports

        if plantuml_type in self.all_defined_structure_names:
            pascal_case_type = to_pascal_case(plantuml_type)
            if for_heritage_list:
                 return pascal_case_type, standard_imports, typing_imports
            # Sempre retorna com apenas uma aspa simples para forward reference
            return f"'{pascal_case_type}'", standard_imports, typing_imports

        typing_imports.add("Any")
        return "Any", standard_imports, typing_imports