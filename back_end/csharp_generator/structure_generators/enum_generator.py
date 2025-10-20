"""
Geração do corpo de enums C# a partir de estruturas PlantUMLEnum.
"""
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from back_end.plantuml_parser.data_structures import PlantUMLEnum
    from ..type_mapper import TypeMapper
    from ..using_manager import UsingManager

from ..utils import (
    to_pascal_case, extract_enum_value_and_number, 
    CodeLineBuilder, determine_enum_underlying_type
)

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

    def generate_code_lines(self) -> List[str]:
        """
        Gera as linhas de código para os valores do enum C#.

        Returns:
            Uma lista de strings, cada uma representando uma linha de código
            para o corpo do enum.
        """
        builder = CodeLineBuilder(2)  # Dentro do enum

        if not self.enum.valores_enum:
            # Enum vazio - adiciona um valor padrão
            builder.add_line("None = 0")
        else:
            enum_values = []
            
            for i, valor in enumerate(self.enum.valores_enum):
                nome_sanitizado, valor_explicito = extract_enum_value_and_number(valor)
                
                if valor_explicito:
                    # Valor com número explícito
                    enum_values.append(f"{nome_sanitizado} = {valor_explicito}")
                else:
                    # Valor sem número - C# atribuirá automaticamente
                    enum_values.append(nome_sanitizado)
            
            # Adiciona todos os valores, exceto o último com vírgula
            for i, enum_value in enumerate(enum_values):
                if i < len(enum_values) - 1:
                    builder.add_line(f"{enum_value},")
                else:
                    builder.add_line(enum_value)
        
        return builder.get_lines()

    def get_enum_underlying_type(self) -> str:
        """
        Determina o tipo subjacente do enum C# baseado nos valores.
        
        Returns:
            String com o tipo subjacente (int, byte, long, etc.)
        """
        return determine_enum_underlying_type(self.enum.valores_enum)