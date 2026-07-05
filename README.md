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

## 🎯 Modo LISTA — cortes com minutagem já definida

Se você **já tem a minutagem de cada corte** (num roteiro, por exemplo), não
precisa da IA adivinhar os temas. Use o modo lista: ele corta os clipes exatos,
legenda e queima — direto de um arquivo JSON.

```bash
# 1. Baixe o vídeo master do Drive pra pasta entrada/
# 2. Confira o caminho no campo "video" do JSON
# 3. Rode:
python cortar_lista.py cortes/gorayeb-ep01.json
```

O JSON descreve cada corte por segmentos de tempo (em segundos):

```json
{
  "video": "entrada/episodio.mp4",
  "cortes": [
    { "n": "1",  "titulo": "O bilhete da mae",  "segmentos": [[990, 1052]] },
    { "n": "C1", "titulo": "Duas maes uma licao", "segmentos": [[990, 1035], [2620, 2659]] }
  ]
}
```

- **Um segmento** `[[inicio, fim]]` → corte direto.
- **Vários segmentos** → o pipeline **costura** (concatena) os trechos num clipe só
  (é assim que os "cortes cruzados" juntam momentos diferentes).

Cada corte gera um `NN-titulo.mp4` (legenda queimada, se `legendas.queimar: true`)
e um `.srt` ao lado. O episódio de exemplo (`cortes/gorayeb-ep01.json`) já vem
com os 39 cortes mapeados.

### Formato Reels (9:16 + headline)

No `config.local.yaml`, o bloco `formato` controla a saída:

```yaml
formato:
  vertical: true        # 9:16 (1080x1920), fundo desfocado + vídeo centralizado
  headline: true        # sobrepõe a headline do corte nos primeiros segundos
  headline_segundos: 3.5
```

A **headline** vem do campo `"headline"` de cada corte no JSON (só aparece nos
cortes que têm uma). Com `vertical: true` o corte já sai pronto pra Reels/Shorts/
TikTok, sem passar por editor.

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
