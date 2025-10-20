"""
Mapeamento de tipos PlantUML para tipos Java.
"""
from typing import Dict, Set
from .utils import to_pascal_case

class TypeMapper:
    """Mapeia tipos PlantUML para tipos Java equivalentes."""
    
    def __init__(self):
        # Mapeamento básico de tipos PlantUML para Java
        self.type_mapping: Dict[str, str] = {
            # Tipos primitivos
            "String": "String",
            "string": "String", 
            "str": "String",
            "int": "int",
            "Integer": "int",
            "long": "long",
            "Long": "long",
            "float": "float",
            "Float": "float", 
            "double": "double",
            "Double": "double",
            "bool": "boolean",
            "Boolean": "boolean",
            "boolean": "boolean",
            "char": "char",
            "Char": "char",
            "Character": "char",
            "byte": "byte",
            "Byte": "byte",
            "short": "short",
            "Short": "short",
            
            # Tipos de data/hora
            "Date": "java.util.Date",
            "DateTime": "java.time.LocalDateTime", 
            "date": "java.util.Date",
            "datetime": "java.time.LocalDateTime",
            "Time": "java.time.LocalTime",
            "TimeSpan": "java.time.Duration",
            
            # Tipos especiais
            "void": "void",
            "Object": "Object",
            "object": "Object",
            "Any": "Object",
            "None": "void",
            "null": "Object"
        }
        
        # Tipos que precisam de import statements
        self.import_requirements: Dict[str, Set[str]] = {
            "Date": {"java.util.Date"},
            "LocalDateTime": {"java.time.LocalDateTime"},
            "LocalTime": {"java.time.LocalTime"},
            "Duration": {"java.time.Duration"},
            "List": {"java.util.List"},
            "ArrayList": {"java.util.ArrayList"},
            "Set": {"java.util.Set"},
            "HashSet": {"java.util.HashSet"},
            "Map": {"java.util.Map"},
            "HashMap": {"java.util.HashMap"},
            "Queue": {"java.util.Queue"},
            "Deque": {"java.util.Deque"},
            "Stack": {"java.util.Stack"},
            "Collection": {"java.util.Collection"},
        }

    def get_java_type_hint_and_imports(self, plantuml_type: str) -> str:
        """
        Converte um tipo PlantUML para o tipo Java equivalente.
        
        Args:
            plantuml_type: O tipo conforme definido no PlantUML
            
        Returns:
            String com o tipo Java correspondente
        """
        if not plantuml_type or plantuml_type.strip() == "":
            return "Object"
        
        clean_type = plantuml_type.strip()
        
        # Se for tipo direto no mapeamento
        if clean_type in self.type_mapping:
            return self.type_mapping[clean_type]
        
        # Genérico (List<T>, Map<K,V>, etc.)
        if self._is_generic_type(clean_type):
            return self._map_generic_type(clean_type)
        
        # Arrays
        if clean_type.endswith("[]"):
            element_type = clean_type[:-2].strip()
            mapped_element = self.get_java_type_hint_and_imports(element_type)
            return f"{mapped_element}[]"
        
        # Tipo customizado (classe do usuário)
        return to_pascal_case(clean_type)
    
    def _is_generic_type(self, type_str: str) -> bool:
        return "<" in type_str and ">" in type_str
    
    def _map_generic_type(self, generic_type: str) -> str:
        import re
        match = re.match(r"(\w+)<(.+)>", generic_type.strip())
        if not match:
            return generic_type
        
        base_type = match.group(1)
        type_params = match.group(2)
        
        java_base = self._map_generic_base_type(base_type)

        if "," in type_params:
            params = [param.strip() for param in type_params.split(",")]
            mapped_params = [self.get_java_type_hint_and_imports(p) for p in params]
            return f"{java_base}<{', '.join(mapped_params)}>"
        else:
            mapped_param = self.get_java_type_hint_and_imports(type_params.strip())
            return f"{java_base}<{mapped_param}>"
    
    def _map_generic_base_type(self, base_type: str) -> str:
        generic_mapping = {
            "List": "List",
            "ArrayList": "ArrayList",
            "Array": "ArrayList",
            "Set": "Set",
            "HashSet": "HashSet",
            "Map": "Map",
            "HashMap": "HashMap", 
            "Dictionary": "Map",
            "Queue": "Queue",
            "Deque": "Deque",
            "Stack": "Stack",
            "Collection": "Collection",
        }
        return generic_mapping.get(base_type, base_type)
    
    def get_required_imports(self, plantuml_type: str) -> Set[str]:
        """
        Retorna os imports necessários para um tipo.
        
        Args:
            plantuml_type: O tipo conforme definido no PlantUML
            
        Returns:
            Set com os packages necessários
        """
        imports = set()
        
        if not plantuml_type:
            return imports
        
        clean_type = plantuml_type.strip()
        
        for type_name, required_imports in self.import_requirements.items():
            # Verifica se o tipo precisa de import
            if type_name in clean_type:
                imports.update(required_imports)
        
        # Para tipos genéricos, verifica os parâmetros também
        if self._is_generic_type(clean_type):
            import re
            match = re.match(r"(\w+)<(.+)>", clean_type)
            if match:
                base_type = match.group(1)
                params = match.group(2)
                if base_type in self.import_requirements:
                    imports.update(self.import_requirements[base_type])
                for param in [p.strip() for p in params.split(",")]:
                    imports.update(self.get_required_imports(param))
        
        # Para arrays, verifica o tipo base
        if clean_type.endswith("[]"):
            element_type = clean_type[:-2].strip()
            imports.update(self.get_required_imports(element_type))
        
        return imports