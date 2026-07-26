from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    session,
    redirect,
    url_for
)

from flask_cors import CORS

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from datetime import datetime

from functools import wraps

import requests
import threading
import webbrowser
import time
import secrets
import hashlib
import uuid
import atexit


from config import (
    DATABASE_PATH,
    MODELS,
    DEFAULT_MODEL,
    LLAMA_BASE_URL,
    SECRET_KEY,
    APP_HOST,
    APP_PORT,
    APP_URL
)


from database import (
    db,
    User,
    Chat,
    Message,
    APIKey
)


from model_manager import (
    model_manager
)


# ============================================================
# FLASK
# ============================================================

import sys
from pathlib import Path


if getattr(sys, "frozen", False):

    BUNDLE_DIR = Path(
        sys._MEIPASS
    )

else:

    BUNDLE_DIR = Path(
        __file__
    ).resolve().parent


app = Flask(
    __name__,

    template_folder=str(
        BUNDLE_DIR / "templates"
    ),

    static_folder=str(
        BUNDLE_DIR / "static"
    )
)

app.secret_key = SECRET_KEY

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = (
    f"sqlite:///"
    f"{DATABASE_PATH.as_posix()}"
)

app.config[
    "SQLALCHEMY_TRACK_MODIFICATIONS"
] = False

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)


db.init_app(app)

CORS(app)


# ============================================================
# HELPERS
# ============================================================

def current_user():

    user_id = session.get(
        "user_id"
    )

    if not user_id:

        return None

    return db.session.get(
        User,
        user_id
    )


def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not current_user():

            if request.path.startswith(
                "/api/"
            ):

                return jsonify({
                    "error":
                        "Authentication required."
                }), 401

            return redirect(
                url_for("login_page")
            )

        return function(
            *args,
            **kwargs
        )

    return wrapper


def create_chat_title(text):

    clean = " ".join(
        text.split()
    )

    if len(clean) <= 48:

        return clean

    return (
        clean[:48].rstrip()
        + "..."
    )


def get_user_chat(
    chat_id,
    user_id
):

    return Chat.query.filter_by(
        id=chat_id,
        user_id=user_id
    ).first()


def build_context(chat_id):

    messages = (
        Message.query
        .filter_by(chat_id=chat_id)
        .order_by(Message.id.asc())
        .all()
    )

    result = []

    # System instructions for LocalGPT
    result.append({
        "role": "system",
        "content": """
You are LocalGPT, a private AI assistant running locally on the user's computer.

When providing programming code, always use Markdown fenced code blocks and include the programming language.

For example, Python code should be formatted using a fenced code block with the language set to python.

The LocalGPT interface automatically provides Copy and Save buttons for fenced code blocks.

If you genuinely need the user to choose between multiple options before you can continue, you may output an interactive question using exactly this format:

<localgpt-question>
{
    "title": "Short title",
    "question": "Question for the user",
    "options": [
        "Option 1",
        "Option 2",
        "Option 3"
    ]
}
</localgpt-question>

Only use <localgpt-question> when an answer is genuinely required before continuing.

Do not use the interactive question format for ordinary conversational questions.

When answering normally, use standard Markdown.
""".strip()
    })

    # Add previous conversation messages
    for message in messages:

        if message.role in (
            "system",
            "user",
            "assistant"
        ):

            result.append({
                "role": message.role,
                "content": message.content
            })

    return result


def ensure_model(model_id):

    if model_id not in MODELS:

        raise ValueError(
            "Unknown model."
        )


    if not MODELS[
        model_id
    ]["path"].exists():

        raise FileNotFoundError(
            f"{MODELS[model_id]['name']} "
            "is not installed."
        )


    if (
        model_manager.current_model
        != model_id
    ):

        model_manager.switch_model(
            model_id
        )

    elif not model_manager.server_ready():

        model_manager.start_model(
            model_id
        )


def generate_completion(
    messages,
    model_id,
    max_tokens=1024,
    temperature=0.7
):

    ensure_model(
        model_id
    )


    response = requests.post(

        f"{LLAMA_BASE_URL}"
        "/v1/chat/completions",

        json={

            "messages":
                messages,

            "temperature":
                temperature,

            "max_tokens":
                max_tokens,

            "stream":
                False
        },

        timeout=300
    )


    if not response.ok:

        raise RuntimeError(
            f"llama.cpp returned "
            f"{response.status_code}: "
            f"{response.text[:500]}"
        )


    result = response.json()


    choices = result.get(
        "choices",
        []
    )


    if not choices:

        raise RuntimeError(
            "The model returned no choices."
        )


    content = (

        choices[0]
        .get(
            "message",
            {}
        )
        .get(
            "content",
            ""
        )
        .strip()
    )


    if not content:

        raise RuntimeError(
            "The model returned "
            "an empty response."
        )


    return content


# ============================================================
# AUTH PAGES
# ============================================================

@app.route("/login")
def login_page():

    if current_user():

        return redirect(
            url_for("index")
        )


    user_exists = (
        User.query.first()
        is not None
    )


    return render_template(
        "login.html",
        user_exists=user_exists
    )


@app.route(
    "/api/auth/register",
    methods=["POST"]
)
def register():

    # LocalGPT currently supports one
    # local owner account.

    if User.query.first():

        return jsonify({
            "error":
                "An account already exists."
        }), 409


    data = request.get_json(
        silent=True
    ) or {}


    username = data.get(
        "username",
        ""
    ).strip()


    password = data.get(
        "password",
        ""
    )


    if len(username) < 3:

        return jsonify({
            "error":
                "Username must contain "
                "at least 3 characters."
        }), 400


    if len(password) < 6:

        return jsonify({
            "error":
                "Password must contain "
                "at least 6 characters."
        }), 400


    user = User(

        username=username,

        password_hash=
            generate_password_hash(
                password
            )
    )


    db.session.add(user)

    db.session.commit()


    session["user_id"] = user.id


    return jsonify({
        "success": True
    })


@app.route(
    "/api/auth/login",
    methods=["POST"]
)
def login():

    data = request.get_json(
        silent=True
    ) or {}


    username = data.get(
        "username",
        ""
    ).strip()


    password = data.get(
        "password",
        ""
    )


    user = User.query.filter_by(
        username=username
    ).first()


    if (
        not user
        or not check_password_hash(
            user.password_hash,
            password
        )
    ):

        return jsonify({
            "error":
                "Invalid username or password."
        }), 401


    session["user_id"] = (
        user.id
    )


    return jsonify({
        "success": True
    })


@app.route(
    "/api/auth/logout",
    methods=["POST"]
)
def logout():

    session.clear()

    return jsonify({
        "success": True
    })


@app.route(
    "/api/auth/me"
)
@login_required
def auth_me():

    user = current_user()

    return jsonify({

        "id":
            user.id,

        "username":
            user.username
    })


# ============================================================
# MAIN UI
# ============================================================

@app.route("/")
@login_required
def index():

    return render_template(
        "index.html",
        username=current_user().username
    )


# ============================================================
# MODELS
# ============================================================

@app.route("/api/models")
@login_required
def models():

    result = []


    for model_id, model in MODELS.items():

        result.append({

            "id":
                model_id,

            "name":
                model["name"],

            "description":
                model["description"],

            "available":
                model["path"].exists(),

            "loaded":
                (
                    model_manager
                    .current_model
                    == model_id
                )
        })


    return jsonify({

        "default":
            DEFAULT_MODEL,

        "current":
            model_manager.current_model,

        "models":
            result
    })


@app.route("/api/status")
@login_required
def status():

    return jsonify(
        model_manager.get_status()
    )


@app.route(
    "/api/models/switch",
    methods=["POST"]
)
@login_required
def switch_model():

    data = request.get_json(
        silent=True
    ) or {}


    model_id = data.get(
        "model"
    )


    try:

        ensure_model(
            model_id
        )


        return jsonify({

            "success":
                True,

            "model":
                model_id
        })


    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


# ============================================================
# CHATS
# ============================================================

@app.route("/api/chats")
@login_required
def chats():

    user = current_user()


    records = (

        Chat.query
        .filter_by(
            user_id=user.id
        )
        .order_by(
            Chat.updated_at.desc()
        )
        .all()
    )


    return jsonify([

        {

            "id":
                chat.id,

            "title":
                chat.title,

            "model":
                chat.model,

            "created_at":
                chat.created_at.isoformat(),

            "updated_at":
                chat.updated_at.isoformat()
        }

        for chat in records
    ])


@app.route(
    "/api/chats/<int:chat_id>"
)
@login_required
def get_chat(chat_id):

    user = current_user()


    chat = get_user_chat(
        chat_id,
        user.id
    )


    if not chat:

        return jsonify({
            "error":
                "Chat not found."
        }), 404


    messages = (

        Message.query
        .filter_by(
            chat_id=chat.id
        )
        .order_by(
            Message.id.asc()
        )
        .all()
    )


    return jsonify({

        "id":
            chat.id,

        "title":
            chat.title,

        "model":
            chat.model,

        "messages": [

            {

                "id":
                    message.id,

                "role":
                    message.role,

                "content":
                    message.content,

                "model":
                    message.model
            }

            for message in messages
        ]
    })


@app.route(
    "/api/chats/<int:chat_id>",
    methods=["PATCH"]
)
@login_required
def rename_chat(chat_id):

    user = current_user()


    chat = get_user_chat(
        chat_id,
        user.id
    )


    if not chat:

        return jsonify({
            "error":
                "Chat not found."
        }), 404


    data = request.get_json(
        silent=True
    ) or {}


    title = data.get(
        "title",
        ""
    ).strip()


    if not title:

        return jsonify({
            "error":
                "Title cannot be empty."
        }), 400


    chat.title = title[:200]

    chat.updated_at = (
        datetime.utcnow()
    )


    db.session.commit()


    return jsonify({
        "success": True
    })


@app.route(
    "/api/chats/<int:chat_id>",
    methods=["DELETE"]
)
@login_required
def delete_chat(chat_id):

    user = current_user()


    chat = get_user_chat(
        chat_id,
        user.id
    )


    if not chat:

        return jsonify({
            "error":
                "Chat not found."
        }), 404


    db.session.delete(chat)

    db.session.commit()


    return jsonify({
        "success": True
    })


# ============================================================
# WEB CHAT
# ============================================================

@app.route(
    "/api/chat",
    methods=["POST"]
)
@login_required
def web_chat():

    user = current_user()


    data = request.get_json(
        silent=True
    ) or {}


    text = data.get(
        "message",
        ""
    ).strip()


    model_id = data.get(
        "model",
        DEFAULT_MODEL
    )


    chat_id = data.get(
        "chat_id"
    )


    if not text:

        return jsonify({
            "error":
                "Message cannot be empty."
        }), 400


    if model_id not in MODELS:

        return jsonify({
            "error":
                "Unknown model."
        }), 400


    # --------------------------------------------------------
    # LOAD/CREATE CHAT
    # --------------------------------------------------------

    chat = None


    if chat_id is not None:

        try:

            chat_id = int(
                chat_id
            )

        except (
            TypeError,
            ValueError
        ):

            return jsonify({
                "error":
                    "Invalid chat ID."
            }), 400


        chat = get_user_chat(
            chat_id,
            user.id
        )


        if not chat:

            return jsonify({
                "error":
                    "Chat not found."
            }), 404


    if not chat:

        chat = Chat(

            user_id=
                user.id,

            title=
                create_chat_title(
                    text
                ),

            model=
                model_id
        )


        db.session.add(chat)

        db.session.flush()


    # --------------------------------------------------------
    # SAVE USER
    # --------------------------------------------------------

    message = Message(

        chat_id=
            chat.id,

        role=
            "user",

        content=
            text,

        model=
            model_id
    )


    db.session.add(
        message
    )


    chat.model = model_id

    chat.updated_at = (
        datetime.utcnow()
    )


    db.session.commit()


    # --------------------------------------------------------
    # GENERATE
    # --------------------------------------------------------

    try:

        conversation = (
            build_context(
                chat.id
            )
        )


        response_text = (
            generate_completion(
                conversation,
                model_id
            )
        )


        assistant = Message(

            chat_id=
                chat.id,

            role=
                "assistant",

            content=
                response_text,

            model=
                model_id
        )


        db.session.add(
            assistant
        )


        chat.updated_at = (
            datetime.utcnow()
        )


        db.session.commit()


        return jsonify({

            "response":
                response_text,

            "chat_id":
                chat.id,

            "title":
                chat.title,

            "model":
                model_id,

            "model_name":
                MODELS[
                    model_id
                ]["name"]
        })


    except Exception as error:

        print(
            "Generation error:",
            error
        )


        return jsonify({

            "error":
                str(error),

            "chat_id":
                chat.id

        }), 500


# ============================================================
# API KEY MANAGER
# ============================================================

@app.route(
    "/api/keys",
    methods=["GET"]
)
@login_required
def list_keys():

    user = current_user()


    keys = (

        APIKey.query
        .filter_by(
            user_id=user.id
        )
        .order_by(
            APIKey.created_at.desc()
        )
        .all()
    )


    return jsonify([

        {

            "id":
                key.id,

            "name":
                key.name,

            "prefix":
                key.key_prefix,

            "created_at":
                key.created_at.isoformat(),

            "last_used_at":
                (
                    key.last_used_at
                    .isoformat()

                    if key.last_used_at
                    else None
                ),

            "revoked":
                key.revoked
        }

        for key in keys
    ])


@app.route(
    "/api/keys",
    methods=["POST"]
)
@login_required
def create_key():

    user = current_user()


    data = request.get_json(
        silent=True
    ) or {}


    name = data.get(
        "name",
        ""
    ).strip()


    if not name:

        return jsonify({
            "error":
                "Key name is required."
        }), 400


    raw_key = (
        "lgpt_"
        + secrets.token_urlsafe(32)
    )


    key_hash = hashlib.sha256(
        raw_key.encode("utf-8")
    ).hexdigest()


    prefix = (
        raw_key[:12]
        + "..."
    )


    record = APIKey(

        user_id=
            user.id,

        name=
            name[:100],

        key_prefix=
            prefix,

        key_hash=
            key_hash
    )


    db.session.add(
        record
    )

    db.session.commit()


    return jsonify({

        "success":
            True,

        "id":
            record.id,

        "name":
            record.name,

        # This is the ONLY time the
        # complete key is returned.

        "key":
            raw_key,

        "prefix":
            prefix
    })


@app.route(
    "/api/keys/<int:key_id>",
    methods=["DELETE"]
)
@login_required
def revoke_key(key_id):

    user = current_user()


    key = APIKey.query.filter_by(

        id=key_id,

        user_id=user.id

    ).first()


    if not key:

        return jsonify({
            "error":
                "API key not found."
        }), 404


    key.revoked = True

    db.session.commit()


    return jsonify({
        "success": True
    })


# ============================================================
# API AUTHENTICATION
# ============================================================

def authenticate_api_key():

    header = request.headers.get(
        "Authorization",
        ""
    )


    if not header.startswith(
        "Bearer "
    ):

        return None


    raw_key = (
        header[7:]
        .strip()
    )


    if not raw_key.startswith(
        "lgpt_"
    ):

        return None


    digest = hashlib.sha256(
        raw_key.encode("utf-8")
    ).hexdigest()


    record = APIKey.query.filter_by(
        key_hash=digest,
        revoked=False
    ).first()


    if not record:

        return None


    record.last_used_at = (
        datetime.utcnow()
    )

    db.session.commit()


    return record


def api_key_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        key = authenticate_api_key()


        if not key:

            return jsonify({

                "error": {

                    "message":
                        "Invalid API key.",

                    "type":
                        "authentication_error"
                }

            }), 401


        request.localgpt_api_key = (
            key
        )


        return function(
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# OPENAI-COMPATIBLE MODELS API
# ============================================================

@app.route(
    "/v1/models",
    methods=["GET"]
)
@api_key_required
def openai_models():

    data = []


    for model_id, model in MODELS.items():

        if model["path"].exists():

            data.append({

                "id":
                    model_id,

                "object":
                    "model",

                "created":
                    0,

                "owned_by":
                    "localgpt"
            })


    return jsonify({

        "object":
            "list",

        "data":
            data
    })


# ============================================================
# OPENAI-COMPATIBLE CHAT API
# ============================================================

@app.route(
    "/v1/chat/completions",
    methods=["POST"]
)
@api_key_required
def openai_chat():

    data = request.get_json(
        silent=True
    ) or {}


    model_id = data.get(
        "model",
        DEFAULT_MODEL
    )


    messages = data.get(
        "messages",
        []
    )


    if model_id not in MODELS:

        return jsonify({

            "error": {

                "message":
                    "Unknown model.",

                "type":
                    "invalid_request_error"
            }

        }), 400


    if not isinstance(
        messages,
        list
    ) or not messages:

        return jsonify({

            "error": {

                "message":
                    "messages must be "
                    "a non-empty array.",

                "type":
                    "invalid_request_error"
            }

        }), 400


    cleaned = []


    for message in messages:

        if not isinstance(
            message,
            dict
        ):

            continue


        role = message.get(
            "role"
        )


        content = message.get(
            "content"
        )


        if (
            role in (
                "system",
                "user",
                "assistant"
            )
            and isinstance(
                content,
                str
            )
        ):

            cleaned.append({

                "role":
                    role,

                "content":
                    content
            })


    if not cleaned:

        return jsonify({

            "error": {

                "message":
                    "No valid messages "
                    "were provided.",

                "type":
                    "invalid_request_error"
            }

        }), 400


    try:

        temperature = float(
            data.get(
                "temperature",
                0.7
            )
        )


        max_tokens = int(
            data.get(
                "max_tokens",
                1024
            )
        )


        response_text = (
            generate_completion(

                cleaned,

                model_id,

                max_tokens=
                    max_tokens,

                temperature=
                    temperature
            )
        )


        completion_id = (
            "chatcmpl-local-"
            + uuid.uuid4().hex
        )


        return jsonify({

            "id":
                completion_id,

            "object":
                "chat.completion",

            "created":
                int(time.time()),

            "model":
                model_id,

            "choices": [

                {

                    "index":
                        0,

                    "message": {

                        "role":
                            "assistant",

                        "content":
                            response_text
                    },

                    "finish_reason":
                        "stop"
                }
            ],

            "usage": {

                # Exact token accounting can
                # be added later.

                "prompt_tokens":
                    0,

                "completion_tokens":
                    0,

                "total_tokens":
                    0
            }
        })


    except Exception as error:

        return jsonify({

            "error": {

                "message":
                    str(error),

                "type":
                    "server_error"
            }

        }), 500


# ============================================================
# START DEFAULT MODEL
# ============================================================

def start_default_model():

    try:

        model_manager.start_model(
            DEFAULT_MODEL
        )

    except Exception as error:

        print()
        print(
            "Default model failed:"
        )
        print(error)
        print()


# ============================================================
# OPEN BROWSER
# ============================================================

def open_browser():

    time.sleep(2)

    try:

        webbrowser.open(
            APP_URL
        )

    except Exception as error:

        print(
            "Browser error:",
            error
        )


# ============================================================
# SHUTDOWN
# ============================================================

def shutdown():

    try:

        model_manager.stop()

    except Exception:

        pass


atexit.register(
    shutdown
)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    with app.app_context():

        db.create_all()


    print()
    print("=" * 55)
    print("                    LocalGPT")
    print("=" * 55)


    for model_id, model in MODELS.items():

        status = (
            "FOUND"
            if model["path"].exists()
            else "MISSING"
        )


        print(
            f"{model['name']:<25}"
            f"{status}"
        )


    print("-" * 55)

    print(
        f"Database: {DATABASE_PATH}"
    )

    print(
        f"Interface: {APP_URL}"
    )

    print("=" * 55)
    print()


    model_thread = threading.Thread(

        target=start_default_model,

        daemon=True
    )


    model_thread.start()


    browser_thread = threading.Thread(

        target=open_browser,

        daemon=True
    )


    browser_thread.start()


    app.run(

        host=APP_HOST,

        port=APP_PORT,

        debug=False,

        use_reloader=False,

        threaded=True
    )