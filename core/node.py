"""
core/node.py
------------
Define a classe Node, que representa cada célula (vértice) do grafo/grid.
Armazena posição, tipo de terreno, recompensas e metadados de busca.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from core.terrain import Terrain


@dataclass
class Node:
    """
    Representa um vértice no grafo de navegação.

    Atributos principais:
        row, col   — posição no grid 2D
        terrain    — tipo de terreno (determina o custo)
        reward     — valor de recompensa coletável (0 = sem recompensa)
        is_start   — marca o ponto inicial do agente
        is_goal    — marca o objetivo final

    Atributos de busca (preenchidos pelos algoritmos):
        g_cost     — custo acumulado do início até este nó
        h_cost     — estimativa heurística até o objetivo
        parent     — nó predecessor no caminho encontrado
    """
    row: int
    col: int
    terrain: Terrain = Terrain.PLAIN
    reward: int = 0
    is_start: bool = False
    is_goal: bool = False

    # Campos de busca — resetados antes de cada execução
    g_cost: float = field(default=float('inf'), compare=False, repr=False)
    h_cost: float = field(default=0.0,          compare=False, repr=False)
    parent: Optional['Node'] = field(default=None, compare=False, repr=False)

    def __hash__(self) -> int:
        """Nós são identificados unicamente por sua posição."""
        return hash((self.row, self.col))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return False
        return self.row == other.row and self.col == other.col

    def __lt__(self, other: 'Node') -> bool:
        """Permite uso em heapq pelo custo f = g + h."""
        return self.f_cost < other.f_cost

    @property
    def f_cost(self) -> float:
        """Custo total estimado: g (real) + h (heurística)."""
        return self.g_cost + self.h_cost

    @property
    def position(self) -> tuple[int, int]:
        """Retorna a posição como tupla (row, col)."""
        return (self.row, self.col)

    @property
    def traversal_cost(self) -> int:
        """Custo de entrar neste nó (definido pelo terreno)."""
        return self.terrain.cost

    def is_walkable(self) -> bool:
        """Retorna True se o nó pode ser visitado."""
        return self.terrain.is_walkable()

    def has_reward(self) -> bool:
        """Retorna True se há uma recompensa neste nó."""
        return self.reward > 0

    def reset_search_state(self) -> None:
        """Limpa os metadados de busca para uma nova execução."""
        self.g_cost = float('inf')
        self.h_cost = 0.0
        self.parent = None

    def __repr__(self) -> str:
        marker = "S" if self.is_start else ("G" if self.is_goal else self.terrain.symbol)
        return f"Node({self.row},{self.col})[{marker}]"
