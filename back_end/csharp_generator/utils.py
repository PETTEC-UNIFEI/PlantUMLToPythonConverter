"""
Utilitários comuns para geração de código C#.
"""
import re
import unicodedata
from typing import List


def sanitize_name_for_csharp(name: str) -> str:
    """
    Sanitiza nome para C#, removendo acentos e caracteres especiais.
    
    Args:
        name: Nome a ser sanitizado
        
    Returns:
        Nome sanitizado válido para C#
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
    name = sanitize_name_for_csharp(name)
    
    # Divide por underline, espaço ou transição minúscula/maiúscula
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
    Converte a visibilidade PlantUML para modificador C#.
    
    Args:
        visibilidade: Símbolo de visibilidade PlantUML (+, -, #, ~)
        
    Returns:
        Modificador de visibilidade C# correspondente
    """
    visibility_map = {
        "+": "public",
        "-": "private", 
        "#": "protected",
        "~": "internal"
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
    # Verifica se há um valor explícito (ex: "ATIVO = 1")
    if "=" in valor:
        parts = valor.split("=", 1)
        name_part = parts[0].strip()
        value_part = parts[1].strip()
        
        # Valida se o valor é numérico
        try:
            int(value_part)
            return to_pascal_case(name_part), value_part
        except ValueError:
            # Se não for numérico, ignora o valor
            return to_pascal_case(name_part), ""
    else:
        # Apenas o nome, sem valor explícito
        return to_pascal_case(valor), ""


class CodeLineBuilder:
    """
    Utilitário para construir linhas de código com indentação adequada.
    """
    
    def __init__(self, base_indent_level: int = 0):
        """
        Inicializa o construtor de linhas.
        
        Args:
            base_indent_level: Nível base de indentação
        """
        self.lines: List[str] = []
        self.base_indent_level = base_indent_level
    
    def add_line(self, text: str, indent_delta: int = 0) -> None:
        """
        Adiciona uma linha de código com indentação.
        
        Args:
            text: Texto da linha
            indent_delta: Alteração no nível de indentação (pode ser negativo)
        """
        actual_indent = self.base_indent_level + indent_delta
        if actual_indent < 0: 
            actual_indent = 0
        self.lines.append("    " * actual_indent + text)
    
    def add_empty_line(self) -> None:
        """Adiciona uma linha vazia."""
        self.lines.append("")
    
    def get_lines(self) -> List[str]:
        """
        Retorna todas as linhas construídas.
        
        Returns:
            Lista com todas as linhas de código
        """
        return self.lines.copy()
    
    def clear(self) -> None:
        """Limpa todas as linhas construídas."""
        self.lines.clear()


def determine_enum_underlying_type(valores_enum: List[str]) -> str:
    """
    Determina o tipo subjacente do enum C# baseado nos valores.
    
    Args:
        valores_enum: Lista de valores do enum
        
    Returns:
        String com o tipo subjacente (int, byte, long, etc.)
    """
    if not valores_enum:
        return "int"  # Padrão
    
    max_value = 0
    min_value = 0
    
    for valor in valores_enum:
        _, valor_explicito = extract_enum_value_and_number(valor)
        if valor_explicito:
            try:
                num_value = int(valor_explicito)
                max_value = max(max_value, num_value)
                min_value = min(min_value, num_value)
            except ValueError:
                continue
    
    # Determina o tipo baseado no range de valores
    if min_value >= 0:
        if max_value <= 255:
            return "byte"
        elif max_value <= 65535:
            return "ushort"
        elif max_value <= 4294967295:
            return "uint"
        else:
            return "ulong"
    else:
        if min_value >= -128 and max_value <= 127:
            return "sbyte"
        elif min_value >= -32768 and max_value <= 32767:
            return "short"
        elif min_value >= -2147483648 and max_value <= 2147483647:
            return "int"
        else:
            return "long"


def format_method_signature(
    visibility: str,
    return_type: str,
    method_name: str,
    parameters: List[str],
    modifiers: List[str] = None,
    is_interface: bool = False
) -> str:
    """
    Formata uma assinatura de método C#.
    
    Args:
        visibility: Modificador de visibilidade
        return_type: Tipo de retorno
        method_name: Nome do método
        parameters: Lista de parâmetros
        modifiers: Lista de modificadores adicionais (static, abstract, etc.)
        is_interface: Se é um método de interface
        
    Returns:
        String com a assinatura formatada
    """
    all_modifiers = []
    
    if not is_interface and visibility:
        all_modifiers.append(visibility)
    
    if modifiers:
        all_modifiers.extend(modifiers)
    
    modifiers_str = " ".join(all_modifiers)
    if modifiers_str:
        modifiers_str += " "
    
    params_str = ", ".join(parameters) if parameters else ""
    
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
    Formata uma declaração de propriedade C#.
    
    Args:
        visibility: Modificador de visibilidade
        property_type: Tipo da propriedade
        property_name: Nome da propriedade
        modifiers: Lista de modificadores adicionais (static, etc.)
        default_value: Valor padrão opcional
        is_interface: Se é uma propriedade de interface
        
    Returns:
        String com a declaração formatada
    """
    all_modifiers = []
    
    if not is_interface and visibility:
        all_modifiers.append(visibility)
    
    if modifiers:
        all_modifiers.extend(modifiers)
    
    modifiers_str = " ".join(all_modifiers)
    if modifiers_str:
        modifiers_str += " "
    
    accessor_part = "{ get; set; }"
    
    if default_value is not None:
        return f"{modifiers_str}{property_type} {property_name} {accessor_part} = {default_value};"
    else:
        return f"{modifiers_str}{property_type} {property_name} {accessor_part}"
