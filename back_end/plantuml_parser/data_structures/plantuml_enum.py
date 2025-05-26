from typing import List, Optional
from .plantuml_estrutura_base import PlantUMLEstruturaBase
from .plantuml_atributo import PlantUMLAtributo

class PlantUMLEnum(PlantUMLEstruturaBase):
    """Representa uma enumeração (enum) definida em um diagrama PlantUML."""

    def __init__(self,
                 nome: str,
                 valores_enum: Optional[List[str]] = None):
        """
        Inicializa uma nova instância de PlantUMLEnum.

        Args:
            nome: O nome da enumeração.
            valores_enum: Uma lista de strings representando os valores constantes do enum. 
                    Opcional, o padrão é uma lista vazia.
        """
        
        atributos_enum = []
        if valores_enum:
            for valor in valores_enum:
                atributos_enum.append(PlantUMLAtributo(nome=valor))
        
        super().__init__(nome, atributos=atributos_enum, metodos=None)
        self.valores_enum : List[str] = valores_enum if valores_enum is not None else []

    def __repr__(self) -> str:
        """Retorna uma representação em string oficial do objeto PlantUMLEnum."""
        
        return f"PlantUMLEnum(nome='{self.nome}', valores={self.valores_enum})"