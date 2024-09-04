import streamlit as st
import time
import vertexai
import base64
from vertexai.preview.vision_models import ImageGenerationModel
from vertexai.generative_models import GenerativeModel, Part, SafetySetting, FinishReason, FunctionDeclaration, Tool, Content
import vertexai.preview.generative_models as generative_models

from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
from google.cloud import texttospeech


YOUR_PROJECT_ID = "south-emea-ml-tools"
vertexai.init(project=YOUR_PROJECT_ID, location="us-central1")
tts_client = texttospeech.TextToSpeechClient()


system_instruction = """You are a financial advisor for ING. Keep it conversational like speaking."""
model = GenerativeModel(
    "gemini-1.5-flash-001",
    system_instruction=[system_instruction]
)

if "messages" not in st.session_state:
    st.session_state.messages = []

####### Functions ########

def start_processing(audio_path):
    #Transcribe audio
    transcribed_text = transcribe_audio(audio_path)
    st.session_state.messages.append({"role": "user", "content": transcribed_text})
    # Gemini response
    get_gemini_response()
    last_message_dict = st.session_state.messages[-1]
    last_message = last_message_dict["content"]
    # Text to speech Response
    text_to_speech_response(last_message)

def record_audio():
    audio_bytes = audio_recorder()
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mp3")
        return audio_bytes

def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            st.error("Sorry, I couldn't understand that.")
            return None
        except sr.RequestError as e:
            st.error("There was an error with speech recognition")
            return None

def get_gemini_response():
    print("Getting Gemini response...")
    contentHistory = [
        Content(role=(m['role'] if m['role'] != 'assistant' else 'model'), parts=[Part.from_text(m['content'])])
        for m in st.session_state.messages[:-1]
    ]
    chat = model.start_chat(
        history=contentHistory
    )
    last_message = st.session_state.messages[-1]
    responses = chat.send_message(last_message["content"],stream=True)
    text_response = []
    for chunk in responses:
        text_response.append(chunk.text if hasattr(chunk, "text") and chunk.text else "")
    response = st.write_stream(text_response)
    st.session_state.messages.append({"role": "assistant", "content": response})

def text_to_speech_response(text):
    print("Text : " + str(text))
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", name="en-US-Casual-K"
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    audio_path = "temp_respnse_audio.mp3"
    with open(audio_path, "wb") as f:
        f.write(response.audio_content)
    autoplay_audio(audio_path)
    
def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("utf-8")
    md = f"""
    <audio autoplay>
    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
    st.markdown(md, unsafe_allow_html=True)


####### UI ########

st.markdown(
    """
    <style>
        .logo-text {
            font-weight: bold; /* Make text thicker */
            font-size: 24px;  /* Adjust the font size */
        }

        .logo-image {
            height: 60px; /* Adjust the logo height as needed */
            width: auto;  /* Maintain aspect ratio */
            margin-left: 10px; /* Add spacing between logo and text */
            vertical-align: middle; /* Vertically center the logo */
        }
    </style>

    <div style="display: flex; align-items: center;">
        <img class="logo-image" src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTzTY6KtRF4YiS9M6VIg7fljLqppoPbJ-mrLw&s" alt="Logo">
         <span class="logo-text">      </span>
        <img class="logo-image" src="https://www.boekhoudeninexcel.nl/wp-content/uploads/2014/09/ING_Logo.png" alt="Logo">
       
    </div>
    """,
    unsafe_allow_html=True,
)

st.title(f"ING Voice Assistant")

st.markdown(
    "This demo is created for the personalization meeting with ING 28/08/2024."
)

audio_bytes = audio_recorder()

if audio_bytes:
    st.write("User audio :")
    st.audio(audio_bytes, format="audio/mp3")
    audio_path = "temp_audio.mp3"
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)
    start_processing(audio_path)



# if prompt := st.chat_input("What is up?"):
#         st.session_state.messages.append({"role": "user", "content": prompt})
#         with st.chat_message("user"):
#             st.markdown(prompt)

#         contentHistory = [
#             Content(role=(m['role'] if m['role'] != 'assistant' else 'model'), parts=[Part.from_text(m['content'])])
#             for m in st.session_state.messages[:-1]
#         ]

#         with st.chat_message("assistant"):
#             chat = model.start_chat(
#                 history=contentHistory
#             )
#             last_message = st.session_state.messages[-1]
#             responses = chat.send_message(last_message["content"],stream=True)
#             text_response = []
#             for chunk in responses:
#                 text_response.append(chunk.text if hasattr(chunk, "text") and chunk.text else "")
#             response = st.write_stream(text_response)
#             print(response)
#         st.session_state.messages.append({"role": "assistant", "content": response})