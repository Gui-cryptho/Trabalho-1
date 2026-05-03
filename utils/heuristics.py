"""
utils/heuristics.py
--------------------
Funções de heurística usadas pelos algoritmos informados (Greedy e A*).
Todas as funções recebem dois Nodes e retornam um float (estimativa de custo).

A heurística é admissível quando nunca superestima o custo real —
condição necessária para que o A* garanta a solução ótima.
"""

import math
from core.node import Node


def manhattan(node: Node, goal: Node) -> float:
    """
    Distância de Manhattan: soma das diferenças absolutas em linha e coluna.
    Admissível quando o custo mínimo de travessia é 1 (terreno Plano).
    Preferida em grids com movimentação 4-direcional.
    """
    return abs(node.row - goal.row) + abs(node.col - goal.col)


def euclidean(node: Node, goal: Node) -> float:
    """
    Distância Euclidiana: distância em linha reta.
    Sempre ≤ Manhattan, portanto também admissível.
    Útil quando há movimentação diagonal (não é o caso aqui, mas está disponível).
    """
    dr = node.row - goal.row
    dc = node.col - goal.col
    return math.sqrt(dr * dr + dc * dc)


def chebyshev(node: Node, goal: Node) -> float:
    """
    Distância de Chebyshev: max(|Δrow|, |Δcol|).
    Adequada para movimentação 8-direcional.
    """
    return max(abs(node.row - goal.row), abs(node.col - goal.col))


def reward_adjusted(node: Node, goal: Node,
                    reward_weight: float = 0.5) -> float:
    """
    Heurística com ajuste por recompensas próximas.

    Reduz a estimativa de custo quando o nó contém uma recompensa,
    incentivando o agente a desviar ligeiramente para coletá-la —
    desde que o desvio valha a pena (controlado por reward_weight).

    Parâmetros:
        reward_weight — quanto a recompensa reduz a heurística (0 a 1).
                        0 = ignora recompensas | 1 = redução máxima.
    """
    base = manhattan(node, goal)
    discount = node.reward * reward_weight if node.has_reward() else 0
    return max(0.0, base - discount)


# Heurística padrão utilizada pelos algoritmos (pode ser trocada facilmente)
DEFAULT_HEURISTIC = manhattan
