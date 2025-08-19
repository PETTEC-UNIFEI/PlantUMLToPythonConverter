"""
Módulo ImportManager para o gerador de código Python.
"""
from typing import Set, List, Optional, Union, TYPE_CHECKING, Any as TypingAny
from .utils import to_pascal_case, sanitize_name_for_python_module
import os 
import re 

from back_end.plantuml_parser import data_structures
from back_end.plantuml_parser.data_structures import PlantUMLClasse, PlantUMLEnum, PlantUMLInterface


if TYPE_CHECKING:
    from .type_mapper import TypeMapper

class ImportManager:
    """Gerencia a coleta e formatação de instruções de import para os arquivos Python."""
    def __init__(self, 
                 all_defined_structure_names: Set[str], 
                 structure_module_paths: dict[str, str]):
        self.all_defined_structure_names: Set[str] = all_defined_structure_names
        self.structure_module_paths: dict[str, str] = structure_module_paths

    def _calculate_relative_import_path(self, 
                                        target_original_plantuml_name: str, 
                                        current_file_module_dot_path: str
                                        ) -> Optional[str]:
        """Calcula a string de import relativo para uma estrutura alvo."""
        target_pascal_case_name = to_pascal_case(target_original_plantuml_name)
        target_module_full_dot_path = self.structure_module_paths.get(target_original_plantuml_name)

        if not target_module_full_dot_path or target_module_full_dot_path == current_file_module_dot_path:
            return None 

        current_path_list = current_file_module_dot_path.split('.')
        target_path_list = target_module_full_dot_path.split('.')
        
        current_package_path_list = current_path_list[:-1]
        target_package_path_list = target_path_list[:-1]
        target_module_name_itself = target_path_list[-1]

        if current_package_path_list == target_package_path_list:
            return f"from .{target_module_name_itself} import {target_pascal_case_name}"

        common_ancestor_len = 0
        while (common_ancestor_len < len(current_package_path_list) and
               common_ancestor_len < len(target_package_path_list) and
               current_package_path_list[common_ancestor_len] == target_package_path_list[common_ancestor_len]):
            common_ancestor_len += 1

        levels_up = len(current_package_path_list) - common_ancestor_len
        path_down_from_ancestor = target_package_path_list[common_ancestor_len:]
        
        import_prefix = "." * levels_up if levels_up > 0 else ""
        
        # Se não subiu e não estão no mesmo pacote, significa que o atual é ancestral do alvo, ou são irmãos na raiz
        if not import_prefix:
             import_prefix = "."
        
        from_path_parts = [import_prefix] if import_prefix != "." else ["."]
        if import_prefix.startswith("."):
            from_path_parts = [import_prefix]
        else:
            from_path_parts = []


        from_path_parts.extend(path_down_from_ancestor)
        from_path_parts.append(target_module_name_itself)
        
        final_from_path = ".".join(s for s in from_path_parts if s)
        if import_prefix == "." and not path_down_from_ancestor and final_from_path == target_module_name_itself:
            final_from_path = f".{target_module_name_itself}"
        elif not final_from_path.startswith(".") and final_from_path:
             final_from_path = "." + final_from_path


        if not final_from_path or final_from_path == ".":
            return f"from .{target_module_name_itself} import {target_pascal_case_name}"

        return f"from {final_from_path} import {target_pascal_case_name}"

    def collect_imports_for_structure(self, 
                                      structure: Union[PlantUMLClasse, PlantUMLEnum, PlantUMLInterface], 
                                      type_mapper: "TypeMapper",
                                      current_file_module_dot_path: str,
                                      inheritance_from_relationships: List[str] = None,
                                      relationships_for_structure: List = None
                                      ) -> List[str]:
        """Coleta e formata todas as instruções de import necessárias."""
        standard_imports: Set[str] = set()
        typing_imports_needed: Set[str] = set() 
        relative_imports: Set[str] = set()
        relative_imports_for_heritage: Set[str] = set()

        if isinstance(structure, data_structures.PlantUMLEnum):
            standard_imports.add("from enum import Enum, auto")
        
        has_abstract_methods = any(m.is_abstract for m in structure.metodos)
        is_interface_or_abstract_class = isinstance(structure, data_structures.PlantUMLInterface) or \
                                         (isinstance(structure, data_structures.PlantUMLClasse) and (structure.is_abstract or has_abstract_methods))
        if is_interface_or_abstract_class:
            standard_imports.add("from abc import ABC, abstractmethod")

        # Coleta todos os nomes de tipos PlantUML usados
        all_types_to_resolve_plantuml: Set[Optional[str]] = set()
        
        # Coleta nomes de tipos usados como herança
        parent_type_names_plantuml: List[str] = []
        if isinstance(structure, data_structures.PlantUMLClasse):
            if structure.classe_pai: parent_type_names_plantuml.append(structure.classe_pai)
            parent_type_names_plantuml.extend(structure.interfaces_implementadas or [])
        elif isinstance(structure, data_structures.PlantUMLInterface):
            parent_type_names_plantuml.extend(structure.interfaces_pai or [])
        
        # Adicionar herança dos relacionamentos
        if inheritance_from_relationships:
            parent_type_names_plantuml.extend(inheritance_from_relationships)
            
        all_types_to_resolve_plantuml.update(parent_type_names_plantuml)

        # Adicionar tipos dos relacionamentos
        if relationships_for_structure:
            for rel in relationships_for_structure:
                all_types_to_resolve_plantuml.add(rel.destino)
                # Adicionar Optional para relacionamentos (parâmetros do __init__)
                typing_imports_needed.add("Optional")
                # Adicionar List para relacionamentos múltiplos
                is_multiple = rel.cardinalidade_destino and ("*" in rel.cardinalidade_destino or rel.cardinalidade_destino.strip() in ["0..*", "1..*", "n"])
                if is_multiple:
                    typing_imports_needed.add("List")

        if isinstance(structure, (data_structures.PlantUMLClasse, data_structures.PlantUMLInterface)):
            for attr in structure.atributos:
                all_types_to_resolve_plantuml.add(attr.tipo)
            for met in structure.metodos:
                all_types_to_resolve_plantuml.add(met.tipo_retorno)
                for param in met.parametros:
                    all_types_to_resolve_plantuml.add(param.tipo)
        
        # Processar cada tipo PlantUML para obter hints Python e imports
        for puml_type_name in all_types_to_resolve_plantuml:
            _hint_str, s_imps, t_imps = type_mapper.get_python_type_hint_and_imports(
                puml_type_name, current_file_module_dot_path, False 
            )
            standard_imports.update(s_imps)
            typing_imports_needed.update(t_imps)
            
            if puml_type_name:
                # Lógica para import relativo
                types_to_check_for_relative_import_stack = [puml_type_name]
                processed_for_relative_import : Set[str] = set()

                while types_to_check_for_relative_import_stack:
                    current_puml_type_for_rel = types_to_check_for_relative_import_stack.pop()
                    if not current_puml_type_for_rel or current_puml_type_for_rel in processed_for_relative_import:
                        continue
                    processed_for_relative_import.add(current_puml_type_for_rel)

                    base_type_for_rel_import = current_puml_type_for_rel
                    generic_match_base = re.match(r"(\w+)\s*<([^>]+)>", current_puml_type_for_rel)
                    
                    if generic_match_base:
                        base_type_for_rel_import = generic_match_base.group(1)
                        inner_content = generic_match_base.group(2)
                        inner_types = [t.strip() for t in inner_content.split(',')]
                        for t_inside in inner_types:
                            if t_inside not in processed_for_relative_import:
                                types_to_check_for_relative_import_stack.append(t_inside)
                        continue 
                    
                    if base_type_for_rel_import and base_type_for_rel_import in self.all_defined_structure_names:
                        rel_imp = self._calculate_relative_import_path(base_type_for_rel_import, current_file_module_dot_path)
                        if rel_imp:
                            if base_type_for_rel_import in parent_type_names_plantuml:
                                relative_imports_for_heritage.add(rel_imp)
                            else:
                                relative_imports.add(rel_imp)

        # Adicionar Optional para parâmetros do __init__
        if isinstance(structure, data_structures.PlantUMLClasse):
            for attr in structure.atributos:
                if not attr.is_static:
                    py_type_hint, _s, t_imps_attr = type_mapper.get_python_type_hint_and_imports(attr.tipo, current_file_module_dot_path)
                    typing_imports_needed.update(t_imps_attr) 
                    if attr.default_value is not None or \
                       (py_type_hint not in ["str", "int", "float", "bool", "Any", "None", "datetime.date"] and not py_type_hint.startswith("'")):
                        typing_imports_needed.add("Optional")
                else:
                    # CORREÇÃO 5: Adicionar ClassVar para atributos estáticos
                    typing_imports_needed.add("ClassVar")
                        
        # Formatar Bloco de Imports
        import_lines: List[str] = []
        
        if standard_imports:
            import_lines.extend(sorted(list(standard_imports)))

        if relative_imports_for_heritage:
            import_lines.extend(sorted(list(relative_imports_for_heritage)))

        if typing_imports_needed:
            valid_typing_imports = {t for t in typing_imports_needed if t and t != "None"}
            if relative_imports:
                valid_typing_imports.add("TYPE_CHECKING")
            if valid_typing_imports:
                if import_lines and not (import_lines[-1].startswith("from typing import") or import_lines[-1].strip() == ""):
                    import_lines.append("")
                import_lines.append(f"from typing import {', '.join(sorted(list(valid_typing_imports)))}")
        elif relative_imports:
            import_lines.append("from typing import TYPE_CHECKING")

        if relative_imports:
            if import_lines and import_lines[-1].strip() != "":
                import_lines.append("")
            import_lines.append("if TYPE_CHECKING:")
            for rel_imp in sorted(list(relative_imports)):
                import_lines.append(f"    {rel_imp}")

        if import_lines and (not import_lines[-1] or import_lines[-1].strip() != ""):
            import_lines.append("")

        return import_lines