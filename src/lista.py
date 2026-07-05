"""Modo LISTA — recorta cortes a partir de timecodes já definidos (roteiro).

Diferente do cortar.py (que usa IA pra achar os temas), aqui os cortes já vêm
prontos num JSON: cada corte tem um ou mais trechos (segmentos) do vídeo master.
Trechos múltiplos são "costurados" (concatenados) — é assim que os cortes
cruzados juntam momentos diferentes num Reel só.

Para cada corte: extrai o(s) trecho(s), transcreve com Whisper pra gerar a
legenda .srt e (opcionalmente) queima a legenda no vídeo.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .cut import _slug
from .subtitle import gerar_srt
from .transcribe import carregar_modelo, transcrever_com_modelo


def _extrair_um(video: str, inicio: float, fim: float, destino: Path) -> None:
    """Extrai um trecho [inicio, fim] do vídeo, recodificando pra corte preciso."""
    dur = fim - inicio
    cmd = [
        "ffmpeg", "-y", "-ss", f"{inicio:.3f}", "-i", video, "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "160k", str(destino),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg falhou ao extrair {inicio}-{fim}:\n{proc.stderr[-600:]}")


def extrair_segmentos(video: str, segmentos: list[tuple[float, float]], destino: Path, tmpdir: str) -> None:
    """Gera o clipe do corte. Um segmento = extração direta; vários = costura (concat)."""
    if len(segmentos) == 1:
        s, e = segmentos[0]
        _extrair_um(video, s, e, destino)
        return

    partes = []
    for i, (s, e) in enumerate(segmentos):
        p = Path(tmpdir) / f"parte_{i}.mp4"
        _extrair_um(video, s, e, p)
        partes.append(p)

    lista_txt = Path(tmpdir) / "concat.txt"
    lista_txt.write_text(
        "".join(f"file '{p.resolve()}'\n" for p in partes), encoding="utf-8"
    )
    proc = subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista_txt),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-b:a", "160k", str(destino)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg falhou na costura:\n{proc.stderr[-600:]}")


def queimar_legenda(clip: Path, srt_path: Path, destino: Path, lcfg: dict) -> None:
    """Queima a legenda .srt no clipe (estilo Reels)."""
    estilo = (
        f"FontSize={lcfg['fonte_tamanho']},"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        "BorderStyle=1,Outline=2,Shadow=0"
    )
    srt_ff = str(srt_path).replace("\\", "/").replace(":", r"\:")
    proc = subprocess.run(
        ["ffmpeg", "-y", "-i", str(clip),
         "-vf", f"subtitles='{srt_ff}':force_style='{estilo}'",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-b:a", "160k", str(destino)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg falhou ao queimar legenda:\n{proc.stderr[-600:]}")


def processar_lista(cfg: dict, json_path: str) -> list[Path]:
    """Processa todos os cortes definidos no JSON. Retorna os arquivos gerados."""
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    video = data["video"]
    if not Path(video).exists():
        raise FileNotFoundError(
            f"Vídeo master não encontrado: '{video}'. "
            "Baixe o MP4 do Drive e ajuste o campo 'video' no JSON."
        )

    saida = Path(cfg["export"]["pasta_saida"])
    saida.mkdir(parents=True, exist_ok=True)
    lcfg = cfg["legendas"]
    maxc = lcfg["max_chars_linha"]
    cortes = data["cortes"]

    modelo = carregar_modelo(cfg)
    gerados: list[Path] = []

    for i, c in enumerate(cortes, start=1):
        n = c["n"]
        titulo = c["titulo"]
        segs = [(float(a), float(b)) for a, b in c["segmentos"]]
        dur = sum(e - s for s, e in segs)
        nome = f"{n}-{_slug(titulo)}"
        print(f"[lista] {i}/{len(cortes)} · corte {n}: {titulo} ({dur:.0f}s)")

        with tempfile.TemporaryDirectory() as td:
            clip = Path(td) / "clip.mp4"
            extrair_segmentos(video, segs, clip, td)

            transc = transcrever_com_modelo(modelo, str(clip), cfg, silencioso=True)
            srt = gerar_srt(transc, 0.0, dur + 1.0, maxc)
            srt_path = saida / f"{nome}.srt"
            srt_path.write_text(srt, encoding="utf-8")

            destino = saida / f"{nome}.mp4"
            if lcfg["queimar"]:
                queimar_legenda(clip, srt_path, destino, lcfg)
            else:
                shutil.copy(clip, destino)

        gerados.append(destino)

    print(f"[lista] {len(gerados)} cortes gerados em '{saida}'.")
    return gerados
