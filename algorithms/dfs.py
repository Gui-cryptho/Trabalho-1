"""
algorithms/dfs.py
------------------
Busca em Profundidade (Depth-First Search).

Características:
    - Explora um ramo até o fim antes de retroceder (LIFO)
    - NÃO garante caminho ótimo (nem em passos nem em custo)
    - Não usa heurística
    - Detecta becos sem saída naturalmente via backtracking
    - Memória mais eficiente que BFS em grafos densos
    - Complexidade: O(V + E)
"""

from typing import List, Tuple, Set
from core.graph import Graph
from core.node import Node
from utils.metrics import Metrics, SearchResult


class DFS:
    """Implementação de Busca em Profundidade (iterativa com pilha explícita)."""

    NAME = "DFS (Profundidade)"

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def search(self, start: Node, goal: Node) -> SearchResult:
        """
        Executa DFS do nó start até goal.
        Usa pilha explícita (iterativa) para evitar estouro de recursão
        em grafos grandes.
        """
        self.graph.reset_search_state()
        metrics = Metrics(self.NAME)

        with metrics.measure():
            result = self._run(start, goal, metrics)

        return result

    def _run(self, start: Node, goal: Node, metrics: Metrics) -> SearchResult:
        stack: List[Node] = [start]
        visited: Set[Node] = set()
        visited_order: List[Node] = []

        start.g_cost = 0.0

        while stack:
            current = stack.pop()

            if current in visited:
                continue

            visited.add(current)
            metrics.expand_node()
            visited_order.append(current)

            if current == goal:
                path, cost, reward = self._reconstruct(start, goal)
                return metrics.build_result(path, visited_order, cost, reward, found=True)

            # Empilha vizinhos em ordem reversa para manter ordem natural de exploração
            for neighbor in reversed(self.graph.get_neighbors(current)):
                if neighbor not in visited:
                    neighbor.parent = current
                    neighbor.g_cost = current.g_cost + neighbor.traversal_cost
                    stack.append(neighbor)

        return metrics.build_result([], visited_order, 0, 0, found=False,
                                    message="Beco sem saída — nenhum caminho encontrado.")

    def _reconstruct(self, start: Node, goal: Node) -> Tuple[List[Node], float, int]:
        """Reconstrói o caminho seguindo os ponteiros parent."""
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
