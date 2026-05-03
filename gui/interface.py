"""
gui/interface.py
-----------------
Interface gráfica principal do sistema de navegação.
Usa Tkinter com Canvas para renderizar o grid, animar o agente
e exibir métricas de desempenho dos algoritmos de busca.

Responsabilidades:
    - Renderizar o mapa com cores por terreno
    - Controles: seleção de algoritmo, mapa aleatório, reset
    - Animar o agente percorrendo o caminho encontrado
    - Exibir painel de métricas (custo, tempo, nós expandidos)
    - Destacar caminho, nós visitados e recompensas coletadas
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import threading

from core.graph import Graph
from core.node import Node
from core.terrain import Terrain, ELEMENT_COLORS
from algorithms.bfs import BFS
from algorithms.dfs import DFS
from algorithms.greedy import Greedy
from algorithms.astar import AStar
from utils.metrics import SearchResult
from utils.heuristics import manhattan, reward_adjusted


# ── Configurações visuais ───────────────────────────────────────────────────
CELL_SIZE    = 72   # tamanho de cada célula do grid em pixels
CELL_PAD     = 3    # espaçamento interno da célula
ANIM_DELAY   = 120  # delay entre frames da animação (ms)
VISIT_DELAY  = 18   # delay ao mostrar nós visitados (ms)

ALGORITHMS = {
    "BFS (Largura)":    "bfs",
    "DFS (Profundidade)": "dfs",
    "Greedy (Gulosa)":  "greedy",
    "A* (A estrela)":   "astar",
}

TERRAIN_LABELS = {
    Terrain.PLAIN: "Plano\ncusto 1",
    Terrain.SANDY: "Arenoso\ncusto 4",
    Terrain.ROCKY: "Rochoso\ncusto 10",
    Terrain.SWAMP: "Pântano\ncusto 20",
    Terrain.WALL:  "Parede",
}

FONT_MAIN  = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 13, "bold")
FONT_MONO  = ("Consolas", 10)
FONT_CELL  = ("Segoe UI", 8)

BG_APP    = "#1E1E2E"
BG_PANEL  = "#2A2A3E"
BG_CARD   = "#313145"
FG_TEXT   = "#CDD6F4"
FG_MUTED  = "#9399B2"
ACCENT    = "#89B4FA"
SUCCESS   = "#A6E3A1"
WARNING   = "#F9E2AF"
ERROR     = "#F38BA8"


class NavigationApp:
    """
    Janela principal da aplicação de navegação por algoritmos de busca.
    Gerencia o ciclo: construir mapa → selecionar algoritmo → buscar → animar.
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("🧭  Navegação com Algoritmos de Busca")
        self.root.configure(bg=BG_APP)
        self.root.resizable(True, True)

        self.graph = Graph()
        self.graph.build_from_map()

        self._result: Optional[SearchResult] = None
        self._anim_job: Optional[str] = None
        self._agent_pos: Optional[Node] = None
        self._collected_rewards: int = 0
        self._running: bool = False

        self._build_layout()
        self._draw_grid()
        self._update_vertex_count()

    # ── Layout principal ────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """Cria o layout principal: painel esquerdo de controles + canvas central."""

        # Frame esquerdo: controles + métricas
        left = tk.Frame(self.root, bg=BG_APP, width=240)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(12, 6), pady=12)
        left.pack_propagate(False)

        self._build_controls(left)
        self._build_legend(left)
        self._build_metrics_panel(left)

        # Frame central: canvas do grid
        center = tk.Frame(self.root, bg=BG_APP)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=12, padx=(0, 12))

        self._build_canvas(center)
        self._build_status_bar(center)

    def _build_controls(self, parent: tk.Frame) -> None:
        """Seção de controles: título, algoritmo, botões de ação."""
        card = self._card(parent, "⚙️  Controles")

        # Seletor de algoritmo
        tk.Label(card, text="Algoritmo:", bg=BG_CARD, fg=FG_MUTED,
                 font=FONT_MAIN).pack(anchor="w", padx=8, pady=(4, 0))

        self._algo_var = tk.StringVar(value="A* (A estrela)")
        combo = ttk.Combobox(card, textvariable=self._algo_var,
                             values=list(ALGORITHMS.keys()),
                             state="readonly", font=FONT_MAIN)
        combo.pack(fill=tk.X, padx=8, pady=4)

        # Heurística (somente informativa para BFS/DFS, ativa para Greedy/A*)
        tk.Label(card, text="Heurística:", bg=BG_CARD, fg=FG_MUTED,
                 font=FONT_MAIN).pack(anchor="w", padx=8, pady=(4, 0))

        self._heur_var = tk.StringVar(value="Manhattan")
        heur_combo = ttk.Combobox(card, textvariable=self._heur_var,
                                  values=["Manhattan", "Euclidiana", "Ajuste p/ recompensas"],
                                  state="readonly", font=FONT_MAIN)
        heur_combo.pack(fill=tk.X, padx=8, pady=4)

        # Botões
        btn_cfg = dict(font=FONT_BOLD, relief="flat", cursor="hand2",
                       padx=6, pady=6, bd=0)

        self._btn_search = tk.Button(
            card, text="▶  Iniciar Busca",
            bg=ACCENT, fg=BG_APP,
            command=self._start_search, **btn_cfg)
        self._btn_search.pack(fill=tk.X, padx=8, pady=(8, 3))

        tk.Button(card, text="🔀  Mapa Aleatório",
                  bg=BG_PANEL, fg=FG_TEXT,
                  command=self._random_map, **btn_cfg).pack(fill=tk.X, padx=8, pady=3)

        tk.Button(card, text="↺  Resetar",
                  bg=BG_PANEL, fg=FG_TEXT,
                  command=self._reset, **btn_cfg).pack(fill=tk.X, padx=8, pady=(3, 8))

        self._vertex_lbl = tk.Label(card, text="", bg=BG_CARD,
                                    fg=FG_MUTED, font=("Segoe UI", 8))
        self._vertex_lbl.pack(pady=(0, 6))

    def _build_legend(self, parent: tk.Frame) -> None:
        """Legenda de terrenos e elementos do mapa."""
        card = self._card(parent, "🗺️  Legenda")

        items = [
            (Terrain.PLAIN.color, "Plano (custo 1)"),
            (Terrain.SANDY.color, "Arenoso (custo 4)"),
            (Terrain.ROCKY.color, "Rochoso (custo 10)"),
            (Terrain.SWAMP.color, "Pântano (custo 20)"),
            (Terrain.WALL.color,  "Parede (intransponível)"),
            (ELEMENT_COLORS["goal"],    "🏆 Objetivo"),
            (ELEMENT_COLORS["reward"],  "💎 Recompensa"),
            (ELEMENT_COLORS["path"],    "Caminho encontrado"),
            (ELEMENT_COLORS["visited"], "Nós explorados"),
        ]

        for color, label in items:
            row = tk.Frame(card, bg=BG_CARD)
            row.pack(fill=tk.X, padx=8, pady=1)
            swatch = tk.Frame(row, bg=color, width=16, height=16, relief="flat")
            swatch.pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(row, text=label, bg=BG_CARD, fg=FG_TEXT,
                     font=("Segoe UI", 8)).pack(side=tk.LEFT)

    def _build_metrics_panel(self, parent: tk.Frame) -> None:
        """Painel de métricas: exibe resultados após a busca."""
        card = self._card(parent, "📊  Métricas")

        self._metrics_text = tk.Text(
            card, height=12, font=FONT_MONO,
            bg=BG_APP, fg=FG_TEXT, relief="flat",
            state="disabled", wrap="word",
            padx=6, pady=4)
        self._metrics_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self._set_metrics("Aguardando execução...\n\nSelecione um algoritmo\ne clique em Iniciar Busca.")

    def _build_canvas(self, parent: tk.Frame) -> None:
        """Canvas principal onde o grid é desenhado."""
        frame = tk.Frame(parent, bg=BG_PANEL, relief="flat", bd=1)
        frame.pack(fill=tk.BOTH, expand=True)

        canvas_w = self.graph.cols * CELL_SIZE
        canvas_h = self.graph.rows * CELL_SIZE

        self._canvas = tk.Canvas(
            frame, width=canvas_w, height=canvas_h,
            bg=BG_APP, highlightthickness=0)
        self._canvas.pack(padx=8, pady=8)

        # Scrollbars para mapas grandes
        hbar = tk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self._canvas.xview)
        vbar = tk.Scrollbar(parent, orient=tk.VERTICAL, command=self._canvas.yview)
        self._canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set,
                               scrollregion=(0, 0, canvas_w, canvas_h))

    def _build_status_bar(self, parent: tk.Frame) -> None:
        """Barra de status na parte inferior."""
        self._status_var = tk.StringVar(value="Pronto — selecione um algoritmo e inicie a busca.")
        bar = tk.Label(parent, textvariable=self._status_var,
                       bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 9),
                       anchor="w", padx=8, pady=4)
        bar.pack(fill=tk.X, pady=(4, 0))

    def _card(self, parent: tk.Frame, title: str) -> tk.Frame:
        """Cria um card com título e retorna o frame interno."""
        outer = tk.Frame(parent, bg=BG_CARD, relief="flat", bd=0)
        outer.pack(fill=tk.X, pady=(0, 8))

        tk.Label(outer, text=title, bg=BG_CARD, fg=ACCENT,
                 font=FONT_BOLD, anchor="w").pack(fill=tk.X, padx=8, pady=(8, 4))

        sep = tk.Frame(outer, bg=BG_PANEL, height=1)
        sep.pack(fill=tk.X, padx=8, pady=(0, 6))

        return outer

    # ── Renderização do grid ────────────────────────────────────────────────

    def _draw_grid(self) -> None:
        """Renderiza o grid completo a partir do estado atual do grafo."""
        self._canvas.delete("all")
        for row in self.graph.nodes:
            for node in row:
                self._draw_cell(node)

    def _draw_cell(self, node: Node,
                   override_color: Optional[str] = None,
                   tag: Optional[str] = None) -> None:
        """Desenha uma única célula no canvas."""
        x0 = node.col * CELL_SIZE + CELL_PAD
        y0 = node.row * CELL_SIZE + CELL_PAD
        x1 = x0 + CELL_SIZE - CELL_PAD * 2
        y1 = y0 + CELL_SIZE - CELL_PAD * 2

        # Cor da célula
        if override_color:
            color = override_color
        elif node.is_goal:
            color = ELEMENT_COLORS["goal"]
        elif node.is_start:
            color = ELEMENT_COLORS["agent"]
        else:
            color = node.terrain.color

        radius = 6
        self._rounded_rect(x0, y0, x1, y1, radius, fill=color, outline="", tags=tag or "")

        # Ícone central
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

        if node.is_start:
            self._canvas.create_text(cx, cy - 6, text="🤖", font=("Segoe UI", 16), tags=tag or "")
            self._canvas.create_text(cx, cy + 10, text="INÍCIO", font=("Segoe UI", 6, "bold"),
                                     fill=BG_APP, tags=tag or "")
        elif node.is_goal:
            self._canvas.create_text(cx, cy - 6, text="🏆", font=("Segoe UI", 16), tags=tag or "")
            self._canvas.create_text(cx, cy + 10, text="OBJETIVO", font=("Segoe UI", 6, "bold"),
                                     fill=BG_APP, tags=tag or "")
        elif node.terrain == Terrain.WALL:
            self._canvas.create_text(cx, cy, text="█", font=("Segoe UI", 18),
                                     fill="#111", tags=tag or "")
        else:
            # Ícone do terreno
            icons = {Terrain.PLAIN: "🌿", Terrain.SANDY: "🏜",
                     Terrain.ROCKY: "⛰", Terrain.SWAMP: "🌊"}
            icon = icons.get(node.terrain, "")
            self._canvas.create_text(cx, cy - 8, text=icon,
                                     font=("Segoe UI", 14), tags=tag or "")

            # Custo do terreno
            self._canvas.create_text(cx, cy + 10, text=f"c:{node.terrain.cost}",
                                     font=("Segoe UI", 7), fill="#555", tags=tag or "")

            # Recompensa
            if node.has_reward():
                self._canvas.create_text(cx + 18, cy - 18, text="💎",
                                         font=("Segoe UI", 11), tags=tag or "")
                self._canvas.create_text(cx + 18, cy - 4, text=f"+{node.reward}",
                                         font=("Segoe UI", 7, "bold"),
                                         fill=ELEMENT_COLORS["reward"], tags=tag or "")

        # Coordenadas discretas (canto superior esquerdo)
        self._canvas.create_text(x0 + 5, y0 + 5, text=f"{node.row},{node.col}",
                                 anchor="nw", font=("Segoe UI", 6),
                                 fill="#888", tags=tag or "")

    def _rounded_rect(self, x0, y0, x1, y1, r, **kwargs):
        """Desenha um retângulo com cantos arredondados no canvas."""
        pts = [
            x0+r, y0,   x1-r, y0,
            x1,   y0,   x1,   y0+r,
            x1,   y1-r, x1,   y1,
            x1-r, y1,   x0+r, y1,
            x0,   y1,   x0,   y1-r,
            x0,   y0+r, x0,   y0,
            x0+r, y0,
        ]
        return self._canvas.create_polygon(pts, smooth=True, **kwargs)

    # ── Ações do usuário ────────────────────────────────────────────────────

    def _start_search(self) -> None:
        """Executa o algoritmo selecionado e inicia a animação."""
        if self._running:
            return

        self._cancel_animation()
        self._draw_grid()  # limpa marcações anteriores
        self._collected_rewards = 0

        algo_key = ALGORITHMS.get(self._algo_var.get(), "astar")
        heuristic = self._get_heuristic()

        algorithm_map = {
            "bfs":    BFS(self.graph),
            "dfs":    DFS(self.graph),
            "greedy": Greedy(self.graph, heuristic),
            "astar":  AStar(self.graph, heuristic),
        }

        algo = algorithm_map[algo_key]
        self._status("⏳ Executando busca...")
        self._btn_search.config(state="disabled")
        self._running = True

        def run():
            result = algo.search(self.graph.start_node, self.graph.goal_node)
            self.root.after(0, lambda: self._on_search_complete(result))

        threading.Thread(target=run, daemon=True).start()

    def _get_heuristic(self):
        """Retorna a função de heurística selecionada."""
        choice = self._heur_var.get()
        if choice == "Euclidiana":
            from utils.heuristics import euclidean
            return euclidean
        elif choice == "Ajuste p/ recompensas":
            return reward_adjusted
        return manhattan

    def _on_search_complete(self, result: SearchResult) -> None:
        """Chamado quando a busca termina — inicia a animação."""
        self._result = result
        self._update_metrics(result)

        if not result.found:
            self._status(f"❌ {result.message}")
            self._btn_search.config(state="normal")
            self._running = False
            messagebox.showwarning("Busca", result.message)
            return

        self._status(f"✅ Caminho encontrado! Animando {len(result.path)} nós...")
        self._animate_visited(result.visited_order, result.path)

    def _animate_visited(self, visited: List[Node], path: List[Node]) -> None:
        """Anima os nós visitados (exploração) e depois o caminho final."""
        path_set = set(id(n) for n in path)
        idx = [0]

        def step():
            if idx[0] < len(visited):
                node = visited[idx[0]]
                if not node.is_start and not node.is_goal and id(node) not in path_set:
                    self._redraw_cell(node, ELEMENT_COLORS["visited"])
                idx[0] += 1
                self._anim_job = self.root.after(VISIT_DELAY, step)
            else:
                self._animate_path(path)

        step()

    def _animate_path(self, path: List[Node]) -> None:
        """Destaca o caminho e depois anima o agente percorrendo-o."""
        # Destaca células do caminho
        for node in path:
            if not node.is_start and not node.is_goal:
                self._redraw_cell(node, ELEMENT_COLORS["path"])

        self.root.after(300, lambda: self._animate_agent(path, 0))

    def _animate_agent(self, path: List[Node], idx: int) -> None:
        """Move o agente passo a passo pelo caminho."""
        if idx >= len(path):
            self._status(f"🎉 Concluído! Recompensas coletadas: +{self._collected_rewards}")
            self._btn_search.config(state="normal")
            self._running = False
            return

        node = path[idx]

        # Apaga posição anterior do agente (restaura cor do caminho)
        if idx > 0:
            prev = path[idx - 1]
            if not prev.is_start and not prev.is_goal:
                self._redraw_cell(prev, ELEMENT_COLORS["path"])

        # Coleta recompensa ao passar pelo nó
        if node.has_reward():
            self._collected_rewards += node.reward
            self.graph.collect_reward(node)

        # Desenha agente na posição atual
        self._draw_agent(node)
        self._status(f"🤖 Passo {idx+1}/{len(path)} | "
                     f"Recompensas: +{self._collected_rewards}")

        self._anim_job = self.root.after(
            ANIM_DELAY, lambda: self._animate_agent(path, idx + 1))

    def _draw_agent(self, node: Node) -> None:
        """Desenha o ícone do agente em um nó específico."""
        x0 = node.col * CELL_SIZE + CELL_PAD
        y0 = node.row * CELL_SIZE + CELL_PAD
        x1 = x0 + CELL_SIZE - CELL_PAD * 2
        y1 = y0 + CELL_SIZE - CELL_PAD * 2
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

        self._canvas.delete(f"agent_{node.row}_{node.col}")
        tag = f"agent_{node.row}_{node.col}"

        self._rounded_rect(x0, y0, x1, y1, 6,
                           fill=ELEMENT_COLORS["agent"], outline="", tags=tag)
        self._canvas.create_text(cx, cy, text="🤖",
                                 font=("Segoe UI", 20), tags=tag)

    def _redraw_cell(self, node: Node, color: str) -> None:
        """Redesenha uma célula com cor de destaque (sem apagar o grid inteiro)."""
        x0 = node.col * CELL_SIZE + CELL_PAD
        y0 = node.row * CELL_SIZE + CELL_PAD
        x1 = x0 + CELL_SIZE - CELL_PAD * 2
        y1 = y0 + CELL_SIZE - CELL_PAD * 2
        tag = f"cell_{node.row}_{node.col}"
        self._canvas.delete(tag)
        self._draw_cell(node, override_color=color, tag=tag)

    def _random_map(self) -> None:
        """Gera um mapa aleatório e redesenha o grid."""
        self._cancel_animation()
        self._running = False
        self.graph.build_random(rows=8, cols=8)
        self._resize_canvas()
        self._draw_grid()
        self._update_vertex_count()
        self._set_metrics("Mapa aleatório gerado.\nClique em Iniciar Busca.")
        self._status("🔀 Novo mapa gerado — pronto para busca.")
        self._btn_search.config(state="normal")

    def _reset(self) -> None:
        """Reseta o mapa padrão e limpa o estado."""
        self._cancel_animation()
        self._running = False
        self.graph.build_from_map()
        self.graph.reset_rewards()
        self._resize_canvas()
        self._draw_grid()
        self._update_vertex_count()
        self._set_metrics("Mapa resetado.\nClique em Iniciar Busca.")
        self._status("↺ Mapa padrão restaurado.")
        self._btn_search.config(state="normal")

    def _cancel_animation(self) -> None:
        """Cancela qualquer animação em andamento."""
        if self._anim_job:
            self.root.after_cancel(self._anim_job)
            self._anim_job = None

    def _resize_canvas(self) -> None:
        """Redimensiona o canvas para o novo tamanho do grafo."""
        w = self.graph.cols * CELL_SIZE
        h = self.graph.rows * CELL_SIZE
        self._canvas.config(width=w, height=h,
                            scrollregion=(0, 0, w, h))

    # ── Utilitários de UI ───────────────────────────────────────────────────

    def _update_metrics(self, result: SearchResult) -> None:
        """Atualiza o painel de métricas com o SearchResult."""
        color = SUCCESS if result.found else ERROR
        self._set_metrics(result.summary(), color)

    def _set_metrics(self, text: str, color: str = FG_TEXT) -> None:
        """Escreve texto no painel de métricas."""
        self._metrics_text.config(state="normal")
        self._metrics_text.delete("1.0", tk.END)
        self._metrics_text.insert(tk.END, text)
        self._metrics_text.config(state="disabled", fg=color)

    def _status(self, msg: str) -> None:
        """Atualiza a barra de status inferior."""
        self._status_var.set(msg)

    def _update_vertex_count(self) -> None:
        """Exibe o número de vértices transitáveis no mapa."""
        count = self.graph.vertex_count()
        self._vertex_lbl.config(text=f"Vértices transitáveis: {count}")
