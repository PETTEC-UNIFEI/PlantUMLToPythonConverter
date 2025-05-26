from typing import List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .plantuml_classe import PlantUMLClasse
    from .plantuml_enum import PlantUMLEnum
    from .plantuml_interface import PlantUMLInterface

TipoElementoPacote = Union[
    "PlantUMLClasse",
    "PlantUMLEnum",
    "PlantUMLInterface",
    "PlantUMLPacote"
]

class PlantUMLPacote:
    """Representa um pacote (package) definido em um diagrama PlantUML, usado para agrupar outros elementos do diagrama."""

    def __init__(self, nome: str):
        """
        Inicializa uma nova instância de PlantUMLPacote.

        Args:
            nome: O nome do pacote.
        """
        
        self.nome: str = nome
        self.elementos: List[TipoElementoPacote] = []

    def adicionar_elemento(self, elemento: TipoElementoPacote):
        """
        Adiciona um elemento (como uma classe, enum, interface ou subpacote)
        a este pacote.

        Args:
            elemento: O objeto do elemento a ser adicionado.
        """
        
        self.elementos.append(elemento)
        
    def __repr__(self) -> str:
        """Retorna uma representação em string oficial do objeto PlantUMLPacote."""
        
        return f"PlantUMLPacote(nome='{self.nome}', elementos={len(self.elementos)})"