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


def transcrever(video: str, cfg: dict) -> list[Segmento]:
    """Transcreve o áudio do vídeo e retorna segmentos com timestamps por palavra."""
    from faster_whisper import WhisperModel

    wcfg = cfg["whisper"]
    print(f"[transcribe] Carregando modelo Whisper '{wcfg['modelo']}' "
          f"({wcfg['dispositivo']}/{wcfg['precisao']})...")

    modelo = WhisperModel(
        wcfg["modelo"],
        device=wcfg["dispositivo"],
        compute_type=wcfg["precisao"],
    )

    print(f"[transcribe] Transcrevendo '{Path(video).name}' — isso pode levar alguns minutos...")
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

    dur = info.duration if info else 0
    print(f"[transcribe] Pronto: {len(segmentos)} segmentos, ~{dur/60:.1f} min de áudio.")
    return segmentos
