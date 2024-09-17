import streamlit as st
import speech_recognition as sr
from openai import OpenAI
from prompts import get_prompt
from helpers import clean_text_for_tts
import os
from playsound import playsound
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchResults
import ollama
import uuid
from ollama_chat import OllamaChatClient
from typing import Optional, List, Dict


def select_model() -> str:
    """
    Displays a select box in the Streamlit sidebar to choose a model.
    Returns the selected model name.
    """
    with st.sidebar:
        # available_models = [
        #    model["name"].split(":")[0] for model in ollama.list()["models"] if "gemma" not in model["name"]
        available_models = ["llama3.1", "mistral-nemo"]
        model_id = st.selectbox("Select model to use", sorted(available_models))
    return model_id


# Helper functions for speech recognition and text-to-speech
def recognize_speech_from_microphone() -> str:
    """
    Listens to the microphone and uses a speech recognition model to transcribe speech.
    Returns the transcribed text or an error message in case of failure.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)

    try:
        text = r.recognize_whisper(audio)
        return text
    except sr.UnknownValueError:
        st.error("Sorry, I did not understand that.")
        return ""
    except sr.RequestError as e:
        st.error(f"Could not request results; {e}")
        return ""


def get_voice_input() -> str:
    """
    Provides a button to capture voice input and displays a spinner during listening.
    Returns the transcribed text from the microphone.
    """
    if st.button("Speak"):
        with st.spinner("Listening..."):
            return recognize_speech_from_microphone()
    st.info("Press Speak...")
    return ""


def speak_text(text: str) -> None:
    """
    Uses the system's text-to-speech capabilities to speak the provided text.
    """
    output_file = "response.mp4"
    command = f"say -o {output_file} --data-format=LEF32@22050 {text}"
    os.system(command)
    playsound(output_file)
    os.remove(output_file)


def get_response_from_ollama(
    client: OllamaChatClient, model_id: str, model_params: dict, messages: List[Dict]
) -> str:
    """
    Interacts with the local Ollama model and retrieves a response based on the conversation history.
    """
    try:
        response = client.chat.completions.create(
            model=model_id, messages=messages, **model_params, stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error communicating with Ollama model: {e}")
        return "Sorry, I couldn't generate a response."


def display_chat_history(history: List[Dict]) -> None:
    """
    Displays the chat history in the Streamlit chat interface.
    """
    for message in history:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


def update_session_state(system_prompt: str) -> None:
    """
    Initializes session state variables if they don't exist.
    """
    if "history" not in st.session_state:
        st.session_state.history = [{"role": "system", "content": system_prompt}]
    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid.uuid4()


def main() -> None:
    """
    Main function to run the Streamlit app, handle user inputs, and interact with the Ollama model.
    """
    # Streamlit app structure
    st.title("Voice Chat with Local LLMS")
    st.markdown(
        """
        <style>
            .st-emotion-cache-1c7y2kd {
                flex-direction: row-reverse;
                text-align: right;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Model selection and initialization
    model_id = select_model()
    model_params = {"temperature": 0.0, "top_p": 0.0}

    st.write("Click the button below and start speaking...")
    input_method = st.radio("Input Method", ["Text", "Voice"])

    if input_method == "Voice":
        user_input = get_voice_input()
    else:
        user_input = st.chat_input("How can I help you today?")

    # System prompt and session state initialization
    system_prompt = get_prompt()
    update_session_state(system_prompt)

    # Display chat history
    display_chat_history(st.session_state.history)

    if not user_input:
        st.stop()

    # Process user input
    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.history.append({"role": "user", "content": user_input})
    messages = [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.history
    ]

    # Get response from the local model
    ollama_chat_client = OllamaChatClient(
        model_id, st.session_state.session_id, model_params=model_params
    )
    response = ollama_chat_client.get_completion(messages)

    st.session_state.history.append({"role": "assistant", "content": response})

    # Display the assistant's response
    with st.chat_message("assistant"):
        if "```" in response:
            st.text(response)
        else:
            st.markdown(response)

    # Speak the response
    text_for_tts = clean_text_for_tts(response)
    if text_for_tts:
        speak_text(text_for_tts)


if __name__ == "__main__":
    main()
