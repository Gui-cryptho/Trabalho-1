# core/node.py — representa cada celula (vertice) do grafo

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from core.terrain import Terreno


@dataclass
class No:
    # vertice do grafo: posicao, terreno, recompensa e metadados de busca
    linha:      int
    coluna:     int
    terreno:    Terreno = Terreno.PLANO
    recompensa: int     = 0
    eh_inicio:  bool    = False
    eh_objetivo: bool   = False

    # campos de busca — resetados antes de cada execucao
    custo_g: float         = field(default=float('inf'), compare=False, repr=False)
    custo_h: float         = field(default=0.0,          compare=False, repr=False)
    pai:     Optional['No'] = field(default=None,        compare=False, repr=False)

    def __hash__(self) -> int:
        return hash((self.linha, self.coluna))

    def __eq__(self, outro: object) -> bool:
        if not isinstance(outro, No):
            return False
        return self.linha == outro.linha and self.coluna == outro.coluna

    def __lt__(self, outro: 'No') -> bool:
        # permite uso em heapq pelo custo_f
        return self.custo_f < outro.custo_f

    @property
    def custo_f(self) -> float:
        return self.custo_g + self.custo_h

    @property
    def posicao(self) -> tuple[int, int]:
        return (self.linha, self.coluna)

    @property
    def custo_travessia(self) -> int:
        return self.terreno.custo

    def eh_transitavel(self) -> bool:
        return self.terreno.eh_transitavel()

    def tem_recompensa(self) -> bool:
        return self.recompensa > 0

    def resetar_estado(self) -> None:
        self.custo_g = float('inf')
        self.custo_h = 0.0
        self.pai     = None

    def __repr__(self) -> str:
        marcador = "S" if self.eh_inicio else ("G" if self.eh_objetivo else self.terreno.simbolo)
        return f"No({self.linha},{self.coluna})[{marcador}]"
