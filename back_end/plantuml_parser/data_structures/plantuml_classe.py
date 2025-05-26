from typing import List, Optional
from .plantuml_estrutura_base import PlantUMLEstruturaBase
from .plantuml_atributo import PlantUMLAtributo
from .plantuml_metodo import PlantUMLMetodo

class PlantUMLClasse(PlantUMLEstruturaBase):
    """Representa uma classe definida em um diagrama PlantUML."""

    def __init__(self,
                 nome: str,
                 atributos: Optional[List[PlantUMLAtributo]] = None,
                 metodos: Optional[List[PlantUMLMetodo]] = None,
                 classe_pai: Optional[str] = None,
                 interfaces_implementadas: Optional[List[str]] = None,
                 is_abstract: bool = False):
        """
        Inicializa um objeto PlantUMLClasse.
        
        Args:
            nome: O nome da classe. É obrigatório.
            atributos: Uma lista de objetos PlantUMLAtributo para esta classe.
                    Opcional, o padrão é uma lista vazia.
            metodos: Uma lista de objetos PlantUMLMetodo para esta classe.
                    Opcional, o padrão é uma lista vazia.
            classe_pai: O nome da classe pai da qual esta classe herda.
                    Opcional, o padrão é None.
            interfaces_implementadas: Uma lista de nomes de interfaces que esta classe implementa.
            O       pcional, o padrão é uma lista vazia.
            is_abstract: True se a classe for abstrata, False caso contrário.
                    O padrão é False.
        """
        
        super().__init__(nome, atributos, metodos)
        self.classe_pai: Optional[str] = classe_pai
        self.interfaces_implementadas: List[str] = interfaces_implementadas if interfaces_implementadas is not None else []
        self.is_abstract: bool = is_abstract
        

    def __repr__(self) -> str:
        """Retorna uma representação em string do objeto PlantUMLClasse."""
        
        base_repr = super().__repr__()
        abstract_modifier = " abstract" if self.is_abstract else ""
        return (f"{base_repr[:-1]}, pai='{self.classe_pai}', "
                f"interfaces={self.interfaces_implementadas}{abstract_modifier})")