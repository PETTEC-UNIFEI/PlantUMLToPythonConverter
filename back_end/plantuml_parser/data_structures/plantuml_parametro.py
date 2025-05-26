from typing import Optional

class PlantUMLParametro:
    """Representa um parâmetro de um método em um diagrama PlantUML."""

    def __init__(self,
                 nome: str,
                 tipo: Optional[str] = None):
        """
        Inicializa uma nova instância de PlantUMLParametro.

        Args:
            nome: O nome do parâmetro.
            tipo: O tipo de dado do parâmetro. Opcional,
                  o padrão é None.
        """
        
        self.nome: str = nome
        self.tipo: Optional[str] = tipo

    def __repr__(self) -> str:
        """Retorna uma representação em string oficial do objeto PlantUMLParametro."""
        
        return f"PlantUMLParametro(nome='{self.nome}', tipo='{self.tipo}')"