# algorithms/astar.py — A* (A estrela)
# expande o no com menor f(n) = g(n) + h(n)
# garante caminho otimo quando a heuristica e admissivel

import heapq
from typing import List, Tuple, Callable, Set
from core.graph import Grafo
from core.node import No
from utils.metrics import Metricas, ResultadoBusca
from utils.heuristics import HEURISTICA_PADRAO


class BuscaAEstrela:

    NOME = "A* (A estrela)"

    def __init__(self, grafo: Grafo,
                 heuristica: Callable[[No, No], float] = HEURISTICA_PADRAO) -> None:
        self.grafo      = grafo
        self.heuristica = heuristica

    def buscar(self, inicio: No, objetivo: No) -> ResultadoBusca:
        self.grafo.resetar_estado_busca()
        metricas = Metricas(self.NOME)
        with metricas.medir():
            resultado = self._executar(inicio, objetivo, metricas)
        resultado.tempo_ms = metricas._tempo_decorrido
        return resultado

    def _executar(self, inicio: No, objetivo: No, metricas: Metricas) -> ResultadoBusca:
        inicio.custo_g = 0.0
        inicio.custo_h = self.heuristica(inicio, objetivo)

        contador = 0
        # heap: (custo_f, contador, no)
        fila_prioridade: List[Tuple[float, int, No]] = [(inicio.custo_f, contador, inicio)]

        # conjunto_aberto rastreia nos na fila com seus custo_g
        conjunto_aberto: dict[No, float] = {inicio: inicio.custo_g}
        conjunto_fechado: Set[No]        = set()
        ordem_visitados:  List[No]       = []

        while fila_prioridade:
            _, _, atual = heapq.heappop(fila_prioridade)

            # descarta entradas desatualizadas (lazy deletion)
            if atual in conjunto_fechado:
                continue
            if atual in conjunto_aberto and conjunto_aberto[atual] < atual.custo_g:
                continue

            conjunto_fechado.add(atual)
            metricas.expandir_no()
            ordem_visitados.append(atual)

            if atual == objetivo:
                caminho, custo, recompensa = self._reconstruir(inicio, objetivo)
                return metricas.construir_resultado(caminho, ordem_visitados, custo, recompensa, encontrado=True)

            for vizinho in self.grafo.obter_vizinhos(atual):
                if vizinho in conjunto_fechado:
                    continue

                tentativa_g = atual.custo_g + vizinho.custo_travessia

                # atualiza se encontramos caminho melhor ate este vizinho
                if tentativa_g < vizinho.custo_g:
                    vizinho.custo_g = tentativa_g
                    vizinho.custo_h = self.heuristica(vizinho, objetivo)
                    vizinho.pai     = atual
                    conjunto_aberto[vizinho] = tentativa_g
                    contador += 1
                    heapq.heappush(fila_prioridade, (vizinho.custo_f, contador, vizinho))

        return metricas.construir_resultado([], ordem_visitados, 0, 0, encontrado=False,
                                            mensagem="Nenhum caminho encontrado — verifique os obstaculos.")

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
