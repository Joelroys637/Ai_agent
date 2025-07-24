import streamlit as st
import asyncio
import base64
import json
import os
import pyaudio
from websockets.asyncio.client import connect

# Load and embed background gif
'''def get_base64_gif(file_path):
    with open(file_path, "rb") as f:
        gif_data = f.read()
    return base64.b64encode(gif_data).decode()

gif_base64 = get_base64_gif("D:/webapppython/SPEECH_AI/ai1.gif")
st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/gif;base64,{gif_base64}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    .login-form {{
        background-color: rgba(0, 0, 0, 0.6);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        max-width: 400px;
        margin: auto;
    }}
    h2 {{ color: #fff; }}
    </style>
""", unsafe_allow_html=True)'''

class GeminiVoiceAssistant:
    def __init__(self):
        self.user_name = "Leo Joel"
        self.assistant_name = "jarvis"
        self._audio_queue = asyncio.Queue()
        self._model = "gemini-2.0-flash-exp"
        self._api_key = "AIzaSyCL8kDsUZHx4hrXXZAin21ejP_nR0XASNo"
        self._uri = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={self._api_key}"

        # Audio settings
        self._FORMAT = pyaudio.paInt16
        self._CHANNELS = 1
        self._CHUNK = 512
        self._RATE = 16000

    async def _connect_to_gemini(self):
        return await connect(
            self._uri, additional_headers={"Content-Type": "application/json"}
        )

    async def _start_audio_streaming(self):
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._capture_audio())
            tg.create_task(self._stream_audio())
            tg.create_task(self._play_response())

    async def _capture_audio(self):
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=self._FORMAT,
            channels=self._CHANNELS,
            rate=self._RATE,
            input=True,
            frames_per_buffer=self._CHUNK,
        )

        while True:
            data = await asyncio.to_thread(stream.read, self._CHUNK)
            await self._ws.send(json.dumps({
                "realtime_input": {
                    "media_chunks": [
                        {
                            "data": base64.b64encode(data).decode(),
                            "mime_type": "audio/pcm"
                        }
                    ]
                }
            }))

    async def _stream_audio(self):
        async for msg in self._ws:
            response = json.loads(msg)

            # Play audio response
            try:
                audio_data = response["serverContent"]["modelTurn"]["parts"][0]["inlineData"]["data"]
                self._audio_queue.put_nowait(base64.b64decode(audio_data))
            except KeyError:
                pass

            # Display assistant text responses
            try:
                text_response = response["serverContent"]["modelTurn"]["parts"][0]["text"]
                if text_response:
                    st.success(f"{self.assistant_name}: {text_response}")
            except KeyError:
                pass

            # Detect end of turn
            if response.get("serverContent", {}).get("turnComplete"):
                pass

    async def _play_response(self):
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=self._FORMAT, channels=self._CHANNELS, rate=24000, output=True
        )
        while True:
            data = await self._audio_queue.get()
            await asyncio.to_thread(stream.write, data)

    async def start(self):
        self._ws = await self._connect_to_gemini()
        await self._ws.send(json.dumps({
            "setup": {
                "model": f"models/{self._model}",
                "system_instruction": {
                    "parts": [
                        {
                        "text": f"""
                        You are a friendly Tamil-speaking AI voice assistant named {self.assistant_name}.
                        The user speaking to you is {self.user_name}.
                        Understand both Tamil and English.
                        Always reply in the same language that the user used.
                        Be friendly and helpful. Speak in female voice.
                        """
                        }
                    ]
                }
            }
        }))
        await self._ws.recv(decode=False)
        st.title("🎙️ Gemini Voice Assistant")
        st.subheader(f"Hello {self.user_name}, you can start speaking to {self.assistant_name}.")
        await self._start_audio_streaming()

# Run app
if __name__ == "__main__":
    client = GeminiVoiceAssistant()
    asyncio.get_event_loop().run_until_complete(client.start())
