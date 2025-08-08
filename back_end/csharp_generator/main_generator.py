"""
Módulo MainCodeGenerator para C# - Orquestrador Principal do Gerador.
"""
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
    """Orquestra a geração de arquivos C# a partir de um diagrama PlantUML."""
    
    def __init__(self, parsed_diagram: PlantUMLDiagrama, output_base_dir: str, diagram_name: str = None, base_namespace: str = "GeneratedCode"):
        # Cria subpasta numerada
        base_dir = output_base_dir
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        
        # Usa o nome do diagrama se fornecido, senão padrão "Diagrama"
        if diagram_name:
            base_name = self._sanitize_name_for_csharp(diagram_name)
        else:
            base_name = "Diagrama"
        
        # Garante unicidade: se já existe, incrementa _2, _3, ...
        nome_final = base_name
        i = 1
        while os.path.exists(os.path.join(base_dir, nome_final)):
            i += 1
            nome_final = f"{base_name}_{i}"
        
        self.output_base_dir = os.path.join(base_dir, nome_final)
        os.makedirs(self.output_base_dir, exist_ok=True)
        
        self.parsed_diagram: PlantUMLDiagrama = parsed_diagram
        self.base_namespace: str = base_namespace
        self.generated_files_manifest: List[str] = []
        
        self._all_defined_structure_names: Set[str] = self._collect_all_structure_names()
        self._structure_namespace_paths: dict[str, str] = self._map_structure_namespace_paths()

        self.type_mapper: TypeMapper = TypeMapper()
        self.using_manager: UsingManager = UsingManager()

    def _sanitize_name_for_csharp(self, name: str) -> str:
        """Sanitiza nome para C#."""
        import unicodedata
        
        # Remove acentos
        name = name.replace('ç', 'c').replace('Ç', 'C')
        nfkd = unicodedata.normalize('NFKD', name)
        name = "".join([c for c in nfkd if not unicodedata.combining(c)])
        
        # Remove caracteres especiais
        name = re.sub(r'[^0-9a-zA-Z_]', '', name)
        
        if not name:
            return "UnnamedDiagram"
        if name[0].isdigit():
            name = "_" + name
            
        return name

    def _collect_all_structure_names(self) -> Set[str]:
        """Coleta recursivamente todos os nomes de estruturas definidas no diagrama."""
        names: Set[str] = set()
        
        def collect_from_package(package: PlantUMLPacote):
            for element in package.elementos:
                if isinstance(element, PlantUMLPacote):
                    collect_from_package(element)
                else:
                    # É uma estrutura (classe, enum, interface)
                    names.add(element.nome)
        
        def collect_from_elements(elementos):
            for element in elementos:
                if isinstance(element, PlantUMLPacote):
                    collect_from_package(element)
                else:
                    # É uma estrutura (classe, enum, interface)
                    names.add(element.nome)
        
        # Coleta do diagrama principal
        collect_from_elements(self.parsed_diagram.elementos)
        
        return names

    def _map_structure_namespace_paths(self) -> Dict[str, str]:
        """Mapeia cada estrutura para seu namespace C# correspondente."""
        structure_namespaces: Dict[str, str] = {}
        
        def map_from_package(package: PlantUMLPacote, parent_namespace: str = ""):
            current_namespace = f"{parent_namespace}.{self._to_pascal_case(package.nome)}" if parent_namespace else self._to_pascal_case(package.nome)
            full_namespace = f"{self.base_namespace}.{current_namespace}" if current_namespace else self.base_namespace
            
            for element in package.elementos:
                if isinstance(element, PlantUMLPacote):
                    map_from_package(element, current_namespace)
                else:
                    # É uma estrutura (classe, enum, interface)
                    structure_namespaces[element.nome] = full_namespace
        
        def map_from_elements(elementos, parent_namespace: str = ""):
            for element in elementos:
                if isinstance(element, PlantUMLPacote):
                    map_from_package(element, parent_namespace)
                else:
                    # É uma estrutura (classe, enum, interface)
                    full_namespace = f"{self.base_namespace}.{parent_namespace}" if parent_namespace else self.base_namespace
                    structure_namespaces[element.nome] = full_namespace
        
        # Mapeia estruturas do diagrama principal
        map_from_elements(self.parsed_diagram.elementos)
        
        return structure_namespaces

    def _to_pascal_case(self, name: str) -> str:
        """Converte nome para PascalCase."""
        import unicodedata
        
        # Remove acentos
        name = name.replace('ç', 'c').replace('Ç', 'C')
        nfkd = unicodedata.normalize('NFKD', name)
        name = "".join([c for c in nfkd if not unicodedata.combining(c)])
        
        # Remove caracteres especiais
        name = re.sub(r'[^0-9a-zA-Z_\s]', '', name)
        
        # Divide por espaços, underlines, etc.
        parts = re.split(r'[_\s]+', name)
        if len(parts) == 1 and name:
            parts = re.findall(r'[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])', name)
        
        capitalized_parts = [p.capitalize() for p in parts if p]
        pascal_case_name = "".join(capitalized_parts)
        
        if not pascal_case_name:
            return "UnnamedStructure"
        if pascal_case_name[0].isdigit():
            return "_" + pascal_case_name
        return pascal_case_name

    def _generate_file_for_structure(self, structure: Union[PlantUMLClasse, PlantUMLEnum, PlantUMLInterface], namespace: str, output_dir: str):
        """Gera um arquivo C# para uma estrutura."""
        structure_name = self._to_pascal_case(structure.nome)
        file_path = os.path.join(output_dir, f"{structure_name}.cs")
        
        # Coleta using statements
        usings = self.using_manager.collect_usings_for_structure(structure, namespace, self.type_mapper)
        using_statements = self.using_manager.format_using_statements(usings)
        
        # Gera o código da estrutura
        if isinstance(structure, PlantUMLClasse):
            generator = ClassGenerator(structure, self.type_mapper, self.using_manager, namespace)
            body_lines = generator.generate_code_lines()
            
            # Determina modificadores da classe
            modifiers = ["public"]
            if structure.is_abstract:
                modifiers.append("abstract")
            
            # Determina herança
            inheritance_parts = []
            if structure.classe_pai:
                inheritance_parts.append(self._to_pascal_case(structure.classe_pai))
            inheritance_parts.extend([self._to_pascal_case(iface) for iface in structure.interfaces_implementadas])
            
            inheritance_str = f" : {', '.join(inheritance_parts)}" if inheritance_parts else ""
            
            class_declaration = f"    {' '.join(modifiers)} class {structure_name}{inheritance_str}"
            
        elif isinstance(structure, PlantUMLEnum):
            generator = EnumGenerator(structure, self.type_mapper, self.using_manager, namespace)
            body_lines = generator.generate_code_lines()
            
            # Determina o tipo subjacente do enum
            underlying_type = generator.get_enum_underlying_type()
            type_suffix = f" : {underlying_type}" if underlying_type != "int" else ""
            
            class_declaration = f"    public enum {structure_name}{type_suffix}"
            
        elif isinstance(structure, PlantUMLInterface):
            generator = InterfaceGenerator(structure, self.type_mapper, self.using_manager, namespace)
            body_lines = generator.generate_code_lines()
            
            # Determina herança de interfaces
            inheritance_parts = []
            if hasattr(structure, 'interfaces_pai') and structure.interfaces_pai:
                inheritance_parts.extend([self._to_pascal_case(iface) for iface in structure.interfaces_pai])
            
            inheritance_str = f" : {', '.join(inheritance_parts)}" if inheritance_parts else ""
            class_declaration = f"    public interface {structure_name}{inheritance_str}"
        
        # Escreve o arquivo
        with open(file_path, 'w', encoding='utf-8') as f:
            # Using statements
            for using_stmt in using_statements:
                f.write(using_stmt + '\n')
            
            if using_statements:
                f.write('\n')
            
            # Namespace
            f.write(f"namespace {namespace}\n")
            f.write("{\n")
            
            # Declaração da estrutura
            f.write(class_declaration + '\n')
            f.write("    {\n")
            
            # Corpo da estrutura
            for line in body_lines:
                f.write(line + '\n')
            
            # Fecha estrutura e namespace
            f.write("    }\n")
            f.write("}\n")
        
        self.generated_files_manifest.append(file_path)
        return file_path

    def _create_package_directory(self, package: PlantUMLPacote, parent_dir: str, parent_namespace: str = "") -> str:
        """Cria diretório para um pacote e processa suas estruturas."""
        package_name = self._to_pascal_case(package.nome)
        package_dir = os.path.join(parent_dir, package_name)
        os.makedirs(package_dir, exist_ok=True)
        
        current_namespace = f"{parent_namespace}.{package_name}" if parent_namespace else package_name
        full_namespace = f"{self.base_namespace}.{current_namespace}" if current_namespace else self.base_namespace
        
        # Processa elementos do pacote
        for element in package.elementos:
            if isinstance(element, PlantUMLPacote):
                # É um subpacote - processa recursivamente
                self._create_package_directory(element, package_dir, current_namespace)
            else:
                # É uma estrutura - gera arquivo
                self._generate_file_for_structure(element, full_namespace, package_dir)
        
        return package_dir

    def generate_files(self) -> List[str]:
        """Gera todos os arquivos C# para o diagrama."""
        
        def generate_from_elements(elementos, output_dir: str, parent_namespace: str = ""):
            for element in elementos:
                if isinstance(element, PlantUMLPacote):
                    # É um pacote - cria diretório e processa recursivamente
                    self._create_package_directory(element, output_dir, parent_namespace)
                else:
                    # É uma estrutura (classe, enum, interface)
                    full_namespace = f"{self.base_namespace}.{parent_namespace}" if parent_namespace else self.base_namespace
                    self._generate_file_for_structure(element, full_namespace, output_dir)
        
        # Gera arquivos para elementos do diagrama principal
        generate_from_elements(self.parsed_diagram.elementos, self.output_base_dir)
        
        # Cria arquivo de projeto C# se necessário
        self._create_project_file()
        
        return self.generated_files_manifest

    def _create_project_file(self):
        """Cria um arquivo .csproj básico para o projeto."""
        project_name = os.path.basename(self.output_base_dir)
        project_file_path = os.path.join(self.output_base_dir, f"{project_name}.csproj")
        
        project_content = f'''<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
  </PropertyGroup>

</Project>
'''
        
        with open(project_file_path, 'w', encoding='utf-8') as f:
            f.write(project_content)
        
        self.generated_files_manifest.append(project_file_path)