# utils/metrics.py — coleta metricas de desempenho de uma execucao de busca

import time
from dataclasses import dataclass, field
from typing import List, Optional
from contextlib import contextmanager


@dataclass
class ResultadoBusca:
    # resultado completo de uma execucao de algoritmo de busca
    caminho:         List = field(default_factory=list)
    nos_visitados:   List = field(default_factory=list)
    custo_total:     float = 0.0
    recompensa_total: int  = 0
    nos_expandidos:  int   = 0
    tempo_ms:        float = 0.0
    algoritmo:       str   = ""
    encontrado:      bool  = False
    mensagem:        str   = ""

    @property
    def custo_liquido(self) -> float:
        return max(0.0, self.custo_total - self.recompensa_total)

    @property
    def tamanho_caminho(self) -> int:
        return len(self.caminho)

    def resumo(self) -> str:
        if not self.encontrado:
            return f"[{self.algoritmo}] {self.mensagem}"
        linhas = [
            f"Algoritmo   : {self.algoritmo}",
            f"Caminho     : {self.tamanho_caminho} nos",
            f"Custo total : {self.custo_total:.0f}",
            f"Recompensas : +{self.recompensa_total}",
            f"Custo liqui.: {self.custo_liquido:.0f}",
            f"Nos expand. : {self.nos_expandidos}",
            f"Tempo       : {self.tempo_ms:.6f} ms",
        ]
        return "\n".join(linhas)


class Metricas:
    # contexto de medicao de tempo para uma busca

    def __init__(self, nome_algoritmo: str) -> None:
        self.nome_algoritmo  = nome_algoritmo
        self._tempo_inicio:  Optional[float] = None
        self._tempo_decorrido: float = 0.0
        self.nos_expandidos: int = 0

    @contextmanager
    def medir(self):
        self._tempo_inicio = time.perf_counter()
        try:
            yield self
        finally:
            self._tempo_decorrido = (time.perf_counter() - self._tempo_inicio) * 1000

    def expandir_no(self) -> None:
        self.nos_expandidos += 1

    def construir_resultado(
        self,
        caminho: List,
        nos_visitados: List,
        custo_total: float,
        recompensa_total: int,
        encontrado: bool,
        mensagem: str = "",
    ) -> ResultadoBusca:
        return ResultadoBusca(
            caminho=caminho,
            nos_visitados=nos_visitados,
            custo_total=custo_total,
            recompensa_total=recompensa_total,
            nos_expandidos=self.nos_expandidos,
            tempo_ms=self._tempo_decorrido,
            algoritmo=self.nome_algoritmo,
            encontrado=encontrado,
            mensagem=mensagem or ("Caminho encontrado!" if encontrado else "Caminho nao encontrado."),
        )
