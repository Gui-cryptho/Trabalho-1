"""
core/terrain.py
---------------
Define os tipos de terreno do ambiente, seus custos de travessia
e as propriedades visuais (cor) usadas na interface gráfica.
"""

from enum import Enum
from dataclasses import dataclass


@dataclass(frozen=True)
class TerrainProperties:
    """Propriedades imutáveis de um tipo de terreno."""
    name: str
    cost: int          # custo de travessia
    color: str         # cor hexadecimal para a GUI
    symbol: str        # símbolo para representação textual


class Terrain(Enum):
    """
    Enumeração dos tipos de terreno disponíveis no ambiente.
    Cada valor carrega suas propriedades completas.
    """
    PLAIN   = TerrainProperties("Plano",   cost=1,  color="#A8D5A2", symbol=".")
    SANDY   = TerrainProperties("Arenoso", cost=4,  color="#F5DEB3", symbol="~")
    ROCKY   = TerrainProperties("Rochoso", cost=10, color="#A0A0A0", symbol="^")
    SWAMP   = TerrainProperties("Pântano", cost=20, color="#6B8E6B", symbol="#")
    WALL    = TerrainProperties("Parede",  cost=-1, color="#2C2C2C", symbol="X")  # intransponível

    @property
    def cost(self) -> int:
        return self.value.cost

    @property
    def color(self) -> str:
        return self.value.color

    @property
    def symbol(self) -> str:
        return self.value.symbol

    @property
    def label(self) -> str:
        return self.value.name

    def is_walkable(self) -> bool:
        """Retorna True se o terreno pode ser atravessado."""
        return self.cost > 0


# Paleta de cores complementares para elementos especiais do mapa
ELEMENT_COLORS = {
    "agent":   "#FF6B35",   # agente (laranja vibrante)
    "goal":    "#FFD700",   # objetivo/prêmio (dourado)
    "reward":  "#00CED1",   # recompensas intermediárias (turquesa)
    "path":    "#FF69B4",   # caminho encontrado (rosa)
    "visited": "#DDA0DD",   # nós visitados/explorados (lilás)
    "start":   "#FF6B35",   # ponto de partida
}
