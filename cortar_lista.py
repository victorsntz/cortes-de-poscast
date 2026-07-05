#!/usr/bin/env python3
"""Cortes de Podcast — modo LISTA (timecodes já definidos no roteiro).

Use quando você JÁ tem a minutagem de cada corte (ex.: exportado de um roteiro).
Corta os clipes exatos, gera legenda por corte e queima no vídeo (config).

Uso:
    python cortar_lista.py cortes/gorayeb-ep01.json
    python cortar_lista.py cortes/gorayeb-ep01.json --config config.local.yaml

O JSON aponta pro vídeo master e lista os cortes. Baixe o MP4 do Drive antes e
confira o campo "video" no JSON.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.config import carregar_config, ffmpeg_disponivel
from src.drive_export import enviar_para_drive
from src.lista import processar_lista


def main() -> int:
    parser = argparse.ArgumentParser(description="Recorta cortes a partir de uma lista de timecodes.")
    parser.add_argument("lista", help="Caminho do JSON de cortes (ex.: cortes/gorayeb-ep01.json).")
    parser.add_argument("--config", help="Caminho do arquivo de config (YAML).")
    args = parser.parse_args()

    if not Path(args.lista).exists():
        print(f"Lista não encontrada: {args.lista}")
        return 1

    if not ffmpeg_disponivel():
        print("ffmpeg/ffprobe não encontrados no PATH. Instale o ffmpeg antes de rodar.")
        return 1

    cfg = carregar_config(args.config)
    gerados = processar_lista(cfg, args.lista)
    if not gerados:
        print("Nenhum corte gerado.")
        return 1

    enviar_para_drive(cfg)
    print(f"\n✅ Concluído! {len(gerados)} cortes em:", Path(cfg["export"]["pasta_saida"]).resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
