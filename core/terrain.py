# core/terrain.py — tipos de terreno, custos e cores da interface

from enum import Enum
from dataclasses import dataclass


@dataclass(frozen=True)
class PropriedadeTerreno:
    # propriedades imutaveis de um tipo de terreno
    nome:    str
    custo:   int
    cor:     str
    simbolo: str


class Terreno(Enum):
    # cada valor carrega suas propriedades completas
    PLANO    = PropriedadeTerreno("Plano",   custo=1,  cor="#A8D5A2", simbolo=".")
    ARENOSO  = PropriedadeTerreno("Arenoso", custo=4,  cor="#F5DEB3", simbolo="~")
    ROCHOSO  = PropriedadeTerreno("Rochoso", custo=10, cor="#A0A0A0", simbolo="^")
    PANTANO  = PropriedadeTerreno("Pantano", custo=20, cor="#6B8E6B", simbolo="#")
    PAREDE   = PropriedadeTerreno("Parede",  custo=-1, cor="#2C2C2C", simbolo="X")

    @property
    def custo(self) -> int:
        return self.value.custo

    @property
    def cor(self) -> str:
        return self.value.cor

    @property
    def simbolo(self) -> str:
        return self.value.simbolo

    @property
    def rotulo(self) -> str:
        return self.value.nome

    def eh_transitavel(self) -> bool:
        return self.custo > 0


# cores para elementos especiais do mapa
CORES_ELEMENTOS = {
    "agente":     "#FF6B35",
    "objetivo":   "#FFD700",
    "recompensa": "#00CED1",
    "caminho":    "#FF69B4",
    "visitado":   "#DDA0DD",
    "inicio":     "#FF6B35",
}
