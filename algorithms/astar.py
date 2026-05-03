"""
algorithms/astar.py
--------------------
Algoritmo A* (A estrela).

Características:
    - Expande o nó com menor f(n) = g(n) + h(n)
    - Garante o caminho ÓTIMO quando a heurística é admissível
    - Combina o melhor do Dijkstra (custo real) com o Greedy (guia heurístico)
    - Usa heurística com ajuste por recompensas próximas (opcional)
    - Complexidade: O(E log V) com heap binário
"""

import heapq
from typing import List, Tuple, Callable, Set
from core.graph import Graph
from core.node import Node
from utils.metrics import Metrics, SearchResult
from utils.heuristics import DEFAULT_HEURISTIC


class AStar:
    """
    Implementação do A* com heurística configurável e suporte a recompensas.
    """

    NAME = "A* (A estrela)"

    def __init__(self, graph: Graph,
                 heuristic: Callable[[Node, Node], float] = DEFAULT_HEURISTIC) -> None:
        self.graph = graph
        self.heuristic = heuristic

    def search(self, start: Node, goal: Node) -> SearchResult:
        """
        Executa A* do nó start até goal.
        Ordena a fila por f(n) = g(n) + h(n).
        """
        self.graph.reset_search_state()
        metrics = Metrics(self.NAME)

        with metrics.measure():
            result = self._run(start, goal, metrics)

        return result

    def _run(self, start: Node, goal: Node, metrics: Metrics) -> SearchResult:
        start.g_cost = 0.0
        start.h_cost = self.heuristic(start, goal)

        counter = 0
        # heap: (f_cost, counter, node)
        heap: List[Tuple[float, int, Node]] = [(start.f_cost, counter, start)]

        # open_set rastreia nós ainda na fila com seus g_costs
        open_set: dict[Node, float] = {start: start.g_cost}
        closed_set: Set[Node] = set()
        visited_order: List[Node] = []

        while heap:
            _, _, current = heapq.heappop(heap)

            # Descarta entradas desatualizadas (lazy deletion)
            if current in closed_set:
                continue
            if current in open_set and open_set[current] < current.g_cost:
                continue

            closed_set.add(current)
            metrics.expand_node()
            visited_order.append(current)

            if current == goal:
                path, cost, reward = self._reconstruct(start, goal)
                return metrics.build_result(path, visited_order, cost, reward, found=True)

            for neighbor in self.graph.get_neighbors(current):
                if neighbor in closed_set:
                    continue

                tentative_g = current.g_cost + neighbor.traversal_cost

                # Atualiza se encontramos um caminho melhor até este vizinho
                if tentative_g < neighbor.g_cost:
                    neighbor.g_cost = tentative_g
                    neighbor.h_cost = self.heuristic(neighbor, goal)
                    neighbor.parent = current
                    open_set[neighbor] = tentative_g
                    counter += 1
                    heapq.heappush(heap, (neighbor.f_cost, counter, neighbor))

        return metrics.build_result([], visited_order, 0, 0, found=False,
                                    message="Nenhum caminho encontrado — verifique os obstáculos.")

    def _reconstruct(self, start: Node, goal: Node) -> Tuple[List[Node], float, int]:
        """Reconstrói o caminho ótimo a partir dos ponteiros parent."""
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
