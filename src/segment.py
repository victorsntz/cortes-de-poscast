"""Etapa 3 — Separação por tema (os "20 assuntos").

Manda a transcrição (com timestamps) pra um LLM e pede pra ele identificar onde
cada assunto começa e termina, dando um título curto a cada corte. Por padrão usa
um modelo LOCAL via Ollama (grátis); dá pra trocar pra API da Anthropic no config.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

import requests

from .transcribe import Segmento


@dataclass
class Tema:
    titulo: str
    inicio: float
    fim: float
    resumo: str = ""


def _transcricao_indexada(segmentos: list[Segmento]) -> str:
    """Monta um texto com marcadores de tempo pro LLM raciocinar sobre a linha do tempo."""
    linhas = []
    for s in segmentos:
        linhas.append(f"[{s.inicio:.1f}s] {s.texto}")
    return "\n".join(linhas)


_PROMPT = """Você é um editor de podcast. Abaixo está a transcrição de um episódio, \
com marcadores de tempo em segundos no formato [123.4s].

Sua tarefa: dividir a conversa em blocos por ASSUNTO. Cada bloco deve ser um tema \
coeso e autossuficiente (que faça sentido como um corte isolado pra redes sociais). \
O episódio tem cerca de {alvo} temas. Cada corte deve durar entre {dmin} e {dmax} segundos.

Para cada tema, devolva:
- "titulo": título curto e chamativo (máx. 8 palavras)
- "inicio": tempo em segundos onde o assunto começa (use os marcadores)
- "fim": tempo em segundos onde o assunto termina
- "resumo": uma frase resumindo o corte

Responda APENAS com um JSON válido no formato:
{{"temas": [{{"titulo": "...", "inicio": 0.0, "fim": 0.0, "resumo": "..."}}]}}

Transcrição:
{transcricao}
"""


def _chamar_ollama(prompt: str, cfg: dict) -> str:
    tcfg = cfg["temas"]
    url = tcfg["ollama_url"].rstrip("/") + "/api/generate"
    resp = requests.post(
        url,
        json={
            "model": tcfg["modelo"],
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
        },
        timeout=1200,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def _chamar_anthropic(prompt: str, cfg: dict) -> str:
    chave = os.environ.get("ANTHROPIC_API_KEY")
    if not chave:
        raise RuntimeError("Defina ANTHROPIC_API_KEY para usar o provedor 'anthropic'.")
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": chave,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": cfg["temas"]["anthropic_modelo"],
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=600,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def separar_temas(segmentos: list[Segmento], cfg: dict) -> list[Tema]:
    """Identifica os temas do episódio e retorna a lista de cortes por assunto."""
    tcfg = cfg["temas"]
    prompt = _PROMPT.format(
        alvo=tcfg["temas_alvo"],
        dmin=tcfg["duracao_min"],
        dmax=tcfg["duracao_max"],
        transcricao=_transcricao_indexada(segmentos),
    )

    provedor = tcfg["provedor"]
    print(f"[temas] Separando por assunto via '{provedor}' ({tcfg['modelo']})...")
    if provedor == "ollama":
        bruto = _chamar_ollama(prompt, cfg)
    elif provedor == "anthropic":
        bruto = _chamar_anthropic(prompt, cfg)
    else:
        raise ValueError(f"Provedor de temas desconhecido: {provedor}")

    dados = _extrair_json(bruto)
    temas = [
        Tema(
            titulo=t["titulo"].strip(),
            inicio=float(t["inicio"]),
            fim=float(t["fim"]),
            resumo=t.get("resumo", "").strip(),
        )
        for t in dados.get("temas", [])
        if float(t["fim"]) > float(t["inicio"])
    ]
    print(f"[temas] {len(temas)} temas identificados.")
    return temas


def _extrair_json(texto: str) -> dict:
    """Tenta parsear JSON mesmo que o modelo enrole com texto em volta."""
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        ini = texto.find("{")
        fim = texto.rfind("}")
        if ini != -1 and fim != -1:
            return json.loads(texto[ini : fim + 1])
        raise
