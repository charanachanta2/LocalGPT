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
| OS | *(add yours here, e.g. Windows 11 / Ubuntu 22.04)* |

> This setup is a normal mid-range gaming/productivity laptop — nothing exotic. The point is to show this is achievable on hardware most people already own.

## Prerequisites

Before setting this up, make sure you have:

- A laptop/desktop with at least 8GB RAM (16GB recommended for smoother performance)
- ~5-10GB free disk space per model
- *(GPU optional — CPU-only works but will be slower)*
- Basic command line familiarity
- One of: [Ollama](https://ollama.com), [LM Studio](https://lmstudio.ai), or [llama.cpp](https://github.com/ggerganov/llama.cpp)

## Setup

*(Fill in the exact steps you used — example below, edit as needed)*

```bash
# 1. Install Ollama / LM Studio / llama.cpp (whichever you used)
# 2. Pull the Gemma model
ollama pull gemma3:4b

# 3. Run it
ollama run gemma3:4b
```

### Step-by-Step (detailed)

1. *(e.g. Download and install Ollama from the website)*
2. *(e.g. Open terminal, run the pull command)*
3. *(e.g. Wait for download — model size ~X GB)*
4. *(e.g. Start chatting via `ollama run gemma3:4b` or connect it to a UI like Open WebUI)*
5. *(Any custom system prompt or persona you set up for your "GPT")*

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



*(Fill in — this makes your numbers credible to others)*

- Each prompt run **3 times**, average taken
- Timer started when prompt submitted, stopped when full response finished streaming
- Fresh session for each test (no prior context in the chat)
- Model: *(specify which of the two — 4B or 4B E4B — for each row, or split into two tables)*

### Observations

- Basic Q&A is fast enough to feel conversational (1–2s).
- Code generation takes noticeably longer (~15s), likely due to longer, more structured output and higher token count rather than model complexity itself.
- Performance is naturally capped by the 4GB VRAM — larger models or longer contexts would be slower or may not fit at all.
- *(Add more once you fill in the extra rows above — e.g. does reasoning take longer than factual recall? Does E4B outperform standard 4B?)*

## Model Comparison: Gemma 3 4B vs Gemma 3 4B E4B

| Metric | Gemma 3 4B | Gemma 3 4B E4B |
|---|---|---|
| Avg. simple Q&A time | *(fill in)* | *(fill in)* |
| Avg. code gen time | *(fill in)* | *(fill in)* |
| RAM usage (idle) | *(fill in)* | *(fill in)* |
| RAM usage (during inference) | *(fill in)* | *(fill in)* |
| Output quality (subjective) | *(fill in)* | *(fill in)* |

## Why This Matters

You don't need expensive hardware or a paid subscription to run your own AI assistant. With open models like Gemma and tools like Ollama/LM Studio, anyone with a decent laptop can set up a private, offline GPT-style assistant in minutes.

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
*(fill in — e.g. "No, but it's slower on CPU-only")*

**Q: How much does this cost to run?**
Free after initial setup — no API fees, runs entirely offline on your own hardware.

**Q: Can I use a different model instead of Gemma?**
Yes — Ollama/LM Studio support many open models (Llama, Mistral, Phi, Qwen, etc.). Gemma was chosen here because *(your reason — e.g. good balance of speed/quality for this hardware)*.

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

*(Add your license here, e.g. MIT)*