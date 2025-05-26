"""
Módulo ImportManager para o gerador de código Python.

Define a classe ImportManager, responsável por determinar e formatar
as instruções de import necessárias para cada arquivo Python gerado.
Isso inclui imports de módulos padrão, do pacote 'typing', e
imports relativos entre os módulos gerados a partir do diagrama PlantUML,
usando blocos TYPE_CHECKING para evitar imports circulares em tempo de execução.
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
    """
    Gerencia a coleta e formatação de instruções de import para os
    arquivos Python gerados.
    """
    def __init__(self, 
                 all_defined_structure_names: Set[str], 
                 structure_module_paths: dict[str, str]):
        """
        Inicializa uma nova instância do ImportManager.

        Args:
            all_defined_structure_names: Um conjunto com todos os nomes originais
                                         de estruturas (classes, enums, interfaces)
                                         definidas no diagrama PlantUML.
            structure_module_paths: Um dicionário mapeando nomes originais de estruturas
                                    para seus caminhos de módulo Python (sanitizados e
                                    pontilhados, ex: 'pacote.subpacote.nome_modulo').
        """
        self.all_defined_structure_names: Set[str] = all_defined_structure_names
        self.structure_module_paths: dict[str, str] = structure_module_paths

    def _calculate_relative_import_path(self, 
                                        target_original_plantuml_name: str, 
                                        current_file_module_dot_path: str
                                        ) -> Optional[str]:
        """
        Calcula a string de import relativo para uma estrutura alvo,
        dado o caminho do módulo do arquivo atual.
        """
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
        
        # Se não subiu (import_prefix vazio), e não estão no mesmo pacote (já tratado), 
        # significa que o atual é ancestral do alvo, ou são irmãos na raiz.
        # O prefixo para descer a partir do nível atual ou da raiz é "."
        if not import_prefix:
             import_prefix = "."
        
        from_path_parts = [import_prefix] if import_prefix != "." else ["."] # Evitar "..pacote" se for só "."
        # Se o prefixo já tem pontos (ex: ".."), não adicionar outro "." inicial do join
        if import_prefix.startswith("."):
            from_path_parts = [import_prefix]
        else: # Se for vazio (ambos na raiz, mas módulos diferentes), o join abaixo adiciona o "."
            from_path_parts = []


        from_path_parts.extend(path_down_from_ancestor)
        from_path_parts.append(target_module_name_itself)
        
        # Remover pontos iniciais redundantes se path_down_from_ancestor começar vazio
        # e o prefixo for só "."
        final_from_path = ".".join(s for s in from_path_parts if s)
        if import_prefix == "." and not path_down_from_ancestor and final_from_path == target_module_name_itself:
            # Caso de mesmo pacote, ex: from .modulo_alvo import Classe
            final_from_path = f".{target_module_name_itself}"
        elif not final_from_path.startswith(".") and final_from_path : # Se não começou com ponto, adicionar um
             final_from_path = "." + final_from_path


        if not final_from_path or final_from_path == ".": 
            # print(f"AVISO: Caminho de import relativo resultou em '.' para {target_pascal_case_name} de {current_file_module_dot_path}")
            return f"from .{target_module_name_itself} import {target_pascal_case_name}" # Fallback

        return f"from {final_from_path} import {target_pascal_case_name}"

    def collect_imports_for_structure(self, 
                                      structure: Union[PlantUMLClasse, PlantUMLEnum, PlantUMLInterface], 
                                      type_mapper: "TypeMapper",
                                      current_file_module_dot_path: str
                                      ) -> List[str]:
        """
        Coleta e formata todas as instruções de import necessárias para
        um arquivo de estrutura Python.
        """
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

        # Coleta todos os nomes de tipos PlantUML usados na estrutura
        all_types_to_resolve_plantuml: Set[Optional[str]] = set()
        
        # Coleta nomes de tipos usados como base de herança
        parent_type_names_plantuml: List[str] = []
        if isinstance(structure, data_structures.PlantUMLClasse):
            if structure.classe_pai: parent_type_names_plantuml.append(structure.classe_pai)
            parent_type_names_plantuml.extend(structure.interfaces_implementadas or [])
        elif isinstance(structure, data_structures.PlantUMLInterface):
            parent_type_names_plantuml.extend(structure.interfaces_pai or [])
        all_types_to_resolve_plantuml.update(parent_type_names_plantuml)

        if isinstance(structure, (data_structures.PlantUMLClasse, data_structures.PlantUMLInterface)):
            for attr in structure.atributos:
                all_types_to_resolve_plantuml.add(attr.tipo)
            for met in structure.metodos:
                all_types_to_resolve_plantuml.add(met.tipo_retorno)
                for param in met.parametros:
                    all_types_to_resolve_plantuml.add(param.tipo)
        
        # Processar cada tipo PlantUML para obter hints Python e necessidades de import
        for puml_type_name in all_types_to_resolve_plantuml:
            # `get_python_type_hint_and_imports` retorna (hint_str, standard_imports_set, typing_imports_set)
            # Onde typing_imports_set contém os NOMES dos tipos de typing (ex: "Any", "List")
            _hint_str, s_imps, t_imps = type_mapper.get_python_type_hint_and_imports(
                puml_type_name, current_file_module_dot_path, False 
            )
            standard_imports.update(s_imps)
            typing_imports_needed.update(t_imps) # Acumula "List", "Optional", "Any", etc.
            
            if puml_type_name: # Só faz sentido para imports relativos se houver um nome
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
                        base_type_for_rel_import = generic_match_base.group(1) # O tipo externo (ex: List)
                        inner_content = generic_match_base.group(2)
                        inner_types = [t.strip() for t in inner_content.split(',')]
                        for t_inside in inner_types:
                            if t_inside not in processed_for_relative_import:
                                types_to_check_for_relative_import_stack.append(t_inside)
                        # Não adicionar import relativo para o tipo genérico externo (List, Dict)
                        # Apenas para os tipos internos se forem definidos pelo usuário
                        continue 
                    
                    if base_type_for_rel_import and base_type_for_rel_import in self.all_defined_structure_names:
                        rel_imp = self._calculate_relative_import_path(base_type_for_rel_import, current_file_module_dot_path)
                        if rel_imp:
                            # Se o tipo é usado como base de herança, precisa do import em tempo de execução
                            if base_type_for_rel_import in parent_type_names_plantuml:
                                relative_imports_for_heritage.add(rel_imp)
                            else:
                                relative_imports.add(rel_imp)

        # Adicionar Optional implicitamente se necessário para parâmetros do __init__
        if isinstance(structure, data_structures.PlantUMLClasse):
            for attr in structure.atributos:
                if not attr.is_static:
                    py_type_hint, _s, t_imps_attr = type_mapper.get_python_type_hint_and_imports(attr.tipo, current_file_module_dot_path)
                    typing_imports_needed.update(t_imps_attr) 
                    if attr.default_value is not None or \
                       (py_type_hint not in ["str", "int", "float", "bool", "Any", "None", "datetime.date"] and not py_type_hint.startswith("'")):
                        typing_imports_needed.add("Optional")
                        
        # --- Formatar Bloco de Imports ---
        import_lines: List[str] = []
        # Standard imports (ex: from enum import Enum, import datetime)
        if standard_imports:
            import_lines.extend(sorted(list(standard_imports)))

        # Imports relativos necessários para herança (fora do TYPE_CHECKING)
        if relative_imports_for_heritage:
            import_lines.extend(sorted(list(relative_imports_for_heritage)))

        # Typing imports (ex: from typing import Any, List, Optional, TYPE_CHECKING)
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

        # Relative imports para type hints (dentro de TYPE_CHECKING)
        if relative_imports:
            if import_lines and import_lines[-1].strip() != "":
                import_lines.append("")
            import_lines.append("if TYPE_CHECKING:")
            for rel_imp in sorted(list(relative_imports)):
                import_lines.append(f"    {rel_imp}")

        # Linha em branco final se houver algum import
        if import_lines and (not import_lines[-1] or import_lines[-1].strip() != ""):
            import_lines.append("")

        return import_lines