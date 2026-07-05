# 🎙️ Cortes de Podcast — automação por tema

Pipeline em Python que pega um episódio de podcast em vídeo (2h, por exemplo) e,
de forma automática:

1. **Transcreve** a conversa inteira (Whisper, rodando na sua máquina)
2. **Detecta os respiros** (silêncios) pra cortar limpo, sem picotar no meio da fala
3. **Separa por assunto** — divide a conversa em ~20 temas coesos usando um LLM
4. **Legenda** cada corte (arquivo `.srt` ou legenda queimada no vídeo)
5. **Recorta** cada tema num MP4 pronto pra Reels / Shorts / TikTok
6. **Exporta** os cortes pro Google Drive (opcional, via rclone)

Tudo com ferramentas **abertas e locais** — o custo por episódio é praticamente zero.

---

## 🧩 Como funciona (a "receita")

```
episódio.mp4
     │
     ▼
[1] Whisper  ──►  transcrição com timestamp por palavra
     │
     ▼
[2] ffmpeg silencedetect  ──►  lista de respiros (pausas)
     │
     ▼
[3] LLM (Ollama local)  ──►  20 temas: título + início + fim
     │
     ▼
[4] gerador de .srt  ──►  legenda de cada corte
     │
     ▼
[5] ffmpeg  ──►  20 MP4s cortados (legenda queimada opcional)
     │
     ▼
[6] rclone  ──►  Google Drive
```

Cada etapa é um módulo isolado em `src/`, então dá pra ajustar/trocar qualquer peça.

---

## 📦 Pré-requisitos

Você precisa instalar 3 ferramentas externas (não são pacotes pip):

### 1. ffmpeg (obrigatório) — corta o vídeo e detecta silêncios
- **Mac:** `brew install ffmpeg`
- **Windows:** `winget install ffmpeg` (ou baixe em https://ffmpeg.org)
- **Linux:** `sudo apt install ffmpeg`

### 2. Ollama (obrigatório pra separar os temas localmente)
- Baixe em https://ollama.com
- Depois rode uma vez pra baixar o modelo:
  ```bash
  ollama pull llama3.1:8b
  ```
- Deixe o Ollama rodando enquanto usa o pipeline.
- *(Alternativa: usar a API da Anthropic em vez do Ollama — veja "Trocar o LLM".)*

### 3. rclone (opcional — só se quiser subir pro Drive automaticamente)
- Instale em https://rclone.org
- Configure o acesso ao seu Drive: `rclone config` → crie um remote chamado `gdrive`
  do tipo *Google Drive*.

---

## 🚀 Instalação

```bash
# 1. Clone o repositório e entre na pasta
git clone <url-do-repo> && cd cortes-de-poscast

# 2. Crie um ambiente virtual e instale as dependências Python
python3 -m venv venv
source venv/bin/activate          # no Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Crie sua configuração pessoal
cp config.example.yaml config.local.yaml
```

Abra o `config.local.yaml` e ajuste o que quiser (modelo do Whisper, quantidade de
temas, se queima legenda, se envia pro Drive etc). Os comentários explicam cada opção.

---

## ▶️ Uso

Coloque o episódio numa pasta (ex.: `entrada/`) e rode:

```bash
python cortar.py entrada/episodio.mp4
```

Os cortes finais saem em `saida/`:

```
saida/
├── 01-abertura-e-boas-vindas.mp4
├── 01-abertura-e-boas-vindas.srt
├── 02-como-comecou-a-carreira.mp4
├── ...
└── temas.json          ← o "mapa" de todos os temas (pra revisar/ajustar)
```

O `temas.json` mostra o título, início e fim de cada corte — útil pra conferir e,
se quiser, editar antes de reprocessar.

---

## ⚙️ Ajustes comuns

| Quero... | Onde mexer (`config.local.yaml`) |
|----------|----------------------------------|
| Transcrição mais precisa | `whisper.modelo: large-v3` (mais lento) |
| Usar GPU NVIDIA (bem mais rápido) | `whisper.dispositivo: cuda` e `precisao: float16` |
| Cortes mais curtos/longos | `temas.duracao_min` / `temas.duracao_max` |
| Mais ou menos temas | `temas.temas_alvo` |
| Legenda só em arquivo (sem queimar) | `legendas.queimar: false` |
| Cortes mais "colados" ou mais folgados | `respiros.margem` |
| Detectar mais/menos silêncios | `respiros.ruido_db` e `duracao_minima` |
| Subir automático pro Drive | `export.enviar_drive: true` |

### Trocar o LLM (Ollama → Anthropic)

Se preferir usar a API da Anthropic (mais qualidade na separação de temas, custo baixo):

```yaml
temas:
  provedor: "anthropic"
  anthropic_modelo: "claude-sonnet-5"
```

E exporte a chave antes de rodar:

```bash
export ANTHROPIC_API_KEY="sua-chave"
```

---

## 🧠 Por que assim (e não uma ferramenta pronta)?

Ferramentas tipo Opus Clip / Vizard fazem parte disso, mas: são pagas por volume,
dão pouco controle sobre *como* o corte é feito, e a separação "por assunto" costuma
ser genérica. Aqui você manda em cada parâmetro, roda quantos episódios quiser sem
mensalidade, e pode plugar novas etapas (thumbnail automática, título pra YouTube,
post no Instagram via Meta API etc.) porque cada passo é um módulo Python isolado.

---

## 🗺️ Próximos passos possíveis

- Gerar **título + descrição** de cada corte pro YouTube/Instagram (mais uma chamada de LLM)
- Criar **thumbnail** automática do momento de maior destaque
- Formato **vertical 9:16** com rosto centralizado (crop dinâmico)
- Postar direto nas redes (a Meta API já está disponível neste ambiente)

Qualquer uma dessas dá pra adicionar como um novo módulo em `src/`.
