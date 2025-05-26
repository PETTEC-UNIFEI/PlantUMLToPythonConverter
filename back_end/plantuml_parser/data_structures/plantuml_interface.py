from typing import List, Optional
from .plantuml_estrutura_base import PlantUMLEstruturaBase
from .plantuml_metodo import PlantUMLMetodo
from .plantuml_atributo import PlantUMLAtributo

class PlantUMLInterface(PlantUMLEstruturaBase):
    """Representa uma interface definida em um diagrama PlantUML."""

    def __init__(self,
                 nome: str,
                 atributos: Optional[List[PlantUMLAtributo]] = None,
                 metodos: Optional[List[PlantUMLMetodo]] = None,
                 interfaces_pai: Optional[List[str]] = None):
        """
        Inicializa uma nova instância de PlantUMLInterface.

        Args:
            nome: O nome da interface.
            atributos: Uma lista opcional de objetos PlantUMLAtributo (geralmente constantes) para esta interface.
                    O padrão é uma lista vazia.
            metodos: Uma lista opcional de objetos PlantUMLMetodo (geralmente abstratos) para esta interface.
                    O padrão é uma lista vazia.
            interfaces_pai: Uma lista opcional de nomes de interfaces das quais esta interface herda.
                    O padrão é uma lista vazia.
        """
        
        super().__init__(nome, atributos, metodos)
        self.interfaces_pai: List[str] = interfaces_pai if interfaces_pai is not None else []

    def __repr__(self) -> str:
        """Retorna uma representação em string do objeto PlantUMLInterface."""
        
        base_repr = super().__repr__()
        return f"{base_repr[:-1]}, pais='{self.interfaces_pai}')"