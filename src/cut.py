"""Etapa 5 — Recorte dos vídeos com ffmpeg (+ legenda queimada, opcional).

Para cada tema: ajusta o início/fim para cair num respiro, gera o .srt do trecho
e chama o ffmpeg pra cortar. Se `legendas.queimar` for true, a legenda é embutida
na imagem (ideal pra Reels/Shorts/TikTok).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .segment import Tema
from .silence import ajustar_para_respiro
from .subtitle import gerar_srt
from .transcribe import Segmento


def _slug(texto: str) -> str:
    s = re.sub(r"[^\w\s-]", "", texto.lower())
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s[:50] or "corte"


def cortar_temas(
    video: str,
    temas: list[Tema],
    segmentos: list[Segmento],
    respiros: list[tuple[float, float]],
    cfg: dict,
) -> list[Path]:
    """Gera um arquivo de vídeo por tema. Retorna os caminhos gerados."""
    saida = Path(cfg["export"]["pasta_saida"])
    saida.mkdir(parents=True, exist_ok=True)

    margem = cfg["respiros"]["margem"]
    lcfg = cfg["legendas"]
    gerados: list[Path] = []

    for i, tema in enumerate(temas, start=1):
        ini = ajustar_para_respiro(tema.inicio, respiros, margem, "inicio")
        fim = ajustar_para_respiro(tema.fim, respiros, margem, "fim")
        if fim <= ini:
            print(f"[corte] Pulando '{tema.titulo}' (intervalo inválido).")
            continue

        nome = f"{i:02d}-{_slug(tema.titulo)}"
        destino = saida / f"{nome}.mp4"
        print(f"[corte] {i}/{len(temas)} '{tema.titulo}' "
              f"({ini:.1f}s → {fim:.1f}s, {fim-ini:.0f}s)")

        srt = gerar_srt(segmentos, ini, fim, lcfg["max_chars_linha"])
        srt_path = saida / f"{nome}.srt"
        srt_path.write_text(srt, encoding="utf-8")

        _rodar_ffmpeg(video, ini, fim, destino, srt_path, lcfg)
        gerados.append(destino)

    print(f"[corte] {len(gerados)} cortes gerados em '{saida}'.")
    return gerados


def _rodar_ffmpeg(
    video: str,
    inicio: float,
    fim: float,
    destino: Path,
    srt_path: Path,
    lcfg: dict,
) -> None:
    dur = fim - inicio
    cmd = ["ffmpeg", "-y", "-ss", f"{inicio:.3f}", "-i", video, "-t", f"{dur:.3f}"]

    if lcfg["queimar"]:
        # Queima a legenda na imagem. Precisa recodificar o vídeo.
        estilo = (
            f"FontSize={lcfg['fonte_tamanho']},"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            "BorderStyle=1,Outline=2,Shadow=0"
        )
        # Escapa o caminho do .srt pro filtro do ffmpeg.
        srt_ff = str(srt_path).replace("\\", "/").replace(":", r"\:")
        cmd += [
            "-vf", f"subtitles='{srt_ff}':force_style='{estilo}'",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "128k",
        ]
    else:
        # Sem queimar: corte rápido copiando os streams (não recodifica).
        cmd += ["-c", "copy"]

    cmd.append(str(destino))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[corte] ERRO no ffmpeg para '{destino.name}':\n{proc.stderr[-800:]}")
