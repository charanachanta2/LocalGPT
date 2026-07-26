import os
import sys
import time
import threading

import requests
import webview
from waitress import serve

from app import app
from config import APP_HOST, APP_PORT, APP_URL
from model_manager import model_manager

def start_model():

    try:
        model_manager.start_model(
            "gemma-3"
        )

    except Exception as error:
        print(
            "Model startup error:",
            error
        )
# ============================================================
# FLASK SERVER
# ============================================================

def run_flask():
    serve(
        app,
        host=APP_HOST,
        port=APP_PORT,
        threads=8
    )


# ============================================================
# WAIT FOR FLASK
# ============================================================

def wait_for_server(timeout=30):

    start = time.time()

    while time.time() - start < timeout:

        try:
            response = requests.get(
                f"{APP_URL}/login",
                timeout=1
            )

            if response.status_code < 500:
                return True

        except requests.RequestException:
            pass

        time.sleep(0.25)

    return False


# ============================================================
# SHUTDOWN
# ============================================================

def shutdown():

    try:
        model_manager.stop()
    except Exception:
        pass


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    model_thread = threading.Thread(
        target=start_model,
        daemon=True
    )

    model_thread.start()
    
    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    if not wait_for_server():

        raise RuntimeError(
            "LocalGPT server failed to start."
        )

    window = webview.create_window(
        title="LocalGPT",
        url=APP_URL,
        width=1400,
        height=900,
        min_size=(900, 650),
        resizable=True,
        text_select=True
    )

    window.events.closed += shutdown

    webview.start(
        debug=False
    )