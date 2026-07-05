"""Carregamento da configuração do pipeline."""
from __future__ import annotations

import os
from pathlib import Path

import yaml


def carregar_config(caminho: str | None = None) -> dict:
    """Carrega config.local.yaml (se existir) ou config.example.yaml."""
    raiz = Path(__file__).resolve().parent.parent
    if caminho:
        arquivo = Path(caminho)
    else:
        local = raiz / "config.local.yaml"
        arquivo = local if local.exists() else raiz / "config.example.yaml"

    if not arquivo.exists():
        raise FileNotFoundError(
            f"Configuração não encontrada: {arquivo}. "
            "Copie config.example.yaml para config.local.yaml."
        )

    with open(arquivo, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    cfg["_raiz"] = str(raiz)
    return cfg


def ffmpeg_disponivel() -> bool:
    """Confere se ffmpeg/ffprobe estão no PATH."""
    from shutil import which

    return which("ffmpeg") is not None and which("ffprobe") is not None
