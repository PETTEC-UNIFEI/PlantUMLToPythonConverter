
"""
Mapeamento de tipos PlantUML para tipos C#.
"""
from typing import Dict, Tuple, Set
from .utils import to_pascal_case

class TypeMapper:
    """Mapeia tipos PlantUML para tipos C# equivalentes."""
    
    def __init__(self):
        # Mapeamento básico de tipos PlantUML para C#
        self.type_mapping: Dict[str, str] = {
            # Tipos primitivos
            "String": "string",
            "string": "string", 
            "str": "string",
            "int": "int",
            "Integer": "int",
            "long": "long",
            "Long": "long",
            "float": "float",
            "Float": "float", 
            "double": "double",
            "Double": "double",
            "bool": "bool",
            "Boolean": "bool",
            "boolean": "bool",
            "char": "char",
            "Char": "char",
            "Character": "char",
            "byte": "byte",
            "Byte": "byte",
            "short": "short",
            "Short": "short",
            "decimal": "decimal",
            "Decimal": "decimal",
            
            # Tipos de data/hora
            "Date": "DateTime",
            "DateTime": "DateTime", 
            "date": "DateTime",
            "datetime": "DateTime",
            "Time": "TimeSpan",
            "TimeSpan": "TimeSpan",
            
            # Tipos especiais
            "void": "void",
            "Object": "object",
            "object": "object",
            "Any": "object",
            "None": "void",
            "null": "object"
        }
        
        # Tipos que precisam de using statements
        self.using_requirements: Dict[str, Set[str]] = {
            "DateTime": {"System"},
            "TimeSpan": {"System"},
            "List": {"System.Collections.Generic"},
            "Dictionary": {"System.Collections.Generic"},
            "HashSet": {"System.Collections.Generic"},
            "Queue": {"System.Collections.Generic"},
            "Stack": {"System.Collections.Generic"},
            "IEnumerable": {"System.Collections.Generic"},
            "IList": {"System.Collections.Generic"},
            "IDictionary": {"System.Collections.Generic"}
        }

    def get_csharp_type_hint_and_imports(self, plantuml_type: str, current_namespace: str = "") -> str:
        """
        Converte um tipo PlantUML para o tipo C# equivalente.
        
        Args:
            plantuml_type: O tipo conforme definido no PlantUML
            current_namespace: O namespace atual (para resolver referências relativas)
            
        Returns:
            String com o tipo C# correspondente
        """
        if not plantuml_type or plantuml_type.strip() == "":
            return "object"
        
        # Remove espaços e normaliza
        clean_type = plantuml_type.strip()
        
        # Verifica se é um tipo direto no mapeamento
        if clean_type in self.type_mapping:
            return self.type_mapping[clean_type]
        
        # Trata tipos genéricos (List<T>, Dictionary<K,V>, etc.)
        if self._is_generic_type(clean_type):
            return self._map_generic_type(clean_type, current_namespace)
        
        # Trata arrays
        if clean_type.endswith("[]"):
            element_type = clean_type[:-2].strip()
            mapped_element = self.get_csharp_type_hint_and_imports(element_type, current_namespace)
            return f"{mapped_element}[]"
        
        # Se não encontrou mapeamento, assume que é um tipo customizado
        # e aplica PascalCase
        return to_pascal_case(clean_type)
    
    def _is_generic_type(self, type_str: str) -> bool:
        """Verifica se o tipo é genérico (contém < e >)."""
        return "<" in type_str and ">" in type_str
    
    def _map_generic_type(self, generic_type: str, current_namespace: str) -> str:
        """Mapeia tipos genéricos para C#."""
        import re
        
        # Extrai o tipo base e os parâmetros de tipo
        match = re.match(r"(\w+)<(.+)>", generic_type.strip())
        if not match:
            return generic_type
        
        base_type = match.group(1)
        type_params = match.group(2)
        
        # Mapeia o tipo base
        csharp_base = self._map_generic_base_type(base_type)
        
        # Processa os parâmetros de tipo
        if "," in type_params:
            # Múltiplos parâmetros (ex: Dictionary<K,V>)
            params = [param.strip() for param in type_params.split(",")]
            mapped_params = [self.get_csharp_type_hint_and_imports(p, current_namespace) for p in params]
            return f"{csharp_base}<{', '.join(mapped_params)}>"
        else:
            # Parâmetro único (ex: List<T>)
            mapped_param = self.get_csharp_type_hint_and_imports(type_params.strip(), current_namespace)
            return f"{csharp_base}<{mapped_param}>"
    
    def _map_generic_base_type(self, base_type: str) -> str:
        """Mapeia tipos genéricos base para C#."""
        generic_mapping = {
            "List": "List",
            "ArrayList": "List",
            "Array": "List",
            "Set": "HashSet",
            "HashSet": "HashSet",
            "Map": "Dictionary",
            "HashMap": "Dictionary", 
            "Dictionary": "Dictionary",
            "Queue": "Queue",
            "Stack": "Stack",
            "Collection": "IEnumerable"
        }
        return generic_mapping.get(base_type, base_type)
    
    def get_required_usings(self, plantuml_type: str) -> Set[str]:
        """
        Retorna os using statements necessários para um tipo.
        
        Args:
            plantuml_type: O tipo conforme definido no PlantUML
            
        Returns:
            Set com os namespaces necessários
        """
        usings = set()
        
        if not plantuml_type:
            return usings
        
        clean_type = plantuml_type.strip()
        
        # Verifica tipos que precisam de using
        for type_name, required_usings in self.using_requirements.items():
            if type_name in clean_type:
                usings.update(required_usings)
        
        return usings