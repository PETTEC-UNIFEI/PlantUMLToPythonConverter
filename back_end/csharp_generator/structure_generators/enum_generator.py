"""
Geração do corpo de enums C# a partir de estruturas PlantUMLEnum.
"""
from typing import List, TYPE_CHECKING
import re
import unicodedata

if TYPE_CHECKING:
    from back_end.plantuml_parser.data_structures import PlantUMLEnum
    from ..type_mapper import TypeMapper
    from ..using_manager import UsingManager

class EnumGenerator:
    """Gera o corpo de uma enumeração C#."""
    
    def __init__(self, 
                 enum_structure: "PlantUMLEnum", 
                 type_mapper: "TypeMapper", 
                 using_manager: "UsingManager",
                 current_namespace: str):
        """
        Inicializa uma nova instância do EnumGenerator.

        Args:
            enum_structure: O objeto PlantUMLEnum parseado.
            type_mapper: Uma instância de TypeMapper para mapeamento de tipos.
            using_manager: Uma instância de UsingManager para gerenciar using statements.
            current_namespace: O namespace atual para resolver referências.
        """
        self.enum: "PlantUMLEnum" = enum_structure
        self.type_mapper: "TypeMapper" = type_mapper
        self.using_manager: "UsingManager" = using_manager
        self.current_namespace: str = current_namespace

    def _sanitize_name_for_csharp(self, name: str) -> str:
        """Sanitiza nome para C#."""
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

    def _to_pascal_case(self, name: str) -> str:
        """Converte nome para PascalCase."""
        name = self._sanitize_name_for_csharp(name)
        parts = re.split(r'[_\s]+', name)
        if len(parts) == 1 and name:
            parts = re.findall(r'[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])', name)
        
        capitalized_parts = [p.capitalize() for p in parts if p]
        pascal_case_name = "".join(capitalized_parts)
        
        if not pascal_case_name:
            return "_UnnamedValue"
        if pascal_case_name[0].isdigit():
            return "_" + pascal_case_name
        return pascal_case_name

    def _extract_enum_value_and_number(self, valor: str) -> tuple[str, str]:
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
                return self._to_pascal_case(name_part), value_part
            except ValueError:
                # Se não for numérico, ignora o valor
                return self._to_pascal_case(name_part), ""
        else:
            # Apenas o nome, sem valor explícito
            return self._to_pascal_case(valor), ""

    def generate_code_lines(self) -> List[str]:
        """
        Gera as linhas de código para os valores do enum C#.

        Returns:
            Uma lista de strings, cada uma representando uma linha de código
            para o corpo do enum.
        """
        lines: List[str] = []
        indent_level = 2  # Assume que já está dentro da definição do enum

        def add_line(text: str, indent_delta: int = 0):
            nonlocal indent_level
            actual_indent = indent_level + indent_delta
            if actual_indent < 0: 
                actual_indent = 0
            lines.append("    " * actual_indent + text)

        if not self.enum.valores_enum:
            # Enum vazio - adiciona um valor padrão
            add_line("None = 0")
        else:
            enum_values = []
            
            for i, valor in enumerate(self.enum.valores_enum):
                nome_sanitizado, valor_explicito = self._extract_enum_value_and_number(valor)
                
                if valor_explicito:
                    # Valor com número explícito
                    enum_values.append(f"{nome_sanitizado} = {valor_explicito}")
                else:
                    # Valor sem número - C# atribuirá automaticamente
                    enum_values.append(nome_sanitizado)
            
            # Adiciona todos os valores, exceto o último com vírgula
            for i, enum_value in enumerate(enum_values):
                if i < len(enum_values) - 1:
                    add_line(f"{enum_value},")
                else:
                    add_line(enum_value)
        
        return lines

    def get_enum_underlying_type(self) -> str:
        """
        Determina o tipo subjacente do enum C# baseado nos valores.
        
        Returns:
            String com o tipo subjacente (int, byte, long, etc.)
        """
        if not self.enum.valores_enum:
            return "int"  # Padrão
        
        max_value = 0
        min_value = 0
        
        for valor in self.enum.valores_enum:
            _, valor_explicito = self._extract_enum_value_and_number(valor)
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