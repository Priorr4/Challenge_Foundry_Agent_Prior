import os
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

load_dotenv()

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

MENU = """
=========================================
       SPOTIFY AI ASSISTANT
=========================================
1. Discover new music
2. Analyze a music dataset
3. Explore musical genres
4. Ask a music question
5. Exit
"""

PROMPTS = {
    "1": "Tell me which artists or songs you like and I'll recommend new music: ",
    "2": "What do you want to analyze in the dataset? ",
    "3": "Which genre(s) do you want to explore? ",
    "4": "Ask your music question: ",
}

PREFIX = {
    "1": "MUSIC DISCOVERY request: ",
    "2": "DATASET ANALYSIS request (use Code Interpreter on the music dataset): ",
    "3": "GENRE EXPLORATION request (use the music knowledge base): ",
    "4": "",
}


def connect():
    """Autenticación (Entra ID) + conexión al agente creado en el portal."""
    project = AIProjectClient(
        endpoint=os.environ["PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
    )
    return project.get_openai_client(agent_name=os.environ["AGENT_NAME"])


def handle_mcp_approvals(openai, conversation_id, response):
    """Si un MCP pide aprobación, la preguntamos al usuario y respondemos."""
    while True:
        requests = [o for o in response.output if o.type == "mcp_approval_request"]
        if not requests:
            return response
        approvals = []
        for req in requests:
            ok = input(f"  🔧 The agent wants to use MCP tool '{req.name}'. Approve? (y/n): ")
            approvals.append({
                "type": "mcp_approval_response",
                "approval_request_id": req.id,
                "approve": ok.strip().lower() == "y",
            })
        response = openai.responses.create(conversation=conversation_id, input=approvals)


def download_files(openai, response):
    """Descarga los gráficos/archivos generados por Code Interpreter."""
    for item in response.output:
        if item.type != "message":
            continue
        for content in item.content:
            for ann in getattr(content, "annotations", None) or []:
                if ann.type == "container_file_citation":
                    data = openai.containers.files.content.retrieve(
                        file_id=ann.file_id, container_id=ann.container_id
                    )
                    path = OUTPUT_DIR / ann.filename
                    path.write_bytes(data.read())
                    print(f"  📁 File saved: {path}")


def main():
    openai = connect()
    conversation = openai.conversations.create()
    print("Hello! Welcome to your personal music assistant.")

    while True:
        print(MENU)
        option = input("Choose an option: ").strip()
        if option == "5":
            print("Goodbye! 🎶")
            break
        if option not in PROMPTS:
            print("Invalid option.")
            continue

        question = input(PROMPTS[option]).strip()
        if not question:
            continue

        print("\n⏳ Thinking...\n")
        try:
            response = openai.responses.create(
                conversation=conversation.id,
                input=PREFIX[option] + question,
            )
            response = handle_mcp_approvals(openai, conversation.id, response)
            print("🎧 " + response.output_text)
            try:
                download_files(openai, response)
            except Exception as e:
                print(f"  (Could not download generated files: {e})")
            if response.usage:
                print(f"\n  [tokens] input={response.usage.input_tokens} "
                      f"output={response.usage.output_tokens}")
        except Exception as e:
            print(f"❌ Error talking to the agent: {e}")


if __name__ == "__main__":
    main()