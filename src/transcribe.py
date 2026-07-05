"""Etapa 1 — Transcrição do episódio com Whisper local (faster-whisper).

Gera uma lista de segmentos com timestamps e o texto de cada trecho de fala.
Isso é a matéria-prima tanto pra separar os temas quanto pra legendar.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Palavra:
    inicio: float
    fim: float
    texto: str


@dataclass
class Segmento:
    inicio: float
    fim: float
    texto: str
    palavras: list[Palavra]

    def dict(self) -> dict:
        d = asdict(self)
        return d


def carregar_modelo(cfg: dict):
    """Carrega o modelo Whisper uma única vez (reutilizável entre vários cortes)."""
    from faster_whisper import WhisperModel

    wcfg = cfg["whisper"]
    print(f"[transcribe] Carregando modelo Whisper '{wcfg['modelo']}' "
          f"({wcfg['dispositivo']}/{wcfg['precisao']})...")
    return WhisperModel(
        wcfg["modelo"],
        device=wcfg["dispositivo"],
        compute_type=wcfg["precisao"],
    )


def transcrever_com_modelo(modelo, video: str, cfg: dict, silencioso: bool = False) -> list[Segmento]:
    """Transcreve um arquivo usando um modelo já carregado."""
    wcfg = cfg["whisper"]
    if not silencioso:
        print(f"[transcribe] Transcrevendo '{Path(video).name}'...")
    segmentos_raw, info = modelo.transcribe(
        video,
        language=wcfg.get("idioma", "pt"),
        word_timestamps=True,   # essencial pra legenda e pra cortar nos respiros
        vad_filter=True,        # filtra silêncios longos já na transcrição
    )

    segmentos: list[Segmento] = []
    for s in segmentos_raw:
        palavras = [
            Palavra(inicio=w.start, fim=w.end, texto=w.word)
            for w in (s.words or [])
            if w.start is not None and w.end is not None
        ]
        segmentos.append(
            Segmento(inicio=s.start, fim=s.end, texto=s.text.strip(), palavras=palavras)
        )
    return segmentos


def transcrever(video: str, cfg: dict) -> list[Segmento]:
    """Transcreve o áudio do vídeo e retorna segmentos com timestamps por palavra."""
    modelo = carregar_modelo(cfg)
    print(f"[transcribe] Isso pode levar alguns minutos...")
    segmentos = transcrever_com_modelo(modelo, video, cfg, silencioso=True)
    print(f"[transcribe] Pronto: {len(segmentos)} segmentos.")
    return segmentos
