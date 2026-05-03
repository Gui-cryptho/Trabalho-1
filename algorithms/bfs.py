"""
algorithms/bfs.py
------------------
Busca em Largura (Breadth-First Search).

Características:
    - Explora nós camada por camada (FIFO)
    - Garante o caminho com MENOR NÚMERO DE PASSOS (não necessariamente menor custo)
    - Não usa heurística
    - Completo: sempre encontra a solução se ela existir
    - Complexidade: O(V + E)
"""

from collections import deque
from typing import List, Tuple
from core.graph import Graph
from core.node import Node
from utils.metrics import Metrics, SearchResult


class BFS:
    """Implementação de Busca em Largura."""

    NAME = "BFS (Largura)"

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def search(self, start: Node, goal: Node) -> SearchResult:
        """
        Executa BFS do nó start até goal.

        Retorna SearchResult com o caminho, custo, recompensas e métricas.
        """
        self.graph.reset_search_state()
        metrics = Metrics(self.NAME)

        with metrics.measure():
            result = self._run(start, goal, metrics)

        return result

    def _run(self, start: Node, goal: Node, metrics: Metrics) -> SearchResult:
        queue: deque[Node] = deque([start])
        visited: set[Node] = {start}
        visited_order: List[Node] = []

        start.g_cost = 0.0

        while queue:
            current = queue.popleft()
            metrics.expand_node()
            visited_order.append(current)

            if current == goal:
                path, cost, reward = self._reconstruct(start, goal)
                return metrics.build_result(path, visited_order, cost, reward, found=True)

            for neighbor in self.graph.get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    neighbor.parent = current
                    neighbor.g_cost = current.g_cost + neighbor.traversal_cost
                    queue.append(neighbor)

        return metrics.build_result([], visited_order, 0, 0, found=False)

    def _reconstruct(self, start: Node, goal: Node) -> Tuple[List[Node], float, int]:
        """Reconstrói o caminho seguindo os ponteiros parent do objetivo até o início."""
        path: List[Node] = []
        current: Node = goal
        total_cost: float = 0.0
        total_reward: int = 0

        while current is not None:
            path.append(current)
            total_cost += current.traversal_cost if current != start else 0
            total_reward += current.reward
            current = current.parent

        path.reverse()
        return path, total_cost, total_reward
