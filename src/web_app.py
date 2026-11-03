
import os

import streamlit as st
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Load environment variables
load_dotenv()

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
AGENT_NAME = os.getenv("AGENT_NAME")

# Page configuration
st.set_page_config(
    page_title="Spotify AI Assistant",
    page_icon="🎧",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.stApp {
    background-color: #121212;
}

h1, h2, h3 {
    color: #1DB954;
}

[data-testid="stSidebar"] {
    background-color: #202020;
}

.stChatMessage {
    border-radius: 12px;
}

div.stButton > button {
    background-color: #1DB954;
    color: white;
    border-radius: 20px;
    border: none;
}

div.stButton > button:hover {
    background-color: #1ed760;
    color: white;
}
</style>
""", unsafe_allow_html=True)


# Connect to the Foundry agent
@st.cache_resource
def connect_to_agent():
    if not PROJECT_ENDPOINT or not AGENT_NAME:
        raise ValueError(
            "PROJECT_ENDPOINT and AGENT_NAME must be configured."
        )

    credential = DefaultAzureCredential()

    project = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=credential
    )

    openai_client = project.get_openai_client(
        agent_name=AGENT_NAME
    )

    return openai_client


# Initialize chat session
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None


# Sidebar
with st.sidebar:
    st.title("🎧 Spotify AI")
    st.caption("Your personal music assistant")

    st.divider()

    st.subheader("Music Assistant")

    st.markdown("""
    Discover music, explore artists,
    understand genres and analyze
    your musical preferences.
    """)

    if st.button("🗑️ New conversation"):
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.rerun()

    st.divider()

    st.caption("Powered by Microsoft Foundry")


# Main page
st.title("🎵 Spotify AI Assistant")

st.markdown(
    "Discover new music. Analyze your taste. Explore artists."
)

st.divider()

# Welcome message
if not st.session_state.messages:
    st.markdown("### Welcome to your music assistant! 🎶")
    st.write("Try asking me something like:")

    st.markdown("""
    - Recommend artists similar to Arctic Monkeys.
    - Explain the difference between indie rock and alternative rock.
    - Create a playlist for studying.
    - Analyze my musical preferences.
    """)


# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Chat input
prompt = st.chat_input("Ask me anything about music...")

if prompt:
    # Display user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("Discovering music... 🎧"):
            try:
                client = connect_to_agent()

                # Create a Foundry conversation if needed
                if st.session_state.conversation_id is None:
                    conversation = client.conversations.create()
                    st.session_state.conversation_id = conversation.id

                response = client.responses.create(
                    conversation=st.session_state.conversation_id,
                    input=prompt
                )

                answer = response.output_text

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as error:
                st.error(
                    "Could not connect to the music assistant. "
                    "Check your Azure login, project endpoint "
                    "and agent configuration."
                )
                st.exception(error)
