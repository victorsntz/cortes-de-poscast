"""Etapa 6 — Envio dos cortes para o Google Drive via rclone (opcional).

O rclone é uma ferramenta aberta e madura pra sincronizar pastas com dezenas de
nuvens, incluindo o Google Drive. Configure uma vez (`rclone config`) e o pipeline
sobe os cortes automaticamente. Veja o README para o passo a passo.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from shutil import which


def enviar_para_drive(cfg: dict) -> None:
    ecfg = cfg["export"]
    if not ecfg.get("enviar_drive"):
        return

    if which("rclone") is None:
        print("[drive] rclone não encontrado no PATH. Pulei o envio. "
              "Instale em https://rclone.org e rode `rclone config`.")
        return

    origem = Path(ecfg["pasta_saida"])
    destino = f"{ecfg['rclone_remote']}:{ecfg['rclone_pasta']}"
    print(f"[drive] Enviando '{origem}' → '{destino}'...")

    proc = subprocess.run(
        ["rclone", "copy", str(origem), destino, "--progress"],
        text=True,
    )
    if proc.returncode == 0:
        print("[drive] Envio concluído.")
    else:
        print(f"[drive] rclone retornou erro (código {proc.returncode}).")
