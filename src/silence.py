"""Etapa 2 — Detecção de respiros (silêncios) com ffmpeg.

Usa o filtro `silencedetect` do ffmpeg pra achar as pausas naturais da conversa.
Esses respiros servem como "pontos de corte seguros": a gente ajusta o início e o
fim de cada tema pra cair num respiro, evitando cortar no meio de uma palavra.
"""
from __future__ import annotations

import re
import subprocess


def detectar_respiros(video: str, cfg: dict) -> list[tuple[float, float]]:
    """Retorna lista de (inicio, fim) de cada silêncio detectado, em segundos."""
    rcfg = cfg["respiros"]
    ruido = rcfg["ruido_db"]
    dur_min = rcfg["duracao_minima"]

    print(f"[respiros] Procurando silêncios (< {ruido}dB por >= {dur_min}s)...")
    cmd = [
        "ffmpeg", "-i", video,
        "-af", f"silencedetect=noise={ruido}dB:d={dur_min}",
        "-f", "null", "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    saida = proc.stderr  # silencedetect escreve no stderr

    inicios = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", saida)]
    fins = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", saida)]

    respiros = list(zip(inicios, fins))
    print(f"[respiros] {len(respiros)} respiros encontrados.")
    return respiros


def ajustar_para_respiro(
    tempo: float,
    respiros: list[tuple[float, float]],
    margem: float,
    tipo: str = "inicio",
) -> float:
    """Empurra um tempo de corte pro respiro mais próximo, pra cortar no silêncio.

    tipo="inicio": corta no FIM do respiro anterior (começa logo após a pausa).
    tipo="fim":    corta no INÍCIO do respiro seguinte (termina antes da próxima fala).
    """
    if not respiros:
        return tempo

    melhor = tempo
    menor_dist = float("inf")
    for ini, fim in respiros:
        ponto = fim if tipo == "inicio" else ini
        dist = abs(ponto - tempo)
        # Só considera respiros próximos (até 3s) pra não deslocar demais o corte.
        if dist < menor_dist and dist <= 3.0:
            menor_dist = dist
            melhor = ponto

    if tipo == "inicio":
        return max(0.0, melhor - margem)
    return melhor + margem
