"""
Utilitários comuns para geração de código Java.
"""
import re
import unicodedata
from typing import List

def sanitize_name_for_java(name: str) -> str:
    """
    Sanitiza nome para Java, removendo acentos e caracteres especiais.
    
    Args:
        name: Nome a ser sanitizado
        
    Returns:
        Nome sanitizado válido para Java
    """
    # Remove acentos e caracteres especiais
    name = name.replace('ç', 'c').replace('Ç', 'C')
    nfkd = unicodedata.normalize('NFKD', name)
    name = "".join([c for c in nfkd if not unicodedata.combining(c)])
    
    # Remove aspas e caracteres inválidos
    name = name.replace('"', '').replace("'", "")
    name = re.sub(r'[^0-9a-zA-Z_]', '', name)
    
    if not name:
        return "_Unnamed"
    if name[0].isdigit():
        name = "_" + name
    
    return name

def to_pascal_case(name: str) -> str:
    """
    Converte nome para PascalCase.
    
    Args:
        name: Nome a ser convertido
        
    Returns:
        Nome em PascalCase
    """
    name = sanitize_name_for_java(name)
    parts = re.split(r'[_\s]+', name)
    if len(parts) == 1 and name:
        parts = re.findall(r'[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])', name)
    
    capitalized_parts = [p.capitalize() for p in parts if p]
    pascal_case_name = "".join(capitalized_parts)
    
    if not pascal_case_name:
        return "_UnnamedItem"
    if pascal_case_name[0].isdigit():
        return "_" + pascal_case_name
    return pascal_case_name

def to_camel_case(name: str) -> str:
    """
    Converte nome para camelCase.
    
    Args:
        name: Nome a ser convertido
        
    Returns:
        Nome em camelCase
    """
    pascal_name = to_pascal_case(name)
    if pascal_name:
        return pascal_name[0].lower() + pascal_name[1:]
    return pascal_name

def get_visibility_modifier(visibilidade: str) -> str:
    """
    Converte a visibilidade PlantUML para modificador Java.
    
    Args:
        visibilidade: Símbolo de visibilidade PlantUML (+, -, #, ~)
        
    Returns:
        Modificador de visibilidade Java correspondente
    """
    visibility_map = {
        "+": "public",
        "-": "private", 
        "#": "protected",
        "~": ""  # Pacote (package-private) em Java não tem palavra reservada
    }
    return visibility_map.get(visibilidade, "public")

def extract_enum_value_and_number(valor: str) -> tuple[str, str]:
    """
    Extrai o nome e valor numérico de um valor de enum.
    
    Args:
        valor: Valor do enum (ex: "ATIVO", "INATIVO = 1", "PENDENTE = 2")
        
    Returns:
        Tupla com (nome_sanitizado, valor_numerico_ou_empty)
    """
    if "=" in valor:
        parts = valor.split("=", 1)
        name_part = parts[0].strip()
        value_part = parts[1].strip()
        try:
            int(value_part)
            return to_pascal_case(name_part), value_part
        except ValueError:
            return to_pascal_case(name_part), ""
    else:
        return to_pascal_case(valor), ""

class CodeLineBuilder:
    """
    Utilitário para construir linhas de código com indentação adequada.
    """
    def __init__(self, base_indent_level: int = 0):
        self.lines: List[str] = []
        self.base_indent_level = base_indent_level
    
    def add_line(self, text: str, indent_delta: int = 0) -> None:
        actual_indent = self.base_indent_level + indent_delta
        if actual_indent < 0: 
            actual_indent = 0
        self.lines.append("    " * actual_indent + text)
    
    def add_empty_line(self) -> None:
        self.lines.append("")
    
    def get_lines(self) -> List[str]:
        return self.lines.copy()
    
    def clear(self) -> None:
        self.lines.clear()

def format_method_signature(
    visibility: str,
    return_type: str,
    method_name: str,
    parameters: List[str],
    modifiers: List[str] = None,
    is_interface: bool = False
) -> str:
    """
    Formata uma assinatura de método Java.
    """
    all_modifiers = []
    if visibility:
        all_modifiers.append(visibility)
    if modifiers:
        all_modifiers.extend(modifiers)
    modifiers_str = " ".join([m for m in all_modifiers if m])
    if modifiers_str:
        modifiers_str += " "
    params_str = ", ".join(parameters) if parameters else ""
    # Para interface métodos, não há corpo nem modificador de visibilidade
    if is_interface:
        return f"{modifiers_str}{return_type} {method_name}({params_str});"
    else:
        return f"{modifiers_str}{return_type} {method_name}({params_str})"

def format_property_declaration(
    visibility: str,
    property_type: str,
    property_name: str,
    modifiers: List[str] = None,
    default_value: str = None,
    is_interface: bool = False
) -> str:
    """
    Formata uma declaração de propriedade Java (campo).
    """
    all_modifiers = []
    if visibility:
        all_modifiers.append(visibility)
    if modifiers:
        all_modifiers.extend(modifiers)
    modifiers_str = " ".join([m for m in all_modifiers if m])
    if modifiers_str:
        modifiers_str += " "
    if default_value is not None:
        return f"{modifiers_str}{property_type} {property_name} = {default_value};"
    else:
        return f"{modifiers_str}{property_type} {property_name};"