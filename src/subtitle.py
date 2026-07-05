"""Etapa 4 — Geração de legendas (.srt) por corte.

A partir das palavras com timestamp da transcrição, monta linhas de legenda
curtas (estilo Reels) só para o intervalo de cada corte, rebaseando os tempos
para começarem do zero (já que cada corte vira um arquivo próprio).
"""
from __future__ import annotations

from .transcribe import Segmento


def _fmt_tempo(seg: float) -> str:
    """Converte segundos em timestamp SRT: HH:MM:SS,mmm."""
    if seg < 0:
        seg = 0
    ms = int(round(seg * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def gerar_srt(
    segmentos: list[Segmento],
    inicio: float,
    fim: float,
    max_chars: int,
) -> str:
    """Gera o conteúdo .srt para o trecho [inicio, fim], com tempos a partir do zero."""
    # Junta todas as palavras que caem dentro do corte.
    palavras = []
    for s in segmentos:
        for w in s.palavras:
            if w.inicio >= inicio and w.fim <= fim:
                palavras.append(w)

    # Agrupa palavras em linhas de legenda respeitando o limite de caracteres.
    linhas = []
    atual = []
    tam = 0
    for w in palavras:
        texto = w.texto.strip()
        if atual and tam + len(texto) + 1 > max_chars:
            linhas.append(atual)
            atual = []
            tam = 0
        atual.append(w)
        tam += len(texto) + 1
    if atual:
        linhas.append(atual)

    # Monta os blocos SRT com tempos rebaseados (corte começa em 0).
    blocos = []
    for i, grupo in enumerate(linhas, start=1):
        t_ini = grupo[0].inicio - inicio
        t_fim = grupo[-1].fim - inicio
        texto = " ".join(w.texto.strip() for w in grupo)
        blocos.append(f"{i}\n{_fmt_tempo(t_ini)} --> {_fmt_tempo(t_fim)}\n{texto}\n")

    return "\n".join(blocos)
