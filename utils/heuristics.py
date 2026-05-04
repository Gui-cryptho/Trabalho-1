# utils/heuristics.py — funcoes heuristicas para Greedy e A*
# heuristica admissivel: nunca superestima o custo real

import math
from core.node import No


def manhattan(no: No, objetivo: No) -> float:
    # distancia de Manhattan — admissivel para grids 4-direcionais
    return abs(no.linha - objetivo.linha) + abs(no.coluna - objetivo.coluna)


def euclidiana(no: No, objetivo: No) -> float:
    # distancia euclidiana em linha reta — sempre <= Manhattan, tambem admissivel
    dl = no.linha - objetivo.linha
    dc = no.coluna - objetivo.coluna
    return math.sqrt(dl * dl + dc * dc)


def chebyshev(no: No, objetivo: No) -> float:
    # distancia de Chebyshev — adequada para movimentacao 8-direcional
    return max(abs(no.linha - objetivo.linha), abs(no.coluna - objetivo.coluna))


def ajuste_recompensa(no: No, objetivo: No, peso: float = 0.5) -> float:
    # reduz a estimativa quando o no tem recompensa, incentivando coleta
    base     = manhattan(no, objetivo)
    desconto = no.recompensa * peso if no.tem_recompensa() else 0
    return max(0.0, base - desconto)


def criar_heuristica_proxima(grafo, raio: int = 2, peso: float = 0.6):
    # retorna heuristica que avalia se vale desviar para recompensas proximas
    # quanto mais perto a recompensa, maior o desconto na estimativa
    def heuristica(no: No, objetivo: No) -> float:
        base    = manhattan(no, objetivo)
        desconto = 0.0
        for dl in range(-raio, raio + 1):
            for dc in range(-raio, raio + 1):
                vizinho = grafo.obter_no(no.linha + dl, no.coluna + dc)
                if vizinho and vizinho.tem_recompensa() and vizinho.eh_transitavel():
                    distancia = abs(dl) + abs(dc)
                    if distancia == 0:
                        distancia = 1
                    desconto += (vizinho.recompensa * peso) / distancia
        return max(0.0, base - desconto)
    return heuristica


# heuristica padrao usada pelos algoritmos
HEURISTICA_PADRAO = manhattan
