from typing import Optional

class PlantUMLAtributo:
    """Representa um atributo de uma classe ou interface PlantUML."""

    def __init__(self,
                 nome: str,
                 tipo: Optional[str] = None,
                 visibilidade: Optional[str] = None,
                 default_value: Optional[str] = None,
                 is_static: bool = False):
        """
        Inicializa uma nova instância de PlantUMLAtributo.

        Args:
                nome: O nome do atributo. É obrigatório.
                tipo: O tipo de dado do atributo (ex: "String", "int").
                                Opcional, o padrão é None.
                visibilidade: A visibilidade do atributo no PlantUML (ex: "+", "-", "#").
                                Opcional, o padrão é None.
                default_value: O valor padrão do atributo, se especificado.
                                Opcional, o padrão é None.
                is_static: True se o atributo for estático, False caso contrário.
                                O padrão é False.
        """
        
        self.nome: str = nome
        self.tipo: Optional[str] = tipo
        self.visibilidade: Optional[str] = visibilidade
        self.default_value: Optional[str] = default_value
        self.is_static: bool = is_static

    def __repr__(self) -> str:
        """Retorna uma representação em string oficial do objeto PlantUMLAtributo, incluindo seu valor default, se houver."""
        
        parts = [
            f"nome='{self.nome}'",
            f"tipo='{self.tipo}'",
            f"visibilidade='{self.visibilidade}'"
        ]
        if self.default_value is not None:
            parts.append(f"default='{self.default_value}'")
        if self.is_static:
            parts.append("static")
        
        return f"PlantUMLAtributo({', '.join(parts)})"