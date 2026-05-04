# core/graph.py — constroi e gerencia o grafo de navegacao como grid 2D

from __future__ import annotations
import random
from typing import List, Optional, Tuple
from core.node import No
from core.terrain import Terreno

# legenda: '.'=Plano '~'=Arenoso '^'=Rochoso '#'=Pantano
#          'X'=Parede 'S'=Inicio 'G'=Objetivo '$'=Recompensa
MAPA_PADRAO: List[str] = [
    "S . . X . . $ ~",
    ". X . X . ^ ^ $",
    ". X . . . X . .",
    ". . ^ X $ . X G",
    "X . . . X . . .",
    ". ~ ~ $ . X . .",
    ". . X . $ ~ . .",
    ". ^ . . . $ ^ .",
]

_CHAR_PARA_TERRENO = {
    '.': Terreno.PLANO,
    '~': Terreno.ARENOSO,
    '^': Terreno.ROCHOSO,
    '#': Terreno.PANTANO,
    'X': Terreno.PAREDE,
    'S': Terreno.PLANO,
    'G': Terreno.PLANO,
    '$': Terreno.PLANO,
}

# movimentos validos: cima, baixo, esquerda, direita
_DIRECOES: List[Tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class Grafo:
    # grafo representado como grid 2D de No

    def __init__(self) -> None:
        self.linhas:      int         = 0
        self.colunas:     int         = 0
        self.nos:         List[List[No]] = []
        self.no_inicial:  Optional[No]   = None
        self.no_objetivo: Optional[No]   = None
        self._nos_recompensa: List[No]   = []

    # ── construcao ────────────────────────────────────────────────────────────

    def construir_do_mapa(self, definicao: List[str] = MAPA_PADRAO) -> None:
        # constroi o grafo a partir de uma lista de strings (chars separados por espaco)
        self.nos = []
        self._nos_recompensa = []
        self.no_inicial  = None
        self.no_objetivo = None

        for l, linha in enumerate(definicao):
            chars = linha.split()
            linha_nos: List[No] = []
            for c, ch in enumerate(chars):
                terreno = _CHAR_PARA_TERRENO.get(ch, Terreno.PLANO)
                no = No(linha=l, coluna=c, terreno=terreno)

                if ch == 'S':
                    no.eh_inicio  = True
                    self.no_inicial = no
                elif ch == 'G':
                    no.eh_objetivo  = True
                    self.no_objetivo = no
                elif ch == '$':
                    no.recompensa = random.randint(5, 20)
                    self._nos_recompensa.append(no)

                linha_nos.append(no)
            self.nos.append(linha_nos)

        self.linhas  = len(self.nos)
        self.colunas = len(self.nos[0]) if self.nos else 0

        if not self.no_inicial or not self.no_objetivo:
            raise ValueError("O mapa precisa ter inicio 'S' e objetivo 'G'.")

    def construir_aleatorio(self, linhas: int = 8, colunas: int = 8,
                             prob_parede: float = 0.15,
                             qtd_recompensas: int = 5) -> None:
        # gera mapa aleatorio garantindo que inicio e objetivo sejam alcancaveis
        terrenos = [Terreno.PLANO, Terreno.PLANO, Terreno.ARENOSO,
                    Terreno.ROCHOSO, Terreno.PANTANO]

        self.nos = []
        self._nos_recompensa = []

        for l in range(linhas):
            linha_nos: List[No] = []
            for c in range(colunas):
                if random.random() < prob_parede:
                    t = Terreno.PAREDE
                else:
                    t = random.choice(terrenos)
                linha_nos.append(No(linha=l, coluna=c, terreno=t))
            self.nos.append(linha_nos)

        self.linhas  = linhas
        self.colunas = colunas

        self.nos[0][0].terreno  = Terreno.PLANO
        self.nos[0][0].eh_inicio = True
        self.no_inicial = self.nos[0][0]

        self.nos[linhas-1][colunas-1].terreno    = Terreno.PLANO
        self.nos[linhas-1][colunas-1].eh_objetivo = True
        self.no_objetivo = self.nos[linhas-1][colunas-1]

        transitaveis = [n for linha in self.nos for n in linha
                        if n.eh_transitavel() and not n.eh_inicio and not n.eh_objetivo]
        for no in random.sample(transitaveis, min(qtd_recompensas, len(transitaveis))):
            no.recompensa = random.randint(5, 20)
            self._nos_recompensa.append(no)

    # ── acesso e navegacao ────────────────────────────────────────────────────

    def obter_no(self, linha: int, coluna: int) -> Optional[No]:
        if 0 <= linha < self.linhas and 0 <= coluna < self.colunas:
            return self.nos[linha][coluna]
        return None

    def obter_vizinhos(self, no: No) -> List[No]:
        # retorna vizinhos transitaveis nas 4 direcoes
        vizinhos: List[No] = []
        for dl, dc in _DIRECOES:
            vizinho = self.obter_no(no.linha + dl, no.coluna + dc)
            if vizinho and vizinho.eh_transitavel():
                vizinhos.append(vizinho)
        return vizinhos

    def obter_transitaveis(self) -> List[No]:
        return [n for linha in self.nos for n in linha if n.eh_transitavel()]

    def obter_recompensas(self) -> List[No]:
        return [n for n in self._nos_recompensa if n.tem_recompensa()]

    # ── estado ────────────────────────────────────────────────────────────────

    def resetar_estado_busca(self) -> None:
        for linha in self.nos:
            for no in linha:
                no.resetar_estado()

    def coletar_recompensa(self, no: No) -> int:
        valor = no.recompensa
        no.recompensa = 0
        return valor

    def resetar_recompensas(self) -> None:
        for no in self._nos_recompensa:
            no.recompensa = random.randint(5, 20)

    def contar_vertices(self) -> int:
        return len(self.obter_transitaveis())

    def __repr__(self) -> str:
        linhas_txt = []
        for linha in self.nos:
            linhas_txt.append(" ".join(repr(n)[3:10] for n in linha))
        return f"Grafo({self.linhas}x{self.colunas}):\n" + "\n".join(linhas_txt)
