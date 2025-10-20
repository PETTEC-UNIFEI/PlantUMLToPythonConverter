"""
Geração do corpo de enums Java a partir de estruturas PlantUMLEnum.
"""
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from back_end.plantuml_parser.data_structures import PlantUMLEnum
    from ..type_mapper import TypeMapper
    from ..import_manager import ImportManager

from ..utils import (
    to_pascal_case, extract_enum_value_and_number, CodeLineBuilder
)

class EnumGenerator:
    """Gera o corpo de uma enumeração Java."""

    def __init__(self,
                 enum_structure: "PlantUMLEnum",
                 type_mapper: "TypeMapper",
                 import_manager: "ImportManager",
                 current_package: str):
        """
        Inicializa uma nova instância do EnumGenerator.

        Args:
            enum_structure: O objeto PlantUMLEnum parseado.
            type_mapper: Uma instância de TypeMapper para mapeamento de tipos.
            import_manager: Uma instância de ImportManager para gerenciar imports.
            current_package: O package atual para resolver referências.
        """
        self.enum: "PlantUMLEnum" = enum_structure
        self.type_mapper: "TypeMapper" = type_mapper
        self.import_manager: "ImportManager" = import_manager
        self.current_package: str = current_package

    def generate_code_lines(self) -> List[str]:
        """
        Gera as linhas de código para os valores do enum Java.

        Returns:
            Uma lista de strings, cada uma representando uma linha de código
            para o corpo do enum.
        """
        builder = CodeLineBuilder(1)  # Dentro do enum

        if not self.enum.valores_enum:
            # Enum vazio - adiciona um valor padrão
            builder.add_line("NONE")
        else:
            enum_values = []
            for valor in self.enum.valores_enum:
                nome_sanitizado, valor_explicito = extract_enum_value_and_number(valor)
                # Em Java, enum não tem valor explícito por padrão, mas pode ser usado com campos extras
                enum_values.append(nome_sanitizado)

            # Adiciona todos os valores separados por vírgula
            for i, enum_value in enumerate(enum_values):
                if i < len(enum_values) - 1:
                    builder.add_line(f"{enum_value},")
                else:
                    builder.add_line(f"{enum_value};")  # Último termina com ponto e vírgula

        return builder.get_lines()