"""
utils/metrics.py
-----------------
Coleta e armazena métricas de desempenho de uma execução de busca.
Fornece um contexto (with statement) para medir o tempo automaticamente
e uma dataclass para transportar os resultados entre camadas.
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional
from contextlib import contextmanager


@dataclass
class SearchResult:
    """
    Resultado completo de uma execução de algoritmo de busca.

    Campos:
        path          — sequência de nós do início ao objetivo (vazia se não encontrado)
        visited_order — ordem em que os nós foram expandidos (para animação)
        total_cost    — custo acumulado real do caminho
        total_reward  — soma das recompensas coletadas ao longo do caminho
        nodes_expanded — quantos nós foram retirados da fila/pilha
        elapsed_ms    — tempo de execução em milissegundos
        algorithm     — nome do algoritmo utilizado
        found         — True se um caminho foi encontrado
        message       — mensagem descritiva (erro, beco sem saída, etc.)
    """
    path: List = field(default_factory=list)
    visited_order: List = field(default_factory=list)
    total_cost: float = 0.0
    total_reward: int = 0
    nodes_expanded: int = 0
    elapsed_ms: float = 0.0
    algorithm: str = ""
    found: bool = False
    message: str = ""

    @property
    def net_cost(self) -> float:
        """Custo líquido: custo do caminho descontando recompensas coletadas."""
        return max(0.0, self.total_cost - self.total_reward)

    @property
    def path_length(self) -> int:
        """Número de nós no caminho (incluindo início e objetivo)."""
        return len(self.path)

    def summary(self) -> str:
        """Retorna um resumo formatado para exibição na GUI."""
        if not self.found:
            return f"[{self.algorithm}] {self.message}"
        lines = [
            f"Algoritmo   : {self.algorithm}",
            f"Caminho     : {self.path_length} nós",
            f"Custo total : {self.total_cost:.0f}",
            f"Recompensas : +{self.total_reward}",
            f"Custo líqui.: {self.net_cost:.0f}",
            f"Nós expand. : {self.nodes_expanded}",
            f"Tempo       : {self.elapsed_ms:.2f} ms",
        ]
        return "\n".join(lines)


class Metrics:
    """
    Contexto de medição de tempo para uma busca.

    Uso:
        metrics = Metrics("A*")
        with metrics.measure():
            # executa o algoritmo
            ...
        result = metrics.build_result(path, visited, cost, reward)
    """

    def __init__(self, algorithm_name: str) -> None:
        self.algorithm_name = algorithm_name
        self._start_time: Optional[float] = None
        self._elapsed_ms: float = 0.0
        self.nodes_expanded: int = 0

    @contextmanager
    def measure(self):
        """Gerenciador de contexto que cronometra o bloco interno."""
        self._start_time = time.perf_counter()
        try:
            yield self
        finally:
            self._elapsed_ms = (time.perf_counter() - self._start_time) * 1000

    def expand_node(self) -> None:
        """Incrementa o contador de nós expandidos."""
        self.nodes_expanded += 1

    def build_result(
        self,
        path: List,
        visited_order: List,
        total_cost: float,
        total_reward: int,
        found: bool,
        message: str = "",
    ) -> SearchResult:
        """Constrói o SearchResult com todas as métricas coletadas."""
        return SearchResult(
            path=path,
            visited_order=visited_order,
            total_cost=total_cost,
            total_reward=total_reward,
            nodes_expanded=self.nodes_expanded,
            elapsed_ms=self._elapsed_ms,
            algorithm=self.algorithm_name,
            found=found,
            message=message or ("Caminho encontrado!" if found else "Caminho não encontrado."),
        )
