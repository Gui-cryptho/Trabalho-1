# algorithms/greedy.py — Busca Gulosa (Greedy Best-First Search)
# expande sempre o no com menor h(n) — rapida mas nao garante otimo
# algoritmos com heuristica coletam recompensas apenas no caminho final

import heapq
from typing import List, Tuple, Callable, Set
from core.graph import Grafo
from core.node import No
from utils.metrics import Metricas, ResultadoBusca
from utils.heuristics import HEURISTICA_PADRAO


class BuscaGulosa:

    NOME = "Greedy (Gulosa)"

    def __init__(self, grafo: Grafo,
                 heuristica: Callable[[No, No], float] = HEURISTICA_PADRAO) -> None:
        self.grafo     = grafo
        self.heuristica = heuristica

    def buscar(self, inicio: No, objetivo: No) -> ResultadoBusca:
        self.grafo.resetar_estado_busca()
        metricas = Metricas(self.NOME)
        with metricas.medir():
            resultado = self._executar(inicio, objetivo, metricas)
        resultado.tempo_ms = metricas._tempo_decorrido
        return resultado

    def _executar(self, inicio: No, objetivo: No, metricas: Metricas) -> ResultadoBusca:
        inicio.custo_h = self.heuristica(inicio, objetivo)
        inicio.custo_g = 0.0

        # heap ordenado por custo_h: (h, contador, no)
        contador = 0
        fila_prioridade: List[Tuple[float, int, No]] = [(inicio.custo_h, contador, inicio)]
        visitados:        Set[No]  = set()
        ordem_visitados:  List[No] = []

        while fila_prioridade:
            _, _, atual = heapq.heappop(fila_prioridade)

            if atual in visitados:
                continue

            visitados.add(atual)
            metricas.expandir_no()
            ordem_visitados.append(atual)

            if atual == objetivo:
                caminho, custo, recompensa = self._reconstruir(inicio, objetivo)
                return metricas.construir_resultado(caminho, ordem_visitados, custo, recompensa, encontrado=True)

            for vizinho in self.grafo.obter_vizinhos(atual):
                if vizinho not in visitados:
                    novo_g = atual.custo_g + vizinho.custo_travessia
                    if novo_g < vizinho.custo_g:
                        vizinho.custo_g = novo_g
                        vizinho.pai     = atual
                        vizinho.custo_h = self.heuristica(vizinho, objetivo)
                        contador += 1
                        heapq.heappush(fila_prioridade, (vizinho.custo_h, contador, vizinho))

        return metricas.construir_resultado([], ordem_visitados, 0, 0, encontrado=False)

    def _reconstruir(self, inicio: No, objetivo: No) -> Tuple[List[No], float, int]:
        caminho:          List[No] = []
        atual:            No       = objetivo
        custo_total:      float    = 0.0
        recompensa_total: int      = 0

        while atual is not None:
            caminho.append(atual)
            custo_total      += atual.custo_travessia if atual != inicio else 0
            recompensa_total += atual.recompensa
            atual = atual.pai

        caminho.reverse()
        return caminho, custo_total, recompensa_total
