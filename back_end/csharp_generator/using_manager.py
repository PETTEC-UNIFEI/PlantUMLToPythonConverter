"""
Gerenciamento de using statements para código C#.
"""
from typing import Set, List, Optional, Union, TYPE_CHECKING, Any as TypingAny
import os 

from back_end.plantuml_parser import data_structures
from back_end.plantuml_parser.data_structures import PlantUMLClasse, PlantUMLEnum, PlantUMLInterface
from .utils import to_pascal_case

class UsingManager:
    """Gerencia using statements para arquivos C#."""
    
    def __init__(self):
        # Using statements padrão que sempre devem ser incluídos
        self.default_usings: Set[str] = {
            "System"
        }
        
        # Cache de using statements calculados
        self._using_cache: dict = {}
    
    def calculate_relative_using_path(self, from_namespace: str, to_namespace: str) -> Optional[str]:
        """
        Calcula o caminho relativo para um using statement.
        
        Args:
            from_namespace: Namespace de origem
            to_namespace: Namespace de destino
            
        Returns:
            String com o namespace relativo ou None se não for necessário
        """
        if not to_namespace or from_namespace == to_namespace:
            return None
        
        # Em C#, geralmente usamos o namespace completo
        return to_namespace
    
    def collect_usings_for_structure(self, structure: Union[PlantUMLClasse, PlantUMLEnum, PlantUMLInterface], 
                                   current_namespace: str, type_mapper) -> Set[str]:
        """
        Coleta todos os using statements necessários para uma estrutura.
        
        Args:
            structure: A estrutura PlantUML (classe, enum ou interface)
            current_namespace: O namespace atual
            type_mapper: O mapeador de tipos para obter using requirements
            
        Returns:
            Set com todos os using statements necessários
        """
        usings: Set[str] = set(self.default_usings)
        
        if isinstance(structure, PlantUMLClasse):
            usings.update(self._collect_usings_for_classe(structure, current_namespace, type_mapper))
        elif isinstance(structure, PlantUMLEnum):
            usings.update(self._collect_usings_for_enum(structure, current_namespace, type_mapper))
        elif isinstance(structure, PlantUMLInterface):
            usings.update(self._collect_usings_for_interface(structure, current_namespace, type_mapper))
        
        # Remove o namespace atual dos usings
        usings.discard(current_namespace)
        
        return usings
    
    def _collect_usings_for_classe(self, classe: PlantUMLClasse, current_namespace: str, type_mapper) -> Set[str]:
        """Coleta using statements específicos para uma classe."""
        usings: Set[str] = set()
        
        # Using para classe pai
        if classe.classe_pai:
            parent_usings = type_mapper.get_required_usings(classe.classe_pai)
            usings.update(parent_usings)
        
        # Using para interfaces implementadas
        for interface in classe.interfaces_implementadas:
            interface_usings = type_mapper.get_required_usings(interface)
            usings.update(interface_usings)
        
        # Using para atributos
        for atributo in classe.atributos:
            if atributo.tipo:
                attr_usings = type_mapper.get_required_usings(atributo.tipo)
                usings.update(attr_usings)
        
        # Using para métodos
        for metodo in classe.metodos:
            # Tipo de retorno
            if metodo.tipo_retorno:
                return_usings = type_mapper.get_required_usings(metodo.tipo_retorno)
                usings.update(return_usings)
            
            # Parâmetros
            for parametro in metodo.parametros:
                if parametro.tipo:
                    param_usings = type_mapper.get_required_usings(parametro.tipo)
                    usings.update(param_usings)
        
        # Adiciona using para NotImplementedException se há métodos
        if classe.metodos:
            usings.add("System")
        
        return usings
    
    def _collect_usings_for_enum(self, enum: PlantUMLEnum, current_namespace: str, type_mapper) -> Set[str]:
        """Coleta using statements específicos para um enum."""
        usings: Set[str] = set()
        
        # Enums em C# geralmente não precisam de usings adicionais além do System
        # mas podemos adicionar lógica específica se necessário
        
        return usings
    
    def _collect_usings_for_interface(self, interface: PlantUMLInterface, current_namespace: str, type_mapper) -> Set[str]:
        """Coleta using statements específicos para uma interface."""
        usings: Set[str] = set()
        
        # Using para interfaces pai
        for parent_interface in getattr(interface, 'interfaces_pai', []):
            parent_usings = type_mapper.get_required_usings(parent_interface)
            usings.update(parent_usings)
        
        # Using para métodos da interface
        for metodo in interface.metodos:
            # Tipo de retorno
            if metodo.tipo_retorno:
                return_usings = type_mapper.get_required_usings(metodo.tipo_retorno)
                usings.update(return_usings)
            
            # Parâmetros
            for parametro in metodo.parametros:
                if parametro.tipo:
                    param_usings = type_mapper.get_required_usings(parametro.tipo)
                    usings.update(param_usings)
        
        return usings
    
    def format_using_statements(self, usings: Set[str]) -> List[str]:
        """
        Formata os using statements para inclusão no arquivo C#.
        
        Args:
            usings: Set com os namespaces
            
        Returns:
            Lista de strings formatadas com os using statements
        """
        if not usings:
            return []
        
        # Ordena os usings alfabeticamente
        sorted_usings = sorted(usings)
        
        # Formata como using statements
        using_lines = []
        for using_namespace in sorted_usings:
            if using_namespace:  # Ignora strings vazias
                using_lines.append(f"using {using_namespace};")
        
        return using_lines
    
    def get_namespace_from_file_path(self, file_path: str, base_namespace: str = "") -> str:
        """
        Calcula o namespace baseado no caminho do arquivo.
        
        Args:
            file_path: Caminho do arquivo
            base_namespace: Namespace base do projeto
            
        Returns:
            Namespace calculado
        """
        # Remove extensão e normaliza o caminho
        path_without_ext = os.path.splitext(file_path)[0]
        path_parts = path_without_ext.replace('\\', '/').split('/')
        
        # Remove partes vazias e converte para PascalCase
        namespace_parts = []
        if base_namespace:
            namespace_parts.append(base_namespace)
        
        for part in path_parts:
            if part and part not in ['.', '..']:
                # Converte para PascalCase
                pascal_part = to_pascal_case(part)
                if pascal_part:
                    namespace_parts.append(pascal_part)
        
        return '.'.join(namespace_parts) if namespace_parts else "DefaultNamespace"