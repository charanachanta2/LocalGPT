# My Own GPT — Built on Gemma (Local LLM)

## Overview

This project shows that you don't need OpenAI or a cloud subscription to have your own personal "GPT." Using Google's open-weight **Gemma** models, you can run a capable chatbot entirely on a normal consumer laptop — no internet required after setup, no API costs, and full privacy since everything runs locally.

This repo/README documents my setup, the hardware it runs on, and real response-time benchmarks so others can see what to expect before trying it themselves.

## Models Used

| Model | Parameters | Notes |
|---|---|---|
| Gemma 3 4B | 4B | Lightweight, fast for everyday Q&A |
| Gemma 3 4B E4B | 4B (efficient variant) | Optimized variant, tested for comparison |

## Hardware Specs

| Component | Spec |
|---|---|
| CPU | Intel Core i5, 12th Gen |
| RAM | 16 GB DDR5 |
| GPU | RTX 3050, 4 GB VRAM |
| OS | Windows 11 |

> This setup is a normal mid-range gaming/productivity laptop — nothing exotic. The point is to show this is achievable on hardware most people already own.

## How It's Built

Unlike most "run an LLM locally" tutorials, this isn't Ollama/LM Studio with a stock chat UI — it's a **fully custom interface** built from scratch:

- **Backend:** Flask + Flask-SQLAlchemy + Flask-CORS, served via `waitress` (production-grade WSGI server)
- **Frontend:** Custom HTML/CSS/JS (`templates/`, `static/`)
- **Inference engine:** `model_manager.py` spawns `llama.exe` (a locally installed [llama.cpp](https://github.com/ggerganov/llama.cpp) server binary) as a subprocess, pointing it at the downloaded `.gguf` model file. Flask then talks to that llama.cpp server over HTTP (`http://127.0.0.1:8080`) to get responses.
- **Chat history/storage:** `database.py` (SQLite, stored in a local `data/` folder)
- **Config:** `config.py` — defines model paths, ports, and per-model settings (GPU layers, context size)
- **Desktop app packaging:** `desktop.py` wraps the Flask app into a standalone desktop application (with its own icon, `localgpt.ico`) — so it runs like a native app instead of "open browser, go to localhost"

Repo: [github.com/charanachanta2/LocalGPT](https://github.com/charanachanta2/LocalGPT)

## Prerequisites

Before setting this up, make sure you have:

- Python 3.x installed
- A laptop/desktop with at least 8GB RAM (16GB recommended for smoother performance)
- ~5-10GB free disk space per model
- *(GPU optional — CPU-only works but will be slower)*
- A [llama.cpp](https://github.com/ggerganov/llama.cpp) build for your OS (specifically `llama.exe` / the `llama-server` binary on Windows) — this is what actually runs the model
- The Gemma model files downloaded as `.gguf` files (see below)

### Folder Layout

`config.py` expects a specific folder structure — the repo folder and the model/runtime files are **siblings**, not nested inside each other:

```
LocalLLM/                          ← parent folder (name it anything)
├── LocalGPT/                      ← this repo, cloned here
│   ├── app.py
│   ├── config.py
│   ├── model_manager.py
│   └── ...
├── models/                        ← put your downloaded .gguf files here
│   ├── gemma-3-4b-it-Q4_K_M.gguf
│   └── gemma-4-E4B-it-Q4_0.gguf
└── runtime/                       ← put the llama.cpp binary here
    └── llama.exe
```

`data/` (for the SQLite chat history database) is created automatically on first run.

## Setup

```bash
# 1. Create a parent folder and clone the repo inside it
mkdir LocalLLM
cd LocalLLM
git clone https://github.com/charanachanta2/LocalGPT.git

# 2. Create the sibling folders llama.cpp and the models expect
mkdir models
mkdir runtime

# 3. Download llama.cpp and place the binary in runtime/
#    (get it from https://github.com/ggerganov/llama.cpp/releases,
#    the Windows build gives you llama-server.exe / llama.exe)

# 4. Download the Gemma model files into models/
curl.exe -L "https://huggingface.co/ggml-org/gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-Q4_K_M.gguf?download=true" -o "models/gemma-3-4b-it-Q4_K_M.gguf"
curl.exe -L "https://huggingface.co/ggml-org/gemma-4-E4B-it-GGUF/resolve/main/gemma-4-E4B-it-Q4_0.gguf?download=true" -o "models/gemma-4-E4B-it-Q4_0.gguf"

# 5. Install Python dependencies
cd LocalGPT
pip install -r requirements.txt

# 6. Run the app
python app.py

# — OR, to run it as a standalone desktop app —
python desktop.py
```

The web interface runs at `http://127.0.0.1:5000` by default (see `APP_PORT` in `config.py`); the llama.cpp server it spawns runs at `http://127.0.0.1:8080` (see `LLAMA_PORT`).

### Step-by-Step (detailed)

1. **Download the Gemma model files** — must match the exact filenames referenced in `config.py`'s `MODELS` dict:
   - `gemma-3-4b-it-Q4_K_M.gguf`
   - `gemma-4-E4B-it-Q4_0.gguf`
2. **Place the model files** in the `models/` folder — a sibling of the cloned repo folder (see Folder Layout above), *not* inside `LocalGPT/`.
3. **Place `llama.exe`** (the llama.cpp server binary) in the `runtime/` folder, also a sibling of the repo.
4. Install dependencies with `pip install -r requirements.txt`.
5. Run `python app.py` for the web interface (served via waitress) — or `python desktop.py` to launch it as a native desktop window. On first request, `model_manager.py` automatically launches `llama.exe` with the right model path, GPU layers, and context size for whichever model you select.

> **Note on GPU layers:** in `config.py`, Gemma 3 4B is configured with `gpu_layers: 99` (full GPU offload — fast), while Gemma 4 E4B is set to `gpu_layers: 0` (CPU-only) because that was the stable configuration on the RTX 3050 (4GB VRAM). This is a big part of why E4B is slower in the benchmarks below.

## Performance Benchmarks

Response times measured on the hardware above. "Simple question" = general knowledge/factual queries. "Code generation" = requests to write a function/script.

| Task Type | Example Prompt | Avg. Response Time |
|---|---|---|
| Simple factual question | "What is the capital of France?" | 1–2 seconds |
| Basic math | "What is 45 * 12?" | 3 seconds |
| Short summarization | "Summarize this paragraph in 2 lines: ..." | 1 second |
| Translation | "Translate 'Good morning' to French" | 1 second |
| Reasoning/logic question | "If a train leaves at 3pm going 60mph..." | 6 seconds (model asked a clarifying question before answering) |
| Creative writing | "Write a 4-line poem about the ocean" | 2 seconds |
| Code debugging | "Fix this broken Python function: ..." | 1 second to respond it needed the code, then 3 seconds to fix it once provided |
| Long-form explanation | "Explain how photosynthesis works" | 12 seconds |
| Code generation | "Write a Python function to reverse a string" | ~15 seconds |
| Code generation | "Write a program to check Armstrong number" | 11 seconds |

### Technical Performance Stats (from llama.cpp server logs)

Captured directly from the local inference server during testing:

| Metric | Value |
|---|---|
| Prompt eval speed | ~242 tokens/sec |
| Text generation speed | ~46–47 tokens/sec |
| Total tokens generated (longer response) | 1024 tokens in ~22 seconds |
| Context reused across turns | Yes (graph/KV cache reuse observed, e.g. "graphs reused = 2240") |

![llama.cpp server logs showing token generation speed](images/llama_cpp_logs.png)

### System Resource Usage During Inference

RAM usage while the model was actively running, captured via Task Manager:

| Metric | Value |
|---|---|
| Total RAM | 16.0 GB DDR5 |
| RAM in use | 13.3 / 15.7 GB (~85%) |
| CPU usage | ~23% (1.88 GHz) |

![Task Manager showing memory usage during inference](images/task_manager_memory.png)

> **Note:** With 4B-parameter models, RAM usage sits close to the ceiling of a 16GB system. Running other heavy applications alongside the model can cause slowdowns or swapping.



### Testing Methodology

- Each prompt run **3 times**, average taken
- Timer started when prompt submitted, stopped when full response finished streaming
- Fresh session for each test (no prior context in the chat)
- Model: Gemma 3 4B (unless noted otherwise)

### Observations

- Basic Q&A is fast enough to feel conversational (1–2s).
- Code generation takes noticeably longer (~11–15s), likely due to longer, more structured output and higher token count rather than model complexity itself.
- Performance is naturally capped by the 4GB VRAM — larger models or longer contexts would be slower or may not fit at all.
- Gemma 4 E4B runs CPU-only in this setup (see GPU layers note above), which is a major reason it's consistently slower than Gemma 3 4B in the comparison table below.

## Model Comparison: Gemma 3 4B vs Gemma 3 4B E4B

| Metric | Gemma 3 4B | Gemma 3 4B E4B |
|---|---|---|
| Avg. simple Q&A time | 2 seconds | 5 seconds |
| Avg. code gen time | 10 seconds | 15 seconds |
| RAM usage (idle) | ~70% | ~75% |
| RAM usage (during inference) | 85–87% | 87–93% |
| Output quality (subjective) | Good for faster responses | Good for smarter, more useful answers |

## Why This Matters

You don't need expensive hardware or a paid subscription to run your own AI assistant. With open models like Gemma running through llama.cpp, anyone with a decent laptop can set up a private, offline GPT-style assistant with their own custom interface — no subscription, no API key, no data leaving the machine.

## Use Cases

What you can realistically use this local GPT for:

- Quick factual lookups without needing internet
- Drafting emails, notes, or short writing
- Learning to code / getting quick code snippets
- Private conversations you don't want sent to the cloud
- Offline assistant while traveling or in low-connectivity areas

## Limitations

Be upfront about these — it builds trust with readers:

- Not as accurate or broad-knowledge as GPT-4/Claude/Gemini (much smaller model)
- Slower on complex tasks (code, long reasoning) as shown in benchmarks above
- Knowledge cutoff is fixed — no internet access, no live/current info
- Limited context window compared to large cloud models
- 4GB VRAM caps how large a model you can comfortably run

## Frequently Asked Questions

**Q: Do I need a GPU to run this?**
No — CPU-only works. In this setup, Gemma 4 E4B actually runs CPU-only (`gpu_layers: 0` in `config.py`) because that was the stable configuration on the RTX 3050's 4GB VRAM. A GPU speeds things up significantly when there's enough VRAM to offload layers to it — Gemma 3 4B uses full GPU offload (`gpu_layers: 99`) here.

**Q: How much does this cost to run?**
Free after initial setup — no API fees, runs entirely offline on your own hardware.

**Q: Can I use a different model instead of Gemma?**
Yes — since the backend runs any `.gguf` file through llama.cpp, you can swap in any GGUF-format model by adding an entry to the `MODELS` dict in `config.py` with its filename, GPU layers, and context size. Gemma was chosen here for a good balance of speed and quality on limited (4GB) VRAM.

**Q: Is my data private?**
Yes — since it runs fully locally, nothing is sent to any external server.

## Future Improvements

- Benchmark larger Gemma variants (9B, 27B) if hardware allows
- Try quantized versions for faster inference
- Add a proper latency-logging script for consistent benchmarking

## Contributing

If others want to try this and share their own benchmark numbers on different hardware, feel free to open a PR or issue with:
- Your hardware specs
- Model + quantization used
- Response times for the same test prompts above

This will help build a broader picture of what's realistically achievable on consumer hardware.

## License

This project is licensed under the [MIT License](LICENSE) — see the LICENSE file for details.