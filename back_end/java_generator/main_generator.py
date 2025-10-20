"""
Módulo MainJavaCodeGenerator - Orquestrador Principal do Gerador Java.
"""
import os
from typing import List, Set, Dict, Union

from back_end.plantuml_parser.data_structures import (
    PlantUMLDiagrama, PlantUMLClasse, PlantUMLEnum, PlantUMLInterface, PlantUMLPacote
)

from .type_mapper import TypeMapper
from .import_manager import ImportManager
from .structure_generators import ClassGenerator, EnumGenerator, InterfaceGenerator
from .utils import sanitize_name_for_java, to_camel_case, to_pascal_case

class MainCodeGenerator:
    """Orquestra a geração de arquivos Java a partir de um diagrama PlantUML."""

    def __init__(self, parsed_diagram: PlantUMLDiagrama, output_base_dir: str, diagram_name: str = None, base_package: str = "generatedcode"):
        # Cria subpasta numerada
        base_dir = output_base_dir
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        # Usa o nome do diagrama se fornecido, senão padrão "Diagrama"
        if diagram_name:
            base_name = sanitize_name_for_java(diagram_name)
        else:
            base_name = "Diagrama"

        nome_final = base_name
        i = 1
        while os.path.exists(os.path.join(base_dir, nome_final)):
            i += 1
            nome_final = f"{base_name}_{i}"

        self.output_base_dir = os.path.join(base_dir, nome_final)
        os.makedirs(self.output_base_dir, exist_ok=True)

        self.parsed_diagram: PlantUMLDiagrama = parsed_diagram
        self.base_package: str = base_package
        self.generated_files_manifest: List[str] = []

        self._all_defined_structure_names: Set[str] = self._collect_all_structure_names()
        self._structure_package_paths: Dict[str, str] = self._map_structure_package_paths()

        self.type_mapper: TypeMapper = TypeMapper()
        self.import_manager: ImportManager = ImportManager()

    def _collect_all_structure_names(self) -> Set[str]:
        """Coleta recursivamente todos os nomes de estruturas definidas no diagrama."""
        names: Set[str] = set()
        def collect_from_package(package: PlantUMLPacote):
            for element in package.elementos:
                if isinstance(element, PlantUMLPacote):
                    collect_from_package(element)
                else:
                    names.add(element.nome)
        def collect_from_elements(elementos):
            for element in elementos:
                if isinstance(element, PlantUMLPacote):
                    collect_from_package(element)
                else:
                    names.add(element.nome)
        collect_from_elements(self.parsed_diagram.elementos)
        return names

    def _map_structure_package_paths(self) -> Dict[str, str]:
        """Mapeia cada estrutura para seu package Java correspondente."""
        structure_packages: Dict[str, str] = {}
        def map_from_package(package: PlantUMLPacote, parent_package: str = ""):
            current_package = f"{parent_package}.{to_camel_case(package.nome)}" if parent_package else to_camel_case(package.nome)
            full_package = f"{self.base_package}.{current_package}" if current_package else self.base_package
            for element in package.elementos:
                if isinstance(element, PlantUMLPacote):
                    map_from_package(element, current_package)
                else:
                    structure_packages[element.nome] = full_package
        def map_from_elements(elementos, parent_package: str = ""):
            for element in elementos:
                if isinstance(element, PlantUMLPacote):
                    map_from_package(element, parent_package)
                else:
                    full_package = f"{self.base_package}.{parent_package}" if parent_package else self.base_package
                    structure_packages[element.nome] = full_package
        map_from_elements(self.parsed_diagram.elementos)
        return structure_packages

    def _generate_file_for_structure(self, structure: Union[PlantUMLClasse, PlantUMLEnum, PlantUMLInterface], package: str, output_dir: str):
        """Gera um arquivo Java para uma estrutura."""
        structure_name = to_pascal_case(structure.nome)
        file_path = os.path.join(output_dir, f"{structure_name}.java")

        # Coleta import statements
        imports = self.import_manager.collect_imports_for_structure(structure, package, self.type_mapper)
        import_statements = self.import_manager.format_import_statements(imports)

        # Gera o código da estrutura
        if isinstance(structure, PlantUMLClasse):
            generator = ClassGenerator(structure, self.type_mapper, self.import_manager, package)
            body_lines = generator.generate_code_lines()
            modifiers = "public"
            if getattr(structure, "is_abstract", False):
                modifiers += " abstract"
            inheritance_parts = []
            if getattr(structure, "classe_pai", None):
                inheritance_parts.append(to_pascal_case(structure.classe_pai))
            if hasattr(structure, "interfaces_implementadas"):
                inheritance_parts.extend([to_pascal_case(iface) for iface in structure.interfaces_implementadas])
            inheritance_str = ""
            if inheritance_parts:
                inheritance_str = " extends " + inheritance_parts[0]
                if len(inheritance_parts) > 1:
                    inheritance_str += " implements " + ", ".join(inheritance_parts[1:])
            class_declaration = f"{modifiers} class {structure_name}{inheritance_str}"

        elif isinstance(structure, PlantUMLEnum):
            generator = EnumGenerator(structure, self.type_mapper, self.import_manager, package)
            body_lines = generator.generate_code_lines()
            class_declaration = f"public enum {structure_name}"

        elif isinstance(structure, PlantUMLInterface):
            generator = InterfaceGenerator(structure, self.type_mapper, self.import_manager, package)
            body_lines = generator.generate_code_lines()
            inheritance_parts = []
            if hasattr(structure, "interfaces_pai") and structure.interfaces_pai:
                inheritance_parts.extend([to_pascal_case(iface) for iface in structure.interfaces_pai])
            inheritance_str = f" extends {', '.join(inheritance_parts)}" if inheritance_parts else ""
            class_declaration = f"public interface {structure_name}{inheritance_str}"

        # Escreve o arquivo
        with open(file_path, 'w', encoding='utf-8') as f:
            # Package
            f.write(f"package {package};\n\n")
            # Imports
            for import_stmt in import_statements:
                f.write(import_stmt + '\n')
            if import_statements:
                f.write('\n')
            # Declaração da estrutura
            f.write(class_declaration + " {\n")
            for line in body_lines:
                f.write("    " + line + '\n')
            f.write("}\n")

        self.generated_files_manifest.append(file_path)
        return file_path

    def _create_package_directory(self, package: PlantUMLPacote, parent_dir: str, parent_package: str = "") -> str:
        """Cria diretório para um pacote e processa suas estruturas."""
        package_name = to_camel_case(package.nome)
        package_dir = os.path.join(parent_dir, package_name)
        os.makedirs(package_dir, exist_ok=True)

        current_package = f"{parent_package}.{package_name}" if parent_package else package_name
        full_package = f"{self.base_package}.{current_package}" if current_package else self.base_package

        for element in package.elementos:
            if isinstance(element, PlantUMLPacote):
                self._create_package_directory(element, package_dir, current_package)
            else:
                self._generate_file_for_structure(element, full_package, package_dir)

        return package_dir

    def generate_files(self) -> List[str]:
        """Gera todos os arquivos Java para o diagrama."""
        def generate_from_elements(elementos, output_dir: str, parent_package: str = ""):
            for element in elementos:
                if isinstance(element, PlantUMLPacote):
                    self._create_package_directory(element, output_dir, parent_package)
                else:
                    full_package = f"{self.base_package}.{parent_package}" if parent_package else self.base_package
                    self._generate_file_for_structure(element, full_package, output_dir)

        generate_from_elements(self.parsed_diagram.elementos, self.output_base_dir)
        self._create_manifest_file()
        return self.generated_files_manifest

    def _create_manifest_file(self):
        """Cria um arquivo de manifesto (opcional) com os arquivos gerados."""
        manifest_path = os.path.join(self.output_base_dir, "generated_files.txt")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            for file_path in self.generated_files_manifest:
                f.write(file_path + '\n')
        self.generated_files_manifest.append(manifest_path)