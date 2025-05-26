from typing import List
from .plantuml_pacote import PlantUMLPacote
from .plantuml_relacionamento import PlantUMLRelacionamento
from .plantuml_classe import PlantUMLClasse
from .plantuml_enum import PlantUMLEnum
from .plantuml_interface import PlantUMLInterface

class PlantUMLDiagrama:
    """Representa o diagrama PlantUML completo como uma coleção de elementos e relacionamentos."""

    def __init__(self):
        """Inicializa uma nova instância de PlantUMLDiagrama, pronta para ser populada."""
        self.elementos: List[PlantUMLClasse | PlantUMLEnum | PlantUMLInterface | PlantUMLPacote] = []
        self.relacionamentos: List[PlantUMLRelacionamento] = []

    def adicionar_elemento(self, elemento: PlantUMLClasse | PlantUMLEnum | PlantUMLInterface | PlantUMLPacote):
        """
        Adiciona um elemento estrutural (classe, enum, interface ou pacote) ao diagrama.

        Args:
            elemento: O objeto da estrutura a ser adicionado.
        """
        self.elementos.append(elemento)

    def adicionar_relacionamento(self, relacionamento: PlantUMLRelacionamento):
        """
        Adiciona um relacionamento ao diagrama.

        Args:
            relacionamento: O objeto PlantUMLRelacionamento a ser adicionado.
        """
        self.relacionamentos.append(relacionamento)

    def __repr__(self) -> str:
        """Retorna uma representação em string do objeto PlantUMLDiagrama."""
        return (f"PlantUMLDiagrama(elementos={len(self.elementos)}, "
                f"relacionamentos={len(self.relacionamentos)})")