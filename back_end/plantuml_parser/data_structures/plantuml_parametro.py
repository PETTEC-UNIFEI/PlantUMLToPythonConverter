from typing import Optional

class PlantUMLParametro:
    """Representa um parâmetro de um método em um diagrama PlantUML."""

    def __init__(self,
                 nome: str,
                 tipo: Optional[str] = None):
        self.nome: str = nome
        self.tipo: Optional[str] = tipo

    def __repr__(self) -> str:
        """Retorna uma representação em string do objeto."""
        return f"PlantUMLParametro(nome='{self.nome}', tipo='{self.tipo}')"