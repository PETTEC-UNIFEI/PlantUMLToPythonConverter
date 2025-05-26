from typing import List, Optional
from .plantuml_atributo import PlantUMLAtributo
from .plantuml_metodo import PlantUMLMetodo

class PlantUMLEstruturaBase:
    """
    Base para estruturas como classes, enums e interfaces do PlantUML.
    """

    def __init__(self,
                 nome: str,
                 atributos: Optional[List[PlantUMLAtributo]] = None,
                 metodos: Optional[List[PlantUMLMetodo]] = None):
        """
        Inicializa uma nova instância de PlantUMLEstruturaBase.

        Args:
            nome: O nome da estrutura PlantUML.
            atributos: Uma lista opcional de objetos PlantUMLAtributo associados a esta estrutura.
                    O padrão é uma lista vazia.
            metodos: Uma lista opcional de objetos PlantUMLMetodo associados a esta estrutura.
                    O padrão é uma lista vazia.
        """
        self.nome: str = nome
        self.atributos: List[PlantUMLAtributo] = atributos if atributos is not None else []
        self.metodos: List[PlantUMLMetodo] = metodos if metodos is not None else []

    def __repr__(self) -> str:
        """Retorna uma representação em string do objeto PlantUMLEstruturaBase."""
        
        return (f"{self.__class__.__name__}(nome='{self.nome}', "
                f"atributos={len(self.atributos)}, metodos={len(self.metodos)})")