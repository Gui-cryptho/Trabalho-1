# utils/audio.py — musica 8-bit gerada proceduralmente + efeitos sonoros
# musica de fundo em La menor via numpy (onda quadrada, triangular e pulso)
# efeitos sonoros do pack Kenney RPG Audio (CC0)
# tecla M: muta/desmuta

import os
import wave
import numpy as np
import pygame
from typing import Optional, List

TAXA_AMOSTRAGEM = 44100
CANAIS = 2
BIT    = -16   # signed 16-bit

_ROOT      = os.path.dirname(os.path.dirname(__file__))
DIR_AUDIO  = os.path.join(_ROOT, 'assets', 'audio')
CAMINHO_MUSICA = os.path.join(DIR_AUDIO, 'bgm.wav')


# ── frequencias (La menor) ────────────────────────────────────────────────────
FREQUENCIAS = {
    'A1': 55.00,  'D2': 73.42,  'E2': 82.41,  'F2': 87.31,  'G2': 98.00,
    'A2': 110.00, 'B2': 123.47, 'C3': 130.81, 'D3': 146.83,
    'E3': 164.81, 'F3': 174.61, 'G3': 196.00, 'A3': 220.00,
    'B3': 246.94, 'C4': 261.63, 'D4': 293.66, 'E4': 329.63,
    'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'A5': 880.00,
    'R' :   0.0,
}

BPM     = 118
_BATIDA = 60.0 / BPM


# ── geradores de onda ─────────────────────────────────────────────────────────

def _envelope(n: int) -> np.ndarray:
    desvanecimento = min(int(TAXA_AMOSTRAGEM * 0.007), n // 4)
    env = np.ones(n)
    if desvanecimento:
        env[:desvanecimento]  = np.linspace(0, 1, desvanecimento)
        env[-desvanecimento:] = np.linspace(1, 0, desvanecimento)
    return env

def _onda_quadrada(freq: float, dur: float, vol: float = 0.26) -> np.ndarray:
    n = int(TAXA_AMOSTRAGEM * dur)
    if freq == 0 or n == 0:
        return np.zeros(n)
    t = np.arange(n) / TAXA_AMOSTRAGEM
    return np.sign(np.sin(2 * np.pi * freq * t)) * _envelope(n) * vol

def _onda_triangular(freq: float, dur: float, vol: float = 0.20) -> np.ndarray:
    n = int(TAXA_AMOSTRAGEM * dur)
    if freq == 0 or n == 0:
        return np.zeros(n)
    t = np.arange(n) / TAXA_AMOSTRAGEM
    return (2 * np.abs(2 * (freq * t % 1) - 1) - 1) * _envelope(n) * vol

def _onda_pulso(freq: float, dur: float, ciclo: float = 0.25, vol: float = 0.15) -> np.ndarray:
    n = int(TAXA_AMOSTRAGEM * dur)
    if freq == 0 or n == 0:
        return np.zeros(n)
    t = np.arange(n) / TAXA_AMOSTRAGEM
    return np.where((freq * t % 1) < ciclo, 1.0, -1.0) * _envelope(n) * vol

def _sequenciar(notas, funcao_onda) -> np.ndarray:
    return np.concatenate([funcao_onda(FREQUENCIAS[n], b * _BATIDA) for n, b in notas])


# ── partitura (La menor, 8 compassos 4/4) ────────────────────────────────────

_MELODIA = [
    ('A3', .5), ('C4', .5), ('E4', .75), ('G4', .25), ('E4', .5), ('D4', .5), ('C4', .5), ('B3', .5),
    ('A3', 1.), ('R',  .5), ('E3', .5), ('G3', .5), ('A3', .5), ('C4', .5), ('B3', .5),
    ('A3', .5), ('B3', .25), ('C4', .25), ('D4', .5), ('E4', .5), ('F4', .5), ('E4', .5), ('D4', .5), ('C4', .5),
    ('B3', .5), ('A3', 1.), ('R', .5), ('E3', .5), ('G3', .5),
    ('F3', .5), ('A3', .5), ('C4', .5), ('E4', .5), ('F4', .25), ('E4', .25), ('D4', .5), ('C4', .5), ('B3', .5),
    ('A3', .5), ('G3', .5), ('F3', .5), ('E3', .5), ('D3', .5), ('E3', .5), ('F3', .5), ('G3', .5),
    ('A3', .25), ('B3', .25), ('C4', .25), ('D4', .25), ('E4', .5), ('G4', .5), ('E4', .5), ('C4', .25), ('B3', .25),
    ('A3', 1.5), ('E3', .5), ('A3', 1.), ('R', 1.),
]

_BAIXO = [
    ('A2', 1.), ('E2', 1.), ('A2', .5), ('E2', .5),
    ('A2', 1.), ('G2', .5), ('A2', .5), ('C3', .5), ('E3', .5),
    ('D2', 1.), ('A2', 1.), ('D2', .5), ('A2', .5),
    ('E2', 1.), ('B2', .5), ('E2', .5), ('G2', .5), ('B2', .5),
    ('F2', 1.), ('C3', 1.), ('F2', .5), ('C3', .5),
    ('D2', 1.), ('A2', 1.), ('D2', .5), ('E2', .5),
    ('G2', 1.), ('D3', 1.), ('G2', .5), ('B2', .5),
    ('A2', 1.5), ('E2', .5), ('A2', 1.), ('R', 1.),
]

_CONTRAPONTO = [
    ('A4', .5), ('R', .5), ('E4', .5), ('R', .5), ('G4', .5), ('R', .5), ('A4', .5), ('R', .5),
    ('G4', .5), ('R', .5), ('F4', .5), ('R', .5), ('E4', .5), ('R', .5), ('D4', .5), ('R', .5),
    ('F4', .5), ('R', .5), ('E4', .5), ('R', .5), ('D4', .5), ('R', 1.5),
    ('E4', .5), ('R', .5), ('D4', .5), ('R', .5), ('C4', .5), ('R', 1.5),
    ('A4', .5), ('R', .5), ('C5', .5), ('R', .5), ('E5', .5), ('R', .5), ('C5', .5), ('R', .5),
    ('B4', .5), ('R', .5), ('G4', .5), ('R', .5), ('F4', .5), ('R', .5), ('E4', .5), ('R', .5),
    ('G4', .5), ('R', .5), ('B4', .5), ('R', .5), ('D5', .5), ('R', .5), ('B4', .5), ('R', .5),
    ('A4', 1.), ('R', 1.), ('E4', 1.), ('R', 1.),
]


def _gerar_musica_fundo() -> np.ndarray:
    melodia     = _sequenciar(_MELODIA,     lambda f, d: _onda_quadrada(f, d, 0.26))
    baixo       = _sequenciar(_BAIXO,       lambda f, d: _onda_triangular(f, d, 0.19))
    contraponto = _sequenciar(_CONTRAPONTO, lambda f, d: _onda_pulso(f, d, 0.25, 0.13))

    n = max(len(melodia), len(baixo), len(contraponto))
    melodia     = np.pad(melodia,     (0, n - len(melodia)))
    baixo       = np.pad(baixo,       (0, n - len(baixo)))
    contraponto = np.pad(contraponto, (0, n - len(contraponto)))

    mistura = melodia + baixo + contraponto
    pico = np.max(np.abs(mistura))
    if pico > 0:
        mistura = mistura / pico * 0.82
    return mistura


def _salvar_wav(array: np.ndarray, caminho: str):
    s16    = (array * 32767).clip(-32767, 32767).astype(np.int16)
    stereo = np.column_stack([s16, s16])
    with wave.open(caminho, 'w') as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(TAXA_AMOSTRAGEM)
        f.writeframes(stereo.tobytes())


def gerar_musica_se_necessario():
    os.makedirs(DIR_AUDIO, exist_ok=True)
    if not os.path.exists(CAMINHO_MUSICA):
        _salvar_wav(_gerar_musica_fundo(), CAMINHO_MUSICA)


# ── efeitos sonoros gerados ───────────────────────────────────────────────────

def _criar_som(array: np.ndarray) -> pygame.mixer.Sound:
    s16    = (array * 32767).clip(-32767, 32767).astype(np.int16)
    stereo = np.column_stack([s16, s16])
    return pygame.sndarray.make_sound(stereo)

def _sfx_clique() -> pygame.mixer.Sound:
    n = int(TAXA_AMOSTRAGEM * 0.05)
    t = np.arange(n) / TAXA_AMOSTRAGEM
    return _criar_som(np.sign(np.sin(2 * np.pi * 900 * t)) * np.linspace(0.3, 0, n))

def _sfx_erro() -> pygame.mixer.Sound:
    a = _onda_quadrada(220, 0.07, 0.35)
    b = _onda_quadrada(165, 0.10, 0.28)
    return _criar_som(np.concatenate([a, b]))

def _sfx_vitoria() -> pygame.mixer.Sound:
    notas = [('A3', .10), ('C4', .10), ('E4', .10), ('A4', .10), ('E4', .08), ('A4', .30)]
    return _criar_som(_sequenciar(notas, lambda f, d: _onda_quadrada(f, d, 0.38)))

def _sfx_iniciar() -> pygame.mixer.Sound:
    notas = [('E4', .07), ('A4', .14)]
    return _criar_som(_sequenciar(notas, lambda f, d: _onda_quadrada(f, d, 0.30)))


class GerenciadorAudio:
    # inicializa mixer, toca musica em loop e gerencia efeitos sonoros

    def __init__(self):
        gerar_musica_se_necessario()
        pygame.mixer.music.load(CAMINHO_MUSICA)
        pygame.mixer.music.set_volume(0.42)
        pygame.mixer.music.play(-1)

        self._efeitos: dict = {
            'clique':    self._carregar_ogg('metalClick.ogg',  _sfx_clique),
            'erro':      self._carregar_ogg('metalLatch.ogg',  _sfx_erro),
            'vitoria':   _sfx_vitoria(),
            'iniciar':   self._carregar_ogg('doorOpen_1.ogg',  _sfx_iniciar),
            'moeda':     self._carregar_ogg('handleCoins.ogg', None),
            'moeda2':    self._carregar_ogg('handleCoins2.ogg',None),
            'passos':    [self._carregar_ogg(f'footstep0{i}.ogg', None) for i in range(5)],
        }
        self._idx_passo = 0
        self._mudo      = False

    def _carregar_ogg(self, nome_arquivo: str, alternativa) -> Optional[pygame.mixer.Sound]:
        caminho = os.path.join(DIR_AUDIO, nome_arquivo)
        if os.path.exists(caminho):
            try:
                return pygame.mixer.Sound(caminho)
            except Exception:
                pass
        return alternativa() if alternativa else None

    def reproduzir(self, nome: str):
        if self._mudo:
            return
        if nome == 'passo':
            validos = [s for s in self._efeitos['passos'] if s]
            if validos:
                s = validos[self._idx_passo % len(validos)]
                self._idx_passo += 1
                s.set_volume(0.30)
                s.play()
        elif nome == 'recompensa':
            s = self._efeitos['moeda'] if self._idx_passo % 2 == 0 else self._efeitos['moeda2']
            if s:
                s.set_volume(0.55)
                s.play()
        else:
            s = self._efeitos.get(nome)
            if s:
                s.set_volume(0.60)
                s.play()

    def alternar_mudo(self):
        self._mudo = not self._mudo
        if self._mudo:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()

    @property
    def mudo(self) -> bool:
        return self._mudo
