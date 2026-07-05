#!/usr/bin/env python3
"""Cortes de Podcast — automação ponta a ponta.

Uso:
    python cortar.py entrada/episodio.mp4
    python cortar.py entrada/episodio.mp4 --config config.local.yaml

Fluxo:
    1. Transcreve o episódio (Whisper local)
    2. Detecta os respiros (silêncios) com ffmpeg
    3. Separa a conversa em temas/assuntos (LLM)
    4. Gera legendas por corte
    5. Recorta cada tema em MP4 (legenda queimada opcional)
    6. (opcional) Sobe os cortes pro Google Drive via rclone
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.config import carregar_config, ffmpeg_disponivel
from src.cut import cortar_temas
from src.drive_export import enviar_para_drive
from src.segment import separar_temas
from src.silence import detectar_respiros
from src.transcribe import transcrever


def main() -> int:
    parser = argparse.ArgumentParser(description="Cortes automáticos de podcast por tema.")
    parser.add_argument("video", help="Caminho do vídeo do episódio (MP4).")
    parser.add_argument("--config", help="Caminho do arquivo de config (YAML).")
    args = parser.parse_args()

    video = Path(args.video)
    if not video.exists():
        print(f"Vídeo não encontrado: {video}")
        return 1

    if not ffmpeg_disponivel():
        print("ffmpeg/ffprobe não encontrados no PATH. Instale o ffmpeg antes de rodar.")
        return 1

    cfg = carregar_config(args.config)

    # 1. Transcrição
    segmentos = transcrever(str(video), cfg)
    if not segmentos:
        print("Nenhuma fala transcrita. Abortando.")
        return 1

    # 2. Respiros
    respiros = detectar_respiros(str(video), cfg)

    # 3. Temas
    temas = separar_temas(segmentos, cfg)
    if not temas:
        print("Nenhum tema identificado. Confira o provedor de LLM no config.")
        return 1

    # Salva o "mapa" de temas pra referência/ajuste manual.
    saida = Path(cfg["export"]["pasta_saida"])
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "temas.json").write_text(
        json.dumps([t.__dict__ for t in temas], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 4 + 5. Legendas e cortes
    cortar_temas(str(video), temas, segmentos, respiros, cfg)

    # 6. Export
    enviar_para_drive(cfg)

    print("\n✅ Concluído! Confira os cortes em:", saida.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
