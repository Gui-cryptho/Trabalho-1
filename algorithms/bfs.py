# algorithms/bfs.py — Busca em Largura (BFS)
# explora nos camada por camada (FIFO), garante menor numero de passos
# busca cega: coleta recompensas de todos os nos visitados durante exploracao

from collections import deque
from typing import List, Tuple
from core.graph import Grafo
from core.node import No
from utils.metrics import Metricas, ResultadoBusca


class BuscaLargura:

    NOME = "BFS (Largura)"

    def __init__(self, grafo: Grafo) -> None:
        self.grafo = grafo

    def buscar(self, inicio: No, objetivo: No) -> ResultadoBusca:
        self.grafo.resetar_estado_busca()
        metricas = Metricas(self.NOME)
        with metricas.medir():
            resultado = self._executar(inicio, objetivo, metricas)
        resultado.tempo_ms = metricas._tempo_decorrido
        return resultado

    def _executar(self, inicio: No, objetivo: No, metricas: Metricas) -> ResultadoBusca:
        fila:           deque[No] = deque([inicio])
        visitados:      set[No]   = {inicio}
        ordem_visitados: List[No] = []
        recompensa_total: int     = 0

        inicio.custo_g = 0.0

        while fila:
            atual = fila.popleft()
            metricas.expandir_no()
            ordem_visitados.append(atual)

            # busca cega coleta recompensa de qualquer no visitado
            if atual.tem_recompensa():
                recompensa_total += atual.recompensa

            if atual == objetivo:
                caminho, custo = self._reconstruir(inicio, objetivo)
                return metricas.construir_resultado(caminho, ordem_visitados, custo, recompensa_total, encontrado=True)

            for vizinho in self.grafo.obter_vizinhos(atual):
                if vizinho not in visitados:
                    visitados.add(vizinho)
                    vizinho.pai     = atual
                    vizinho.custo_g = atual.custo_g + vizinho.custo_travessia
                    fila.append(vizinho)

        return metricas.construir_resultado([], ordem_visitados, 0, 0, encontrado=False)

    def _reconstruir(self, inicio: No, objetivo: No) -> Tuple[List[No], float]:
        caminho:     List[No] = []
        atual:       No       = objetivo
        custo_total: float    = 0.0

        while atual is not None:
            caminho.append(atual)
            custo_total += atual.custo_travessia if atual != inicio else 0
            atual = atual.pai

        caminho.reverse()
        return caminho, custo_total
