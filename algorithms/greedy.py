"""
algorithms/greedy.py
---------------------
Busca Gulosa (Greedy Best-First Search).

Características:
    - Sempre expande o nó com MENOR heurística h(n) (ignora g)
    - Rápida, mas NÃO garante caminho ótimo
    - Usa fila de prioridade (min-heap) ordenada por h(n)
    - Pode falhar em encontrar o caminho ótimo ao ignorar o custo real
    - Boa para exploração rápida quando a heurística é confiável
"""

import heapq
from typing import List, Tuple, Callable, Set
from core.graph import Graph
from core.node import Node
from utils.metrics import Metrics, SearchResult
from utils.heuristics import DEFAULT_HEURISTIC


class Greedy:
    """Implementação de Busca Gulosa com heurística configurável."""

    NAME = "Greedy (Gulosa)"

    def __init__(self, graph: Graph,
                 heuristic: Callable[[Node, Node], float] = DEFAULT_HEURISTIC) -> None:
        self.graph = graph
        self.heuristic = heuristic

    def search(self, start: Node, goal: Node) -> SearchResult:
        """
        Executa Greedy do nó start até goal usando a heurística configurada.
        A fila de prioridade é ordenada exclusivamente por h(n).
        """
        self.graph.reset_search_state()
        metrics = Metrics(self.NAME)

        with metrics.measure():
            result = self._run(start, goal, metrics)

        return result

    def _run(self, start: Node, goal: Node, metrics: Metrics) -> SearchResult:
        # Calcula h do início
        start.h_cost = self.heuristic(start, goal)
        start.g_cost = 0.0

        # heap ordenado por h_cost: (h, counter, node)
        # counter serve como desempate determinístico
        counter = 0
        heap: List[Tuple[float, int, Node]] = [(start.h_cost, counter, start)]
        visited: Set[Node] = set()
        visited_order: List[Node] = []

        while heap:
            _, _, current = heapq.heappop(heap)

            if current in visited:
                continue

            visited.add(current)
            metrics.expand_node()
            visited_order.append(current)

            if current == goal:
                path, cost, reward = self._reconstruct(start, goal)
                return metrics.build_result(path, visited_order, cost, reward, found=True)

            for neighbor in self.graph.get_neighbors(current):
                if neighbor not in visited:
                    new_g = current.g_cost + neighbor.traversal_cost
                    if new_g < neighbor.g_cost:
                        neighbor.g_cost = new_g
                        neighbor.parent = current
                        neighbor.h_cost = self.heuristic(neighbor, goal)
                        counter += 1
                        heapq.heappush(heap, (neighbor.h_cost, counter, neighbor))

        return metrics.build_result([], visited_order, 0, 0, found=False)

    def _reconstruct(self, start: Node, goal: Node) -> Tuple[List[Node], float, int]:
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
