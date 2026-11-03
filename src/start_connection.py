import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

load_dotenv()

project = AIProjectClient(
    endpoint=os.environ["PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

# Cliente OpenAI ya "ligado" a nuestro agente del portal
openai = project.get_openai_client(agent_name=os.environ["AGENT_NAME"])

conversation = openai.conversations.create()
response = openai.responses.create(
    conversation=conversation.id,
    input="Hola, ¿qué puedes hacer por mí?",
)
print(response.output_text)