from typing import Optional

class PlantUMLRelacionamento:
    """Representa um relacionamento (como herança, associação, composição)
    entre duas estruturas em um diagrama PlantUML."""

    def __init__(self,
                 origem: str,
                 destino: str,
                 tipo: str,
                 label: Optional[str] = None,
                 cardinalidade_origem: Optional[str] = None,
                 cardinalidade_destino: Optional[str] = None):
        """
        Inicializa uma nova instância de PlantUMLRelacionamento.

        Args:
                origem: O nome da estrutura de origem do relacionamento.
                destino: O nome da estrutura de destino do relacionamento.
                tipo: Uma string descrevendo o tipo de relacionamento
                        (ex: "heranca", "associacao", "composicao", "agregacao", "dependencia", "implementacao").
                abel: O rótulo textual do relacionamento. Opcional.
                cardinalidade_origem: A cardinalidade na ponta de origem.
                        Opcional.
                cardinalidade_destino: A cardinalidade na ponta de destino.
                        Opcional.
        """
        
        self.origem: str = origem
        self.destino: str = destino
        self.tipo: str = tipo
        self.label: Optional[str] = label
        self.cardinalidade_origem: Optional[str] = cardinalidade_origem
        self.cardinalidade_destino: Optional[str] = cardinalidade_destino

    def __repr__(self) -> str:
        """Retorna uma representação em string oficial do objeto PlantUMLRelacionamento,
        incluindo cardinalidades se presentes."""
        
        parts = [
            f"origem='{self.origem}'"
        ]
        if self.cardinalidade_origem:
            parts.append(f"card_origem='{self.cardinalidade_origem}'")
        
        parts.append(f"destino='{self.destino}'")
        
        if self.cardinalidade_destino:
            parts.append(f"card_destino='{self.cardinalidade_destino}'")
            
        parts.append(f"tipo='{self.tipo}'")
        
        if self.label:
            parts.append(f"label='{self.label}'")
            
        return f"PlantUMLRelacionamento({', '.join(parts)})"