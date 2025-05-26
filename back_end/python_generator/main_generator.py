"""
Módulo MainCodeGenerator (Orquestrador Principal do Gerador).

Define a classe MainCodeGenerator, que orquestra todo o processo de
geração de código Python a partir de um diagrama PlantUML parseado.
Ele gerencia a criação de diretórios e arquivos de pacotes,
e delega a geração do conteúdo específico de cada estrutura
(classe, enum, interface) para os geradores apropriados no
subpacote 'structure_generators'. Também utiliza o TypeMapper
e o ImportManager para lidar com tipos e imports.
"""
from typing import List, Set, Optional, Union, Any, Tuple, Dict, Callable, TYPE_CHECKING
import os
import re

from back_end.plantuml_parser.data_structures import (
    PlantUMLDiagrama, PlantUMLClasse, PlantUMLEnum, PlantUMLInterface, PlantUMLPacote
)
# Imports dos novos módulos dentro de python_generator
from .utils import sanitize_name_for_python_module, to_pascal_case
from .type_mapper import TypeMapper
from .import_manager import ImportManager
from .structure_generators import ClassGenerator, EnumGenerator, InterfaceGenerator


class MainCodeGenerator:
    """
    Orquestra a geração de arquivos de código Python a partir de um objeto ParsedDiagram,
    delegando a geração de conteúdo específico para sub-geradores.
    """
    def __init__(self, parsed_diagram: PlantUMLDiagrama, output_base_dir: str):
        """
        Inicializa o MainCodeGenerator.

        Args:
            parsed_diagram: O objeto PlantUMLDiagrama contendo a estrutura
                            parseada do diagrama PlantUML.
            output_base_dir: O diretório raiz onde os arquivos Python gerados
                             e a estrutura de pacotes serão criados.
        """
        # --- NOVO: cria subpasta numerada ---
        base_dir = output_base_dir
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        # Busca o maior número já usado
        existentes = [d for d in os.listdir(base_dir) if re.match(r"diagrama\d+$", d)]
        if existentes:
            maior = max([int(re.findall(r"\d+", nome)[0]) for nome in existentes])
            novo_num = maior + 1
        else:
            novo_num = 1
        self.output_base_dir = os.path.join(base_dir, f"diagrama{novo_num:02d}")
        os.makedirs(self.output_base_dir, exist_ok=True)
        # -------------------------------------
        self.parsed_diagram: PlantUMLDiagrama = parsed_diagram
        self.generated_files_manifest: List[str] = []
        
        self._all_defined_structure_names: Set[str] = self._collect_all_structure_names()
        self._structure_module_paths: dict[str, str] = self._map_structure_module_paths()

        self.type_mapper: TypeMapper = TypeMapper(self._all_defined_structure_names, self._structure_module_paths)
        self.import_manager: ImportManager = ImportManager(self._all_defined_structure_names, self._structure_module_paths)


    def _collect_all_structure_names(self) -> Set[str]:
        """
        Coleta recursivamente todos os nomes de estruturas definidas
        (classes, enums, interfaces) no diagrama.
        """
        names: Set[str] = set()
        def _collect_recursive(elements: List[Any]):
            for item in elements:
                if isinstance(item, (PlantUMLClasse, PlantUMLEnum, PlantUMLInterface)):
                    names.add(item.nome) 
                elif isinstance(item, PlantUMLPacote):
                    _collect_recursive(item.elementos)
        _collect_recursive(self.parsed_diagram.elementos)
        return names

    def _map_structure_module_paths(self) -> dict[str, str]:
        """
        Mapeia o nome original de cada estrutura para seu caminho de módulo Python
        (sanitizado e pontilhado), relativo à raiz do output_base_dir.
        Ex: 'PacotePrincipal.SubPacote.nome_da_classe_sanitizado'.
        """
        paths: dict[str, str] = {}
        def _map_recursive(elements: List[Any], current_path_parts: List[str]): # current_path_parts são nomes de pacotes sanitizados
            for item in elements:
                sanitized_item_module_name = sanitize_name_for_python_module(item.nome)
                if isinstance(item, (PlantUMLClasse, PlantUMLEnum, PlantUMLInterface)):
                    module_dot_path = ".".join(current_path_parts + [sanitized_item_module_name])
                    paths[item.nome] = module_dot_path # Chave é o nome original PlantUML
                elif isinstance(item, PlantUMLPacote):
                    _map_recursive(item.elementos, current_path_parts + [sanitized_item_module_name])
        _map_recursive(self.parsed_diagram.elementos, [])
        return paths

    def _generate_file_for_structure(self, 
                                     structure: Union[PlantUMLClasse, PlantUMLEnum, PlantUMLInterface], 
                                     current_disk_path: str, 
                                     package_dot_path_parts: List[str]):
        """
        Gera um arquivo .py para uma única estrutura (classe, enum ou interface).

        Este método coordena a coleta de imports, a geração da declaração da
        estrutura e a geração do corpo da estrutura usando geradores específicos.

        Args:
            structure: O objeto da estrutura (PlantUMLClasse, PlantUMLEnum, ou PlantUMLInterface).
            current_disk_path: O caminho no disco onde o arquivo será salvo (diretório do pacote).
            package_dot_path_parts: Lista de nomes de pacotes (sanitizados) que formam o caminho
                                     pontilhado até o diretório do módulo atual.
        """
        file_content_lines: List[str] = []
        
        python_class_name = to_pascal_case(structure.nome)
        current_file_module_name_sanitized = sanitize_name_for_python_module(structure.nome)
        current_file_module_dot_path = ".".join(package_dot_path_parts + [current_file_module_name_sanitized])

        # 1. Coletar e Adicionar Imports
        import_lines = self.import_manager.collect_imports_for_structure(
            structure, self.type_mapper, current_file_module_dot_path
        )
        file_content_lines.extend(import_lines) # Adiciona as linhas de import (já formatadas)

        # 2. Gerar Declaração da Estrutura
        parent_classes_py_hints_for_class_def: List[str] = []
        parent_type_names_plantuml: List[str] = []

        if isinstance(structure, PlantUMLClasse):
            if structure.classe_pai: parent_type_names_plantuml.append(structure.classe_pai)
            parent_type_names_plantuml.extend(structure.interfaces_implementadas or [])
        elif isinstance(structure, PlantUMLInterface):
            parent_type_names_plantuml.extend(structure.interfaces_pai or [])
        
        for p_type_name in parent_type_names_plantuml:
            if p_type_name:
                hint, _s_imp, _t_imp = self.type_mapper.get_python_type_hint_and_imports(
                    p_type_name, current_file_module_dot_path, for_heritage_list=True
                )
                parent_classes_py_hints_for_class_def.append(hint)
        
        # Adicionar ABC e Enum à lista de herança se aplicável
        has_abstract_methods = any(m.is_abstract for m in structure.metodos)
        if isinstance(structure, PlantUMLClasse) and (structure.is_abstract or has_abstract_methods):
            if "ABC" not in parent_classes_py_hints_for_class_def: parent_classes_py_hints_for_class_def.append("ABC")
        elif isinstance(structure, PlantUMLInterface):
            if "ABC" not in parent_classes_py_hints_for_class_def: parent_classes_py_hints_for_class_def.append("ABC")
        elif isinstance(structure, PlantUMLEnum):
            parent_classes_py_hints_for_class_def = ["Enum"] # Sobrescreve, Enum só herda de Enum

        parent_str = f"({', '.join(parent_classes_py_hints_for_class_def)})" if parent_classes_py_hints_for_class_def else ""
        file_content_lines.append(f"class {python_class_name}{parent_str}:")
        
        # 3. Gerar Docstring da Classe (VOCÊ ADICIONARÁ A SUA AQUI)
        file_content_lines.append(f'    """Representa a estrutura {structure.nome} do PlantUML."""')
        file_content_lines.append("") 

        # 4. Gerar Corpo da Estrutura usando sub-geradores
        body_lines: List[str] = []
        if isinstance(structure, PlantUMLEnum):
            enum_gen = EnumGenerator(structure, self.type_mapper, current_file_module_dot_path)
            body_lines.extend(enum_gen.generate_code_lines())
        elif isinstance(structure, PlantUMLInterface):
            interface_gen = InterfaceGenerator(structure, self.type_mapper, current_file_module_dot_path)
            body_lines.extend(interface_gen.generate_code_lines())
        elif isinstance(structure, PlantUMLClasse):
            class_gen = ClassGenerator(structure, self.type_mapper, current_file_module_dot_path)
            body_lines.extend(class_gen.generate_code_lines())
        
        if not body_lines : # Adicionar pass se o corpo (gerado pelos sub-geradores) estiver vazio
             # Mas EnumGenerator já adiciona pass se não tiver valores, e Class/Interface também.
             # Esta verificação pode ser redundante se os sub-geradores já garantem um 'pass'.
             # Vamos confiar que os sub-geradores colocam 'pass' se necessário.
             if isinstance(structure, PlantUMLEnum) and not structure.valores_enum and not any(attr.is_static for attr in structure.atributos):
                pass # EnumGenerator já deve ter adicionado pass
             elif isinstance(structure, (PlantUMLInterface, PlantUMLClasse)) and not structure.atributos and not structure.metodos:
                pass # Class/InterfaceGenerator já deve ter adicionado pass
        
        file_content_lines.extend(body_lines)
        file_content_lines.append("") 

        # 5. Salvar o Arquivo
        file_name = f"{sanitize_name_for_python_module(structure.nome)}.py"
        file_path = os.path.join(current_disk_path, file_name)
        
        os.makedirs(current_disk_path, exist_ok=True)
        
        final_content = "\n".join(file_content_lines)
        final_content = re.sub(r'\n\s*\n\s*$', '\n\n', final_content) 

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        self.generated_files_manifest.append(os.path.relpath(file_path, self.output_base_dir))

    def _create_package_init(self, package_disk_path: str, structure_names_in_package: Optional[List[str]] = None, sub_package_names: Optional[List[str]] = None):
        """
        Cria um arquivo __init__.py para um pacote, opcionalmente importando
        suas estruturas e subpacotes e definindo __all__.
        """
        init_file_path = os.path.join(package_disk_path, "__init__.py")
        init_content: List[str] = ["# Pacote gerado automaticamente"]
        
        structure_exports = []
        if structure_names_in_package:
            init_content.append("\n# Importando estruturas deste pacote")
            for original_name in sorted(structure_names_in_package):
                python_module_name = sanitize_name_for_python_module(original_name)
                python_class_name = to_pascal_case(original_name)
                init_content.append(f"from .{python_module_name} import {python_class_name}")
                structure_exports.append(python_class_name)
        
        sub_package_exports = []
        if sub_package_names: # Nomes já são sanitizados (nomes de diretório)
            init_content.append("\n# Importando sub-pacotes")
            for sanitized_pkg_name in sorted(sub_package_names):
                init_content.append(f"from . import {sanitized_pkg_name}")
                sub_package_exports.append(sanitized_pkg_name)

        all_exports = sorted(structure_exports + sub_package_exports)
        if all_exports:
            init_content.append("\n__all__ = [")
            for export_name in all_exports:
                init_content.append(f"    \"{export_name}\",")
            init_content.append("]")

        with open(init_file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(init_content) + "\n")
        self.generated_files_manifest.append(os.path.relpath(init_file_path, self.output_base_dir))

    def generate_files(self) -> List[str]:
        """
        Orquestra a geração de todos os arquivos Python e __init__.py
        baseado no diagrama PlantUML parseado.
        """
        os.makedirs(self.output_base_dir, exist_ok=True)
        self.generated_files_manifest = []
        # Mapeia 'caminho.do.pacote' para {'structures': [nomes_originais], 'sub_packages': [nomes_sanitizados]}
        package_content_map: Dict[str, Dict[str, List[str]]] = {"root": {"structures": [], "sub_packages": []}}

        def _organize_for_inits(elements: List[Any], current_package_key_parts: List[str]):
            current_package_key = ".".join(current_package_key_parts) if current_package_key_parts else "root"
            if current_package_key not in package_content_map:
                package_content_map[current_package_key] = {"structures": [], "sub_packages": []}

            for item in elements:
                if isinstance(item, (PlantUMLClasse, PlantUMLEnum, PlantUMLInterface)):
                    package_content_map[current_package_key]["structures"].append(item.nome)
                elif isinstance(item, PlantUMLPacote):
                    sanitized_pkg_name = sanitize_name_for_python_module(item.nome)
                    package_content_map[current_package_key]["sub_packages"].append(sanitized_pkg_name)
                    _organize_for_inits(item.elementos, current_package_key_parts + [sanitized_pkg_name])
        
        _organize_for_inits(self.parsed_diagram.elementos, [])

        def _generate_recursive(elements: List[Any], current_disk_path: str, current_package_dot_path_parts: List[str]):
            os.makedirs(current_disk_path, exist_ok=True)
            current_package_key = ".".join(current_package_dot_path_parts) if current_package_dot_path_parts else "root"
            
            structure_names_for_init = package_content_map.get(current_package_key, {}).get("structures", [])
            sub_package_names_for_init = package_content_map.get(current_package_key, {}).get("sub_packages", []) # Nomes já sanitizados
            
            self._create_package_init(current_disk_path, structure_names_for_init, sub_package_names_for_init)

            for item in elements:
                if isinstance(item, (PlantUMLClasse, PlantUMLEnum, PlantUMLInterface)):
                    self._generate_file_for_structure(item, current_disk_path, current_package_dot_path_parts)
                elif isinstance(item, PlantUMLPacote):
                    sanitized_sub_pkg_name = sanitize_name_for_python_module(item.nome)
                    new_disk_path = os.path.join(current_disk_path, sanitized_sub_pkg_name)
                    _generate_recursive(item.elementos, new_disk_path, current_package_dot_path_parts + [sanitized_sub_pkg_name])
        
        _generate_recursive(self.parsed_diagram.elementos, self.output_base_dir, [])
        
        if self.parsed_diagram.relacionamentos:
            rel_file_path = os.path.join(self.output_base_dir, "_diagram_relationships.txt")
            with open(rel_file_path, 'w', encoding='utf-8') as f:
                f.write("# Relacionamentos do Diagrama PlantUML (informativo)\n\n")
                for rel in self.parsed_diagram.relacionamentos:
                    card_o = f" ({rel.cardinalidade_origem})" if rel.cardinalidade_origem else ""
                    card_d = f" ({rel.cardinalidade_destino})" if rel.cardinalidade_destino else ""
                    lbl = f" (Label: {rel.label})" if rel.label else ""
                    f.write(f"# {rel.origem}{card_o} {rel.tipo} {rel.destino}{card_d}{lbl}\n")
            self.generated_files_manifest.append(os.path.relpath(rel_file_path, self.output_base_dir))
        
        return self.generated_files_manifest