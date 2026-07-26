from pathlib import Path
import sys
import os


# ============================================================
# PATHS
# ============================================================

if getattr(sys, "frozen", False):
    LOCAL_LLM_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", LOCAL_LLM_DIR))
else:
    APP_DIR = Path(__file__).resolve().parent
    LOCAL_LLM_DIR = APP_DIR.parent
    BUNDLE_DIR = APP_DIR


MODEL_DIR = LOCAL_LLM_DIR / "models"
DATA_DIR = LOCAL_LLM_DIR / "data"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DATABASE_PATH = DATA_DIR / "localgpt.db"


# ============================================================
# FLASK
# ============================================================

# Persistent secret used for browser sessions.
SECRET_FILE = DATA_DIR / ".secret_key"


def load_secret_key():
    if SECRET_FILE.exists():
        return SECRET_FILE.read_text(
            encoding="utf-8"
        ).strip()

    secret = os.urandom(32).hex()

    SECRET_FILE.write_text(
        secret,
        encoding="utf-8"
    )

    return secret


SECRET_KEY = load_secret_key()


# ============================================================
# MODELS
# ============================================================

MODELS = {

    "gemma-3": {
        "name": "Gemma 3 4B",
        "description": "Fast",
        "path":
            MODEL_DIR /
            "gemma-3-4b-it-Q4_K_M.gguf",

        "gpu_layers": 99,
        "context": 4096
    },

    "gemma-4": {
        "name": "Gemma 4 E4B",
        "description": "Smart",
        "path":
            MODEL_DIR /
            "gemma-4-E4B-it-Q4_0.gguf",

        # Keep CPU-only because this was the
        # stable configuration on your RTX 3050.
        "gpu_layers": 0,
        "context": 4096
    }
}


DEFAULT_MODEL = "gemma-3"


# ============================================================
# LLAMA.CPP
# ============================================================

LLAMA_HOST = "127.0.0.1"
LLAMA_PORT = 8080

LLAMA_BASE_URL = (
    f"http://{LLAMA_HOST}:{LLAMA_PORT}"
)

# For now Windows resolves your installed llama.exe.
#
# Later, for the portable EXE, we'll change this to:
# D:\LocalLLM\runtime\llama.exe

LLAMA_EXECUTABLE = str(
    LOCAL_LLM_DIR
    / "runtime"
    / "llama.exe"
)

MODEL_START_TIMEOUT = 180


# ============================================================
# LOCALGPT
# ============================================================

APP_HOST = "127.0.0.1"
APP_PORT = 5000

APP_URL = (
    f"http://{APP_HOST}:{APP_PORT}"
)