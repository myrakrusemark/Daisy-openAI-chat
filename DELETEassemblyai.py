import pyaudio
import websockets
import asyncio
import base64
import json

class AssemblyAISpeechRecognizer:
    def __init__(self, auth_key, sample_rate=16000, frames_per_buffer=3200):
        self.auth_key = auth_key
        self.sample_rate = sample_rate
        self.frames_per_buffer = frames_per_buffer
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = sample_rate
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frames_per_buffer
        )
        self.url = f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={self.sample_rate}"
        self.ws = None

    async def connect(self):
        self.ws = await websockets.connect(
            self.url,
            extra_headers=(("Authorization", self.auth_key),),
            ping_interval=5,
            ping_timeout=20
        )
        await asyncio.sleep(0.1)
        session_begins = await self.ws.recv()
        print(session_begins)

    async def disconnect(self):
        await self.ws.close()
        self.p.terminate()

    async def send_audio(self, stream):
        while True:
            try:
                data = stream.read(self.frames_per_buffer)
                data = base64.b64encode(data).decode("utf-8")
                json_data = json.dumps({"audio_data":str(data)})
                await self.ws.send(json_data)
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"Connection closed with error code {e.code}: {e.reason}")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                break
            await asyncio.sleep(0.01)

    async def receive_text(self):
        while True:
            try:
                result_str = await self.ws.recv()
                text = json.loads(result_str)['text']
                yield text
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"Connection closed with error code {e.code}: {e.reason}")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                break

    async def transcribe(self):
        async with self.ws:
            send_task = asyncio.create_task(self.send_audio(self.stream))
            receive_task = asyncio.create_task(self.receive_text())
            await asyncio.gather(send_task, receive_task)
