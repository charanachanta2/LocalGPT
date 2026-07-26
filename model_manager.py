import atexit
import subprocess
import threading
import time

import requests

from config import (
    MODELS,
    LLAMA_EXECUTABLE,
    LLAMA_HOST,
    LLAMA_PORT,
    LLAMA_BASE_URL,
    MODEL_START_TIMEOUT
)


class ModelManager:

    def __init__(self):

        self.process = None
        self.current_model = None
        self.status = "stopped"
        self.error = None

        self.lock = threading.Lock()


    # ========================================================
    # HEALTH
    # ========================================================

    def server_ready(self):

        try:

            response = requests.get(
                f"{LLAMA_BASE_URL}/health",
                timeout=2
            )

            return response.ok

        except requests.RequestException:

            return False


    # ========================================================
    # START
    # ========================================================

    def start_model(self, model_id):

        with self.lock:

            if model_id not in MODELS:

                raise ValueError(
                    f"Unknown model: {model_id}"
                )


            model = MODELS[model_id]


            if not model["path"].exists():

                raise FileNotFoundError(
                    f"Model not found: "
                    f"{model['path']}"
                )


            if (
                self.current_model == model_id
                and self.process
                and self.process.poll() is None
                and self.server_ready()
            ):

                return True


            self._stop_model()


            self.status = "loading"
            self.error = None


            print()
            print("=" * 55)
            print("LocalGPT Model Manager")
            print("=" * 55)

            print(
                f"Loading       : {model['name']}"
            )

            print(
                f"Model         : {model['path']}"
            )

            print(
                f"GPU layers    : "
                f"{model['gpu_layers']}"
            )

            print(
                f"Context       : "
                f"{model['context']}"
            )

            print("=" * 55)
            print()


            command = [

                LLAMA_EXECUTABLE,

                "serve",

                "-m",
                str(model["path"]),

                "--host",
                LLAMA_HOST,

                "--port",
                str(LLAMA_PORT),

                "-ngl",
                str(model["gpu_layers"]),

                "-c",
                str(model["context"])
            ]


            try:

                flags = 0

                if hasattr(
                    subprocess,
                    "CREATE_NEW_PROCESS_GROUP"
                ):

                    flags = (
                        subprocess
                        .CREATE_NEW_PROCESS_GROUP
                    )


                self.process = subprocess.Popen(
                    command,
                    stdout=None,
                    stderr=None,
                    creationflags=flags
                )


            except Exception as error:

                self.process = None
                self.status = "error"
                self.error = str(error)

                raise


            start_time = time.time()


            while (
                time.time() - start_time
                < MODEL_START_TIMEOUT
            ):

                if self.process.poll() is not None:

                    self.status = "error"

                    self.error = (
                        "llama.cpp exited while "
                        "loading the model."
                    )

                    self.process = None

                    raise RuntimeError(
                        self.error
                    )


                if self.server_ready():

                    self.current_model = model_id
                    self.status = "ready"
                    self.error = None

                    print()
                    print(
                        f"{model['name']} READY"
                    )
                    print()

                    return True


                time.sleep(1)


            self.status = "error"

            self.error = (
                f"{model['name']} did not start "
                f"within "
                f"{MODEL_START_TIMEOUT} seconds."
            )


            self._stop_model()

            raise TimeoutError(
                self.error
            )


    # ========================================================
    # STOP
    # ========================================================

    def _stop_model(self):

        if not self.process:

            self.current_model = None

            return


        print(
            "Stopping current model..."
        )


        try:

            if self.process.poll() is None:

                self.process.terminate()

                try:

                    self.process.wait(
                        timeout=10
                    )

                except subprocess.TimeoutExpired:

                    self.process.kill()

                    self.process.wait(
                        timeout=5
                    )


        except Exception as error:

            print(
                "Model shutdown error:",
                error
            )


        finally:

            self.process = None
            self.current_model = None


    def stop(self):

        with self.lock:

            self._stop_model()

            self.status = "stopped"


    # ========================================================
    # SWITCH
    # ========================================================

    def switch_model(
        self,
        model_id
    ):

        if (
            model_id ==
            self.current_model
            and self.server_ready()
        ):

            return True


        return self.start_model(
            model_id
        )


    # ========================================================
    # STATUS
    # ========================================================

    def get_status(self):

        model = None


        if self.current_model:

            config = MODELS.get(
                self.current_model
            )

            if config:

                model = {

                    "id":
                        self.current_model,

                    "name":
                        config["name"],

                    "description":
                        config["description"]
                }


        return {

            "status":
                self.status,

            "ready":
                (
                    self.status == "ready"
                    and self.server_ready()
                ),

            "model":
                model,

            "error":
                self.error
        }


model_manager = ModelManager()

atexit.register(
    model_manager.stop
)