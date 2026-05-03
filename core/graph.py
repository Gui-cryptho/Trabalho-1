"""
core/graph.py
-------------
Constrói e gerencia o grafo de navegação como um grid 2D.
Responsável por gerar o mapa, definir adjacências (4 direções)
e fornecer utilitários para acesso aos nós.
"""

from __future__ import annotations
import random
from typing import List, Optional, Tuple
from core.node import Node
from core.terrain import Terrain


# Layout do mapa padrão (7×8 = 56 células, ≥ 30 vértices transitáveis)
# Legenda de caracteres:
#   '.' = Plano | '~' = Arenoso | '^' = Rochoso | '#' = Pântano
#   'X' = Parede | 'S' = Início  | 'G' = Objetivo | '$' = Recompensa
DEFAULT_MAP: List[str] = [
    "S . . X . . . ~",
    ". X . X . ^ ^ .",
    ". X . . . X . .",
    ". . ^ X $ . X G",
    "X . . . X . . .",
    ". ~ ~ . . X . .",
    ". . X . $ ~ . .",
    ". ^ . . . . ^ .",
]

_CHAR_TO_TERRAIN = {
    '.': Terrain.PLAIN,
    '~': Terrain.SANDY,
    '^': Terrain.ROCKY,
    '#': Terrain.SWAMP,
    'X': Terrain.WALL,
    'S': Terrain.PLAIN,
    'G': Terrain.PLAIN,
    '$': Terrain.PLAIN,
}

# Movimentos válidos: cima, baixo, esquerda, direita
_DIRECTIONS: List[Tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class Graph:
    """
    Grafo representado como grid 2D de Nodes.

    Responsabilidades:
        - Construir o grid a partir de uma definição de mapa
        - Calcular vizinhos válidos (4-conectividade)
        - Expor nós de início e objetivo
        - Resetar estado para novas buscas
    """

    def __init__(self) -> None:
        self.rows: int = 0
        self.cols: int = 0
        self.nodes: List[List[Node]] = []
        self.start_node: Optional[Node] = None
        self.goal_node: Optional[Node] = None
        self._reward_nodes: List[Node] = []

    # ------------------------------------------------------------------
    # Construção do grafo
    # ------------------------------------------------------------------

    def build_from_map(self, map_def: List[str] = DEFAULT_MAP) -> None:
        """
        Constrói o grafo a partir de uma lista de strings.
        Cada string representa uma linha; caracteres separados por espaço.
        """
        self.nodes = []
        self._reward_nodes = []
        self.start_node = None
        self.goal_node = None

        for r, line in enumerate(map_def):
            chars = line.split()
            row_nodes: List[Node] = []
            for c, ch in enumerate(chars):
                terrain = _CHAR_TO_TERRAIN.get(ch, Terrain.PLAIN)
                node = Node(row=r, col=c, terrain=terrain)

                if ch == 'S':
                    node.is_start = True
                    self.start_node = node
                elif ch == 'G':
                    node.is_goal = True
                    self.goal_node = node
                elif ch == '$':
                    node.reward = random.randint(5, 20)
                    self._reward_nodes.append(node)

                row_nodes.append(node)
            self.nodes.append(row_nodes)

        self.rows = len(self.nodes)
        self.cols = len(self.nodes[0]) if self.nodes else 0

        if not self.start_node or not self.goal_node:
            raise ValueError("O mapa deve conter um ponto de início 'S' e um objetivo 'G'.")

    def build_random(self, rows: int = 8, cols: int = 8,
                     wall_prob: float = 0.15,
                     reward_count: int = 4) -> None:
        """
        Gera um mapa aleatório com terrenos variados e obstáculos.
        Garante que início e objetivo sejam sempre alcançáveis.
        """
        terrains = [Terrain.PLAIN, Terrain.PLAIN, Terrain.SANDY,
                    Terrain.ROCKY, Terrain.SWAMP]

        self.nodes = []
        self._reward_nodes = []

        for r in range(rows):
            row_nodes: List[Node] = []
            for c in range(cols):
                if random.random() < wall_prob:
                    t = Terrain.WALL
                else:
                    t = random.choice(terrains)
                row_nodes.append(Node(row=r, col=c, terrain=t))
            self.nodes.append(row_nodes)

        self.rows = rows
        self.cols = cols

        # Início (canto superior-esquerdo) e objetivo (canto inferior-direito)
        self.nodes[0][0].terrain = Terrain.PLAIN
        self.nodes[0][0].is_start = True
        self.start_node = self.nodes[0][0]

        self.nodes[rows-1][cols-1].terrain = Terrain.PLAIN
        self.nodes[rows-1][cols-1].is_goal = True
        self.goal_node = self.nodes[rows-1][cols-1]

        # Distribui recompensas aleatórias em células caminháveis
        walkable = [n for row in self.nodes for n in row
                    if n.is_walkable() and not n.is_start and not n.is_goal]
        for node in random.sample(walkable, min(reward_count, len(walkable))):
            node.reward = random.randint(5, 20)
            self._reward_nodes.append(node)

    # ------------------------------------------------------------------
    # Acesso e navegação
    # ------------------------------------------------------------------

    def get_node(self, row: int, col: int) -> Optional[Node]:
        """Retorna o nó na posição (row, col) ou None se fora dos limites."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.nodes[row][col]
        return None

    def get_neighbors(self, node: Node) -> List[Node]:
        """
        Retorna os vizinhos transitáveis de um nó (4 direções).
        Paredes e células fora dos limites são excluídas.
        """
        neighbors: List[Node] = []
        for dr, dc in _DIRECTIONS:
            neighbor = self.get_node(node.row + dr, node.col + dc)
            if neighbor and neighbor.is_walkable():
                neighbors.append(neighbor)
        return neighbors

    def get_all_walkable(self) -> List[Node]:
        """Retorna todos os nós transitáveis do grafo."""
        return [n for row in self.nodes for n in row if n.is_walkable()]

    def get_reward_nodes(self) -> List[Node]:
        """Retorna os nós que contêm recompensas."""
        return [n for n in self._reward_nodes if n.has_reward()]

    # ------------------------------------------------------------------
    # Gerenciamento de estado
    # ------------------------------------------------------------------

    def reset_search_state(self) -> None:
        """Limpa os metadados de busca em todos os nós."""
        for row in self.nodes:
            for node in row:
                node.reset_search_state()

    def collect_reward(self, node: Node) -> int:
        """
        Coleta a recompensa de um nó (se houver) e retorna o valor.
        A recompensa é zerada após a coleta.
        """
        value = node.reward
        node.reward = 0
        return value

    def reset_rewards(self) -> None:
        """
        Restaura as recompensas de todos os nós (útil para reset do mapa).
        """
        for node in self._reward_nodes:
            node.reward = random.randint(5, 20)

    def vertex_count(self) -> int:
        """Retorna o número total de vértices transitáveis."""
        return len(self.get_all_walkable())

    def __repr__(self) -> str:
        lines = []
        for row in self.nodes:
            lines.append(" ".join(repr(n)[5:12] for n in row))
        return f"Graph({self.rows}×{self.cols}):\n" + "\n".join(lines)
