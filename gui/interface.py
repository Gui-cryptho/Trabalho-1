# gui/interface.py — interface grafica com Pygame e pixel art (Kenney Tiny Dungeon CC0)
# estetica de RPG retro com tiles escalados 4x, fonte bitmap e menus estilizados

import sys, os, math, threading
import pygame
from typing import List, Optional

from core.graph import Grafo
from core.node import No
from core.terrain import Terreno
from algorithms.bfs import BuscaLargura
from algorithms.dfs import BuscaProfundidade
from algorithms.greedy import BuscaGulosa
from algorithms.astar import BuscaAEstrela
from utils.metrics import ResultadoBusca
from utils.heuristics import manhattan, euclidiana, criar_heuristica_proxima
from utils.audio import GerenciadorAudio

# ── caminhos ──────────────────────────────────────────────────────────────────
_RAIZ        = os.path.dirname(os.path.dirname(__file__))
CAMINHO_FONT = os.path.join(_RAIZ, 'assets', 'fonts',   'PressStart2P.ttf')
DIR_TILES    = os.path.join(_RAIZ, 'assets', 'sprites', 'Tiles')

# ── dimensoes base ────────────────────────────────────────────────────────────
LARG_JANELA, ALT_JANELA = 1440, 920
LARG_PAINEL = 300
ALT_TOPO    = 54
ALT_STATUS  = 36
TAM_TILE    = 96   # tiles 16x16 escalados 6x

# ── animacao ──────────────────────────────────────────────────────────────────
MS_VISITA = 22
MS_PASSO  = 160

# ── ids dos tiles (Kenney Tiny Dungeon) ───────────────────────────────────────
TILES = {
    'plano':      1,
    'arenoso':   30,
    'rochoso':   24,
    'pantano':   20,
    'parede':    38,
    'agente':    84,
    'objetivo':  90,
    'recompensa': 116,
    'inicio':    85,
}

# ── paleta de cores ───────────────────────────────────────────────────────────
C_FUNDO  = (10,   8,  18)
C_PAINEL = (14,  12,  24)
C_ESCURO = ( 6,   4,  12)
C_OURO   = (210, 165,  45)
C_OURO2  = (245, 205,  80)
C_TEXTO  = (225, 215, 185)
C_OPACO  = (130, 120, 100)
C_VERDE  = (100, 200, 100)
C_VERM   = (220,  80,  80)
C_HOVER  = (100, 140, 210)

LISTA_ALGORITMOS = ["BFS (Largura)", "DFS (Profundidade)", "Greedy (Gulosa)", "A* (A estrela)"]
LISTA_HEURISTICAS = ["Manhattan", "Euclidiana", "Recompensas proximas"]


class EntradaTexto:
    # campo de texto para digitar coordenadas (linha,col)

    def __init__(self, x, y, larg, alt, placeholder="linha,col"):
        self.rect        = pygame.Rect(x, y, larg, alt)
        self.texto       = ""
        self.placeholder = placeholder
        self.ativo       = False
        self._fonte      = None

    def definir_fonte(self, f):
        self._fonte = f

    def processar_evento(self, evento) -> bool:
        # retorna True quando o usuario confirma com Enter
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.ativo = self.rect.collidepoint(evento.pos)

        if evento.type == pygame.KEYDOWN and self.ativo:
            if evento.key == pygame.K_BACKSPACE:
                self.texto = self.texto[:-1]
                return False
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return True
            if evento.unicode in "0123456789," and len(self.texto) < 7:
                self.texto += evento.unicode

        return False

    def desenhar(self, tela):
        borda = C_OURO if self.ativo else C_OPACO
        pygame.draw.rect(tela, C_ESCURO, self.rect, border_radius=3)
        pygame.draw.rect(tela, borda,    self.rect, 1, border_radius=3)

        if self._fonte:
            exibir = self.texto if self.texto else self.placeholder
            cor    = C_TEXTO   if self.texto else C_OPACO
            t = self._fonte.render(exibir, True, cor)
            tela.blit(t, t.get_rect(midleft=(self.rect.x + 6, self.rect.centery)))

            # cursor piscante
            if self.ativo and pygame.time.get_ticks() % 900 < 450:
                cx = self.rect.x + 6 + (self._fonte.size(self.texto)[0] if self.texto else 0) + 1
                pygame.draw.rect(tela, C_TEXTO, (cx, self.rect.y + 4, 2, self.rect.height - 8))


ID_TILE_TERRENO = {
    Terreno.PLANO:   TILES['plano'],
    Terreno.ARENOSO: TILES['arenoso'],
    Terreno.ROCHOSO: TILES['rochoso'],
    Terreno.PANTANO: TILES['pantano'],
    Terreno.PAREDE:  TILES['parede'],
}


# ─────────────────────────────────────────────────────────────────────────────
class AplicacaoNavegacao:

    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self._larg, self._alt = LARG_JANELA, ALT_JANELA
        self._tela_cheia = False
        self.tela  = pygame.display.set_mode((LARG_JANELA, ALT_JANELA), pygame.RESIZABLE)
        pygame.display.set_caption("Trabalho de IA 1")
        self.relogio = pygame.time.Clock()
        self._audio  = GerenciadorAudio()

        # fontes
        self.f_titulo    = pygame.font.Font(CAMINHO_FONT, 16)
        self.f_principal = pygame.font.Font(CAMINHO_FONT, 12)
        self.f_pequena   = pygame.font.Font(CAMINHO_FONT, 10)
        self.f_mono      = pygame.font.SysFont("monospace", 14)
        self.f_coord     = pygame.font.SysFont("monospace", 12, bold=True)

        # tiles pixel art e overlays
        self._cache_tiles: dict = {}
        self._tiles = {k: self._carregar_tile(v) for k, v in TILES.items()}
        self._ov_visitado  = self._criar_overlay((148,  0, 211), 135)
        self._ov_caminho   = self._criar_overlay((255, 20, 147), 150)
        self._ov_inicio    = self._criar_overlay(( 50, 50, 200),  80)
        self._ov_objetivo  = self._criar_overlay((220, 180,   0),  80)

        # grafo e estado da busca
        self.grafo = Grafo()
        self.grafo.construir_do_mapa()

        self._resultado:  Optional[ResultadoBusca] = None
        self._pendente:   Optional[ResultadoBusca] = None
        self._pronto:     bool = False
        self._executando: bool = False
        self._status:     str  = "Selecione o algoritmo e pressione BUSCAR."

        # animacao
        self._estado_anim    = "ocioso"
        self._anim_visitados: List[No] = []
        self._anim_caminho:   List[No] = []
        self._anim_idx    = 0
        self._anim_ts     = 0
        self._coletado    = 0
        self._destaque:   dict = {}   # id(no) -> overlay

        # selecao de algoritmo e heuristica
        self._idx_algo = 3   # A* por padrao
        self._idx_heur = 0   # Manhattan por padrao
        self._btn_hover = None

        # rects populados no primeiro _desenhar_painel()
        self._rects_botao  = {}
        self._rect_algo    = pygame.Rect(0, 0, 0, 0)
        self._rect_heur    = pygame.Rect(0, 0, 0, 0)

        # campo de texto para destino
        self._entrada_destino = EntradaTexto(10, 0, LARG_PAINEL - 20, 28, "linha,col")
        self._entrada_destino.definir_fonte(self.f_pequena)

        self._recalcular_grade()

    # ── tiles e overlays ──────────────────────────────────────────────────────

    def _carregar_tile(self, id_tile: int) -> pygame.Surface:
        if id_tile in self._cache_tiles:
            return self._cache_tiles[id_tile]
        caminho = os.path.join(DIR_TILES, f'tile_{id_tile:04d}.png')
        bruto   = pygame.image.load(caminho).convert_alpha()
        escalado = pygame.transform.scale(bruto, (TAM_TILE, TAM_TILE))
        self._cache_tiles[id_tile] = escalado
        return escalado

    def _criar_overlay(self, rgb, alfa) -> pygame.Surface:
        s = pygame.Surface((TAM_TILE, TAM_TILE), pygame.SRCALPHA)
        s.fill((*rgb, alfa))
        return s

    def _recalcular_grade(self):
        colunas = self.grafo.colunas
        linhas  = self.grafo.linhas
        area_larg = self._larg - LARG_PAINEL
        area_alt  = self._alt  - ALT_TOPO - ALT_STATUS
        self._gx = (area_larg - colunas * TAM_TILE) // 2
        self._gy = ALT_TOPO + (area_alt - linhas * TAM_TILE) // 2
        self._px = self._larg - LARG_PAINEL   # borda esquerda do painel

    def _alternar_tela_cheia(self):
        self._tela_cheia = not self._tela_cheia
        if self._tela_cheia:
            info = pygame.display.Info()
            self._larg, self._alt = info.current_w, info.current_h
            self.tela = pygame.display.set_mode(
                (self._larg, self._alt), pygame.FULLSCREEN)
        else:
            self._larg, self._alt = LARG_JANELA, ALT_JANELA
            self.tela = pygame.display.set_mode(
                (self._larg, self._alt), pygame.RESIZABLE)
        self._recalcular_grade()

    # ── loop principal ────────────────────────────────────────────────────────

    def executar(self):
        while True:
            self.relogio.tick(60)
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self._processar_evento(evento)
            self._atualizar()
            self._desenhar()
            pygame.display.flip()

    # ── eventos ───────────────────────────────────────────────────────────────

    def _processar_evento(self, evento):
        mx, my = pygame.mouse.get_pos()
        self._btn_hover = None

        # atalhos de teclado
        if evento.type == pygame.KEYDOWN and not self._entrada_destino.ativo:
            if evento.key == pygame.K_F11:
                self._alternar_tela_cheia()
            if evento.key == pygame.K_m:
                self._audio.alternar_mudo()

        # redimensionamento de janela
        if evento.type == pygame.VIDEORESIZE and not self._tela_cheia:
            self._larg, self._alt = evento.w, evento.h
            self.tela = pygame.display.set_mode(
                (self._larg, self._alt), pygame.RESIZABLE)
            self._recalcular_grade()

        # campo de destino
        if self._entrada_destino.processar_evento(evento):
            self._aplicar_destino()

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for nome, rect in self._rects_botao.items():
                if rect.collidepoint(mx, my):
                    self._audio.reproduzir('clique')
                    self._ao_clicar(nome)
                    return
            if self._rect_algo.collidepoint(mx, my):
                self._idx_algo = (self._idx_algo + 1) % len(LISTA_ALGORITMOS)
                self._audio.reproduzir('clique')
            if self._rect_heur.collidepoint(mx, my):
                self._idx_heur = (self._idx_heur + 1) % len(LISTA_HEURISTICAS)
                self._audio.reproduzir('clique')

        if evento.type == pygame.MOUSEMOTION:
            for nome, rect in self._rects_botao.items():
                if rect.collidepoint(mx, my):
                    self._btn_hover = nome

    def _ao_clicar(self, nome):
        if nome == 'buscar':
            self._iniciar_busca()
        elif nome == 'aleatorio':
            self._mapa_aleatorio()
        elif nome == 'resetar':
            self._resetar()

    def _aplicar_destino(self):
        bruto = self._entrada_destino.texto.strip()
        try:
            partes = bruto.split(",")
            linha, coluna = int(partes[0]), int(partes[1])
            self._definir_objetivo(linha, coluna)
            self._entrada_destino.texto = ""
        except Exception:
            self._status = "Formato invalido. Use  linha,col  (ex: 3,7)"

    def _definir_objetivo(self, linha: int, coluna: int):
        no = self.grafo.obter_no(linha, coluna)
        if no is None:
            self._status = f"({linha},{coluna}) esta fora do mapa!"
            return
        if not no.eh_transitavel():
            self._status = f"({linha},{coluna}) e uma parede — escolha outra celula."
            return
        if no.eh_inicio:
            self._status = "Destino nao pode ser o ponto de inicio!"
            return
        if self.grafo.no_objetivo:
            self.grafo.no_objetivo.eh_objetivo = False
        no.eh_objetivo       = True
        self.grafo.no_objetivo = no
        self._destaque    = {}
        self._estado_anim = "ocioso"
        self._resultado   = None
        self._status = f"Destino definido: ({linha},{coluna}) — pronto para buscar."

    # ── busca ─────────────────────────────────────────────────────────────────

    def _iniciar_busca(self):
        if self._executando:
            return
        self._destaque    = {}
        self._coletado    = 0
        self._resultado   = None
        self._pronto      = False
        self._estado_anim = "ocioso"
        self._executando  = True
        self._status      = "Executando busca..."
        self._audio.reproduzir('iniciar')

        heuristica = self._obter_heuristica()
        algoritmos = {
            "BFS (Largura)":      BuscaLargura(self.grafo),
            "DFS (Profundidade)": BuscaProfundidade(self.grafo),
            "Greedy (Gulosa)":    BuscaGulosa(self.grafo, heuristica),
            "A* (A estrela)":     BuscaAEstrela(self.grafo, heuristica),
        }
        algo = algoritmos[LISTA_ALGORITMOS[self._idx_algo]]

        def executar_busca():
            resultado      = algo.buscar(self.grafo.no_inicial, self.grafo.no_objetivo)
            self._pendente = resultado
            self._pronto   = True

        threading.Thread(target=executar_busca, daemon=True).start()

    def _obter_heuristica(self):
        if self._idx_heur == 1:
            return euclidiana
        if self._idx_heur == 2:
            return criar_heuristica_proxima(self.grafo)
        return manhattan

    # ── atualizacao ───────────────────────────────────────────────────────────

    def _atualizar(self):
        if self._pronto:
            self._pronto      = False
            self._resultado   = self._pendente
            self._executando  = False
            resultado = self._resultado

            if not resultado.encontrado:
                self._status = f"SEM CAMINHO! {resultado.mensagem}"
                self._audio.reproduzir('erro')
                return

            conjunto_caminho = set(id(n) for n in resultado.caminho)
            self._anim_visitados = [
                n for n in resultado.nos_visitados
                if not n.eh_inicio and not n.eh_objetivo and id(n) not in conjunto_caminho
            ]
            self._anim_caminho = resultado.caminho[:]
            self._anim_idx     = 0
            self._anim_ts      = pygame.time.get_ticks()
            self._estado_anim  = "visitando"
            self._status       = f"Explorando mapa... ({len(resultado.caminho)} passos no caminho)"

        agora = pygame.time.get_ticks()

        if self._estado_anim == "visitando":
            if agora - self._anim_ts >= MS_VISITA:
                self._anim_ts = agora
                if self._anim_idx < len(self._anim_visitados):
                    no = self._anim_visitados[self._anim_idx]
                    self._destaque[id(no)] = self._ov_visitado
                    self._anim_idx += 1
                else:
                    for no in self._anim_caminho:
                        if not no.eh_inicio and not no.eh_objetivo:
                            self._destaque[id(no)] = self._ov_caminho
                    self._anim_idx    = 0
                    self._anim_ts     = agora
                    self._estado_anim = "movendo"
                    self._status      = "Agente em movimento!"

        elif self._estado_anim == "movendo":
            if agora - self._anim_ts >= MS_PASSO:
                self._anim_ts = agora
                if self._anim_idx < len(self._anim_caminho):
                    no = self._anim_caminho[self._anim_idx]
                    if no.tem_recompensa():
                        self._coletado += no.recompensa
                        self.grafo.coletar_recompensa(no)
                        self._audio.reproduzir('recompensa')
                    else:
                        self._audio.reproduzir('passo')
                    self._status = (
                        f"Passo {self._anim_idx + 1}/{len(self._anim_caminho)}"
                        f"   Recompensas: +{self._coletado}"
                    )
                    self._anim_idx += 1
                else:
                    self._estado_anim = "concluido"
                    self._status = f"* OBJETIVO ALCANCADO! *  Recompensas: +{self._coletado}"
                    self._audio.reproduzir('vitoria')

    # ── desenho ───────────────────────────────────────────────────────────────

    def _desenhar(self):
        self.tela.fill(C_FUNDO)
        self._desenhar_barra_topo()
        self._desenhar_painel()
        self._desenhar_grade()
        self._desenhar_status()

    # ── barra de topo ─────────────────────────────────────────────────────────

    def _desenhar_barra_topo(self):
        larg = self._larg
        pygame.draw.rect(self.tela, C_PAINEL, (0, 0, larg, ALT_TOPO))
        pygame.draw.line(self.tela, C_OURO, (0, ALT_TOPO - 1), (larg, ALT_TOPO - 1), 2)

        # titulo centralizado na area do mapa
        cx = (larg - LARG_PAINEL) // 2
        t1 = self.f_titulo.render("DUNGEONS", True, C_OURO2)
        t2 = self.f_titulo.render("OF KOTLIN", True, C_OURO)
        self._texto_rpg(self.f_titulo, "DUNGEONS",  (cx - t1.get_width() // 2, 6),  C_OURO2)
        self._texto_rpg(self.f_titulo, "OF KOTLIN", (cx - t2.get_width() // 2, 28), C_OURO)

        # indicadores: mute e fullscreen
        cor_mudo = C_VERM if self._audio.mudo else C_OPACO
        t_mudo   = self.f_pequena.render("[M] MUDO" if self._audio.mudo else "[M] musica on", True, cor_mudo)
        self.tela.blit(t_mudo, (larg - LARG_PAINEL - t_mudo.get_width() - 16, 10))

        t_f11 = self.f_pequena.render(
            "[F11] tela cheia" if not self._tela_cheia else "[F11] janela", True, C_OPACO)
        self.tela.blit(t_f11, (larg - LARG_PAINEL - t_f11.get_width() - 16, 24))

    # ── painel direito ────────────────────────────────────────────────────────

    def _desenhar_painel(self):
        px  = self._px
        pw  = LARG_PAINEL - 20
        x   = px + 10
        alt = self._alt

        # fundo com textura de pedra
        pygame.draw.rect(self.tela, C_PAINEL,
                         (px, ALT_TOPO, LARG_PAINEL, alt - ALT_TOPO - ALT_STATUS))
        tile_parede = self._tiles['parede']
        for l in range((alt - ALT_TOPO) // TAM_TILE + 1):
            for c in range(LARG_PAINEL // TAM_TILE + 1):
                tmp = tile_parede.copy()
                tmp.set_alpha(35)
                self.tela.blit(tmp, (px + c * TAM_TILE, ALT_TOPO + l * TAM_TILE))
        pygame.draw.line(self.tela, C_OURO, (px, ALT_TOPO), (px, alt - ALT_STATUS), 2)

        y = ALT_TOPO + 12

        # seletores
        y = self._desenhar_seletor(x, y, pw, "ALGORITMO",  LISTA_ALGORITMOS,  self._idx_algo, '_rect_algo')
        y += 6
        y = self._desenhar_seletor(x, y, pw, "HEURISTICA", LISTA_HEURISTICAS, self._idx_heur, '_rect_heur')
        y += 8

        # campo de destino
        lbl = self.f_pequena.render("DESTINO (Enter p/ confirmar)", True, C_OURO)
        self.tela.blit(lbl, (x, y)); y += 17
        self._entrada_destino.rect.x = x
        self._entrada_destino.rect.y = y
        self._entrada_destino.rect.w = pw
        self._entrada_destino.desenhar(self.tela)
        objetivo = self.grafo.no_objetivo
        if objetivo:
            dica = self.f_pequena.render(f"atual: {objetivo.linha},{objetivo.coluna}", True, C_OPACO)
            self.tela.blit(dica, (x + pw - dica.get_width(), y + 7))
        y += 36

        pygame.draw.line(self.tela, C_OURO, (x, y), (x + pw, y)); y += 12

        # botoes: BUSCAR (destaque) + ALEATORIO | RESETAR lado a lado
        self._rects_botao = {}

        rect_buscar = pygame.Rect(x, y, pw, 34)
        self._rects_botao['buscar'] = rect_buscar
        hover_b = (self._btn_hover == 'buscar')
        pygame.draw.rect(self.tela, (40, 35, 10) if hover_b else C_ESCURO, rect_buscar, border_radius=3)
        pygame.draw.rect(self.tela, C_OURO2 if hover_b else C_OURO, rect_buscar, 1, border_radius=3)
        lbl = self.f_principal.render("BUSCAR", True, C_OURO2 if hover_b else C_OURO)
        self.tela.blit(lbl, lbl.get_rect(center=rect_buscar.center))
        y += 42

        metade = (pw - 6) // 2
        for i, (rotulo, chave) in enumerate([("ALEATORIO", "aleatorio"), ("RESETAR", "resetar")]):
            rx   = x + i * (metade + 6)
            rect = pygame.Rect(rx, y, metade, 28)
            self._rects_botao[chave] = rect
            hover = (self._btn_hover == chave)
            pygame.draw.rect(self.tela, (20, 18, 35) if hover else C_ESCURO, rect, border_radius=3)
            pygame.draw.rect(self.tela, C_OURO if hover else C_OPACO, rect, 1, border_radius=3)
            lbl = self.f_pequena.render(rotulo, True, C_OURO if hover else C_OPACO)
            self.tela.blit(lbl, lbl.get_rect(center=rect.center))
        y += 36

        pygame.draw.line(self.tela, C_OURO, (x, y), (x + pw, y)); y += 10

        # legenda de terrenos
        lbl = self.f_pequena.render("TERRENOS", True, C_OURO)
        self.tela.blit(lbl, (x, y)); y += 18

        legenda = [
            ('plano',      "Plano   custo 1"),
            ('arenoso',    "Arenoso custo 4"),
            ('rochoso',    "Rochoso custo 10"),
            ('pantano',    "Pantano custo 20"),
            ('parede',     "Parede  bloq."),
            ('objetivo',   "Objetivo"),
            ('recompensa', "Recompensa"),
        ]
        for chave, desc in legenda:
            mini = pygame.transform.scale(self._tiles[chave], (24, 24))
            self.tela.blit(mini, (x, y))
            txt = self.f_pequena.render(desc, True, C_TEXTO)
            self.tela.blit(txt, (x + 30, y + 6))
            y += 26

        pygame.draw.line(self.tela, C_OURO, (x, y), (x + pw, y)); y += 10

        # metricas
        lbl = self.f_pequena.render("METRICAS", True, C_OURO)
        self.tela.blit(lbl, (x, y)); y += 18

        if self._resultado:
            cor = C_VERDE if self._resultado.encontrado else C_VERM
            for linha in self._resultado.resumo().split("\n"):
                t = self.f_mono.render(linha, True, cor)
                self.tela.blit(t, (x, y)); y += 17
        else:
            t = self.f_mono.render("Aguardando...", True, C_OPACO)
            self.tela.blit(t, (x, y))

        # rodape: contagem de vertices
        vc = self.f_mono.render(f"Vertices: {self.grafo.contar_vertices()}", True, C_OPACO)
        self.tela.blit(vc, (x, alt - ALT_STATUS - 22))

    def _desenhar_seletor(self, x, y, larg, rotulo, opcoes, idx, attr) -> int:
        # desenha seletor clicavel estilo RPG, retorna y apos o widget
        lbl = self.f_pequena.render(rotulo, True, C_OURO)
        self.tela.blit(lbl, (x, y)); y += 17

        rect = pygame.Rect(x, y, larg, 28)
        setattr(self, attr, rect)
        pygame.draw.rect(self.tela, C_ESCURO, rect, border_radius=3)
        pygame.draw.rect(self.tela, C_OURO,   rect, 1, border_radius=3)

        val = opcoes[idx][:18]
        txt = self.f_pequena.render(f"< {val} >", True, C_TEXTO)
        self.tela.blit(txt, txt.get_rect(center=rect.center))
        return y + 34

    def _texto_rpg(self, fonte, texto, pos, cor):
        # texto com sombra estilo RPG
        sombra = fonte.render(texto, True, (0, 0, 0))
        self.tela.blit(sombra, (pos[0] + 1, pos[1] + 1))
        lbl = fonte.render(texto, True, cor)
        self.tela.blit(lbl, pos)

    # ── grade do mapa ─────────────────────────────────────────────────────────

    def _desenhar_grade(self):
        larg_grade = self.grafo.colunas * TAM_TILE
        alt_grade  = self.grafo.linhas  * TAM_TILE
        pygame.draw.rect(self.tela, C_ESCURO,
                         (self._gx - 4, self._gy - 4, larg_grade + 8, alt_grade + 8),
                         border_radius=4)
        pygame.draw.rect(self.tela, C_OURO,
                         (self._gx - 4, self._gy - 4, larg_grade + 8, alt_grade + 8),
                         2, border_radius=4)

        no_agente = None
        if self._estado_anim in ("movendo", "concluido") and self._anim_idx > 0:
            idx_atual = min(self._anim_idx - 1, len(self._anim_caminho) - 1)
            no_agente = self._anim_caminho[idx_atual]

        for linha in self.grafo.nos:
            for no in linha:
                self._desenhar_celula(no, no_agente)

    def _desenhar_celula(self, no: No, no_agente: Optional[No]):
        x = self._gx + no.coluna * TAM_TILE
        y = self._gy + no.linha  * TAM_TILE

        # tile de terreno base
        chave_tile = {
            Terreno.PLANO:   'plano',
            Terreno.ARENOSO: 'arenoso',
            Terreno.ROCHOSO: 'rochoso',
            Terreno.PANTANO: 'pantano',
            Terreno.PAREDE:  'parede',
        }.get(no.terreno, 'plano')
        self.tela.blit(self._tiles[chave_tile], (x, y))

        # overlay de exploracao ou caminho
        if id(no) in self._destaque:
            self.tela.blit(self._destaque[id(no)], (x, y))

        if no.eh_inicio:
            self.tela.blit(self._ov_inicio, (x, y))
            self.tela.blit(self._tiles['inicio'], (x, y))
        elif no.eh_objetivo:
            self.tela.blit(self._ov_objetivo, (x, y))
            self.tela.blit(self._tiles['objetivo'], (x, y))
        else:
            if no.tem_recompensa():
                self.tela.blit(self._tiles['recompensa'], (x, y))
                txt_val  = f"+{no.recompensa}"
                val_surf = self.f_principal.render(txt_val, True, C_OURO2)
                bg_val   = pygame.Surface((val_surf.get_width() + 6, val_surf.get_height() + 4), pygame.SRCALPHA)
                bg_val.fill((0, 0, 0, 170))
                vx = x + TAM_TILE - val_surf.get_width() - 6
                self.tela.blit(bg_val,   (vx - 2, y + 2))
                self.tela.blit(val_surf, (vx,     y + 4))

        # agente com animacao de bob
        if no is no_agente:
            bob = int(math.sin(pygame.time.get_ticks() * 0.008) * 3)
            self.tela.blit(self._tiles['agente'], (x, y + bob))

        # coordenada com fundo escuro e sombra para legibilidade
        txt_coord = f"{no.linha},{no.coluna}"
        c_surf    = self.f_coord.render(txt_coord, True, (220, 210, 170))
        bg_coord  = pygame.Surface((c_surf.get_width() + 4, c_surf.get_height() + 2), pygame.SRCALPHA)
        bg_coord.fill((0, 0, 0, 150))
        self.tela.blit(bg_coord, (x + 2, y + 2))
        self.tela.blit(c_surf,   (x + 4, y + 3))

        # custo do terreno no canto inferior com o mesmo tratamento
        if no.terreno != Terreno.PAREDE and not no.eh_inicio and not no.eh_objetivo:
            txt_custo = f"c:{no.terreno.custo}"
            k_surf    = self.f_coord.render(txt_custo, True, (180, 220, 180))
            bg_custo  = pygame.Surface((k_surf.get_width() + 4, k_surf.get_height() + 2), pygame.SRCALPHA)
            bg_custo.fill((0, 0, 0, 150))
            cy = y + TAM_TILE - k_surf.get_height() - 4
            self.tela.blit(bg_custo, (x + 2, cy))
            self.tela.blit(k_surf,   (x + 4, cy + 1))

    # ── barra de status ───────────────────────────────────────────────────────

    def _desenhar_status(self):
        larg, alt = self._larg, self._alt
        barra = pygame.Rect(0, alt - ALT_STATUS, larg, ALT_STATUS)
        pygame.draw.rect(self.tela, C_ESCURO, barra)
        pygame.draw.line(self.tela, C_OURO, (0, alt - ALT_STATUS), (larg, alt - ALT_STATUS))

        cor    = C_OURO2 if "OBJETIVO" in self._status else C_TEXTO
        t      = self.f_principal.render(self._status[:90], True, cor)
        sombra = self.f_principal.render(self._status[:90], True, (0, 0, 0))
        self.tela.blit(sombra, (13, alt - ALT_STATUS + 10))
        self.tela.blit(t,      (12, alt - ALT_STATUS + 9))

    # ── acoes ─────────────────────────────────────────────────────────────────

    def _mapa_aleatorio(self):
        if self._executando:
            return
        self.grafo.construir_aleatorio(linhas=8, colunas=8)
        self._recalcular_grade()
        self._destaque    = {}
        self._estado_anim = "ocioso"
        self._resultado   = None
        self._status      = "Novo mapa gerado. Pressione BUSCAR."

    def _resetar(self):
        if self._executando:
            return
        self.grafo.construir_do_mapa()
        self.grafo.resetar_recompensas()
        self._recalcular_grade()
        self._destaque    = {}
        self._estado_anim = "ocioso"
        self._resultado   = None
        self._status      = "Mapa resetado. Pressione BUSCAR."
