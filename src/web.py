import os
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

load_dotenv()

AGENT_NAME = os.environ["AGENT_NAME"]
AGENT_REF = {"agent_reference": {"name": AGENT_NAME, "type": "agent_reference"}}

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------- Conexión con el agente de Foundry ----------
project = AIProjectClient(
    endpoint=os.environ["PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
openai = project.get_openai_client()


def ask_agent(conversation_id, user_input):
    response = openai.responses.create(
        conversation=conversation_id, input=user_input, extra_body=AGENT_REF
    )
    # Aprobaciones de MCP (el MCP solo LEE datos)
    while True:
        requests = [o for o in response.output if o.type == "mcp_approval_request"]
        if not requests:
            return response
        approvals = [
            {"type": "mcp_approval_response", "approval_request_id": r.id, "approve": True}
            for r in requests
        ]
        response = openai.responses.create(
            conversation=conversation_id, input=approvals, extra_body=AGENT_REF
        )


DOWNLOADED_IDS = set()  # archivos ya descargados (para no repetirlos en cada respuesta)
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp")


def _save_container_file(container_id, file_id, filename):
    data = openai.containers.files.content.retrieve(file_id=file_id, container_id=container_id)
    path = OUTPUT_DIR / Path(filename).name
    path.write_bytes(data.read())
    DOWNLOADED_IDS.add(file_id)
    print(f"[charts] saved {path}")
    return path


def download_files(response):
    """Descarga los gráficos/archivos generados por Code Interpreter."""
    paths = []
    container_ids = set()

    # Depuración: qué devuelve el agente
    print("[debug] output items:", [item.type for item in response.output])

    for item in response.output:
        # 1) Contenedor donde Code Interpreter ejecutó el código
        if item.type == "code_interpreter_call" and getattr(item, "container_id", None):
            container_ids.add(item.container_id)
        # 2) Archivos enlazados explícitamente en la respuesta
        if item.type == "message":
            for content in item.content:
                for ann in getattr(content, "annotations", None) or []:
                    if getattr(ann, "type", "") == "container_file_citation":
                        container_ids.add(ann.container_id)
                        if ann.file_id not in DOWNLOADED_IDS:
                            paths.append(_save_container_file(ann.container_id, ann.file_id, ann.filename))

    # 3) Archivos creados en el contenedor aunque el agente no los haya enlazado
    for container_id in container_ids:
        for f in openai.containers.files.list(container_id=container_id):
            if f.id in DOWNLOADED_IDS or getattr(f, "source", None) == "user":
                continue
            paths.append(_save_container_file(container_id, f.id, f.path))

    return paths


# ---------- Lógica del chat ----------
def add_user_message(message, history):
    if not message or not message.strip():
        return "", history
    return "", history + [{"role": "user", "content": message.strip()}]


def bot_reply(history, conversation_id):
    if not history or history[-1]["role"] != "user":
        return history, conversation_id
    message = history[-1]["content"]

    try:
        if conversation_id is None:
            conversation_id = openai.conversations.create().id
        response = ask_agent(conversation_id, message)
    except Exception as e:
        history.append({
            "role": "assistant",
            "content": "⚠️ Could not connect to the music assistant. Check your Azure login, "
                       f"project endpoint and agent configuration.\n\n`{e}`",
        })
        return history, conversation_id

    answer = response.output_text or "(The agent returned no text)"
    if response.usage:
        answer += (f"\n\n<sub>🔢 tokens · input {response.usage.input_tokens}"
                   f" · output {response.usage.output_tokens}</sub>")
    history.append({"role": "assistant", "content": answer})

    try:
        for path in download_files(response):
            if path.suffix.lower() in IMAGE_EXT:
                history.append({"role": "assistant", "content": gr.Image(str(path))})
            else:
                history.append({"role": "assistant", "content": gr.File(str(path))})
    except Exception as e:
        history.append({"role": "assistant", "content": f"(Could not download the generated file: {e})"})

    return history, conversation_id


def new_conversation():
    return [], None


# ---------- Estilo (mismos colores que la versión Streamlit) ----------
GREEN = "#1DB954"
GREEN_HOVER = "#1ED760"
BLACK = "#121212"
SECONDARY = "#202020"
INPUT = "#2A2A2A"
BORDER = "#2E2E2E"
GREY_TEXT = "#B3B3B3"


def both(**kwargs):
    """Aplica cada color al modo claro y al oscuro."""
    out = {}
    for key, value in kwargs.items():
        out[key] = value
        out[f"{key}_dark"] = value
    return out


theme = gr.themes.Base(
    primary_hue=gr.themes.colors.green,
    neutral_hue=gr.themes.colors.gray,
    font=[gr.themes.GoogleFont("Montserrat"), "Arial", "sans-serif"],
).set(**both(
    body_background_fill=BLACK,
    body_text_color="#FFFFFF",
    body_text_color_subdued=GREY_TEXT,
    background_fill_primary=BLACK,
    background_fill_secondary=SECONDARY,
    block_background_fill=SECONDARY,
    block_border_color=BORDER,
    border_color_primary=BORDER,
    input_background_fill=INPUT,
    button_primary_background_fill=GREEN,
    button_primary_background_fill_hover=GREEN_HOVER,
    button_primary_text_color="#000000",
    button_secondary_background_fill=INPUT,
    button_secondary_background_fill_hover="#3E3E3E",
    button_secondary_text_color="#FFFFFF",
))

CSS = f"""
footer {{ display: none !important; }}
.gradio-container {{ max-width: 1100px !important; margin: 0 auto !important; }}
h1, h2, h3 {{ color: {GREEN} !important; }}
#tagline p {{ color: {GREY_TEXT} !important; font-size: 1.05rem; }}
.sidebar {{ background: {SECONDARY} !important; border-right: 1px solid {BORDER} !important; }}
#chatbot {{ border-radius: 16px !important; border: 1px solid {BORDER} !important; }}
.message.user, [data-testid="user"] {{
    background: {GREEN} !important; color: #000000 !important;
    border: none !important; border-radius: 14px !important;
}}
.message.user *, [data-testid="user"] * {{ color: #000000 !important; }}
.message.bot, [data-testid="bot"] {{
    background: {INPUT} !important; color: #FFFFFF !important;
    border: 1px solid {BORDER} !important; border-radius: 14px !important;
}}
button {{ border-radius: 999px !important; font-weight: 700 !important; }}
#msg textarea {{ border-radius: 999px !important; padding: 12px 18px !important; }}
"""

WELCOME = """
### Welcome to your music assistant! 🎶
Try asking me something like:
- Recommend artists similar to Arctic Monkeys.
- Explain the difference between indie rock and alternative rock.
- Create a playlist for studying.
- Analyze my musical preferences.
"""

# ---------- Interfaz ----------
with gr.Blocks(theme=theme, css=CSS, title="Spotify AI Assistant") as demo:
    conversation_state = gr.State(None)

    with gr.Sidebar():
        gr.Markdown("## 🎧 Spotify AI\nYour personal music assistant")
        gr.Markdown("---\n### Music Assistant\nDiscover music, explore artists, "
                    "understand genres and analyze your musical preferences.")
        new_btn = gr.Button("🗑️ New conversation", variant="primary")
        gr.Markdown("---\n<sub>Powered by Microsoft Foundry</sub>")

    gr.Markdown("# 🎵 Spotify AI Assistant")
    gr.Markdown("Discover new music. Analyze your taste. Explore artists.", elem_id="tagline")

    chatbot = gr.Chatbot(
        type="messages",
        elem_id="chatbot",
        height=520,
        show_label=False,
        placeholder=WELCOME,
    )

    with gr.Row(equal_height=True):
        msg = gr.Textbox(
            placeholder="Ask me anything about music...",
            show_label=False, container=False, scale=8, autofocus=True, elem_id="msg",
        )
        send_btn = gr.Button("Send ➤", variant="primary", scale=1)

    gr.Examples(
        examples=[
            "Me gusta Arctic Monkeys y The Strokes. Recomiéndame cinco grupos.",
            "Hazme una playlist para estudiar durante dos horas.",
            "¿Qué diferencias hay entre el indie rock y el alternative rock?",
            "What is the Discovery Ladder for Arctic Monkeys?",
        ],
        inputs=msg,
        label="Try one of these",
    )

    for trigger in (msg.submit, send_btn.click):
        trigger(add_user_message, [msg, chatbot], [msg, chatbot], queue=False).then(
            bot_reply, [chatbot, conversation_state], [chatbot, conversation_state]
        )
    new_btn.click(new_conversation, None, [chatbot, conversation_state])


if __name__ == "__main__":
    demo.launch(inbrowser=True, allowed_paths=[str(OUTPUT_DIR)])
