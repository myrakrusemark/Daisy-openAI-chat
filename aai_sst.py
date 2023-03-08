import pyaudio
import websockets
import asyncio
import base64
import json
import play_sound
import threading
import time
import functions
import constants
import sys
import logging
import logging_setup


# Set up AssemblyAI API key and websocket endpoint
auth_key = "f7754f3d71ac422caf4cfc54bace4306"
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

# Define global variables
result_str = ""
new_result_str = ""
result_received = False

# Define async function to send and receive data
async def send_receive():
    # Set up PyAudio
    FRAMES_PER_BUFFER = 3200
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=FRAMES_PER_BUFFER
    )

    async with websockets.connect(
        URL,
        extra_headers=(("Authorization", auth_key),),
        ping_interval=5,
        ping_timeout=20
    ) as _ws:
        await asyncio.sleep(0.1)
        #print("Receiving SessionBegins ...")
        session_begins = await _ws.recv()
        #print(session_begins)
        print("AAI Listening ...")


        async def send():
            # Clear the audio buffer
            # This was originally to help Daisy from speaking over itself. Delete if no problem.
            #if stream.get_read_available() > 0:
            #    print("cleaning stream")
            #    stream.read(stream.get_read_available())

            logging.info("TTS Send start")
            #When a result is received, close the loop, allowing send_receive to finish (Let me diiiiieeeee)

            #Get the beep as CLOSE to the audio recorder as possible
            stop_event, thread = play_sound.play_sound_with_thread(constants.cwd+'beep.wav', 0.2)
            while result_received == False:
                try:
                    data = stream.read(FRAMES_PER_BUFFER)
                    data = base64.b64encode(data).decode("utf-8")
                    json_data = json.dumps({"audio_data":str(data)})
                    await _ws.send(json_data)
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"Connection closed with error code {e.code}: {e.reason}")
                    break
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    break
                await asyncio.sleep(0.01)
            logging.info("TTS Send done")
            return
        
        async def receive():
            logging.info("TTS Receive start")
            global result_str, result_received, new_result_str
            result_str = ""
            new_result_str = ""
            result_received = False
            while True:
                while result_received == False:
                    try:
                        new_result = await _ws.recv()
                        new_result_str = json.loads(new_result)['text']
                        if len(new_result_str) >= len(result_str):
                            result_str = new_result_str
                            # Move the cursor to the beginning of the last line
                            sys.stdout.write('\033[F')
                            # Clear the line
                            sys.stdout.write('\033[2K')
                            print("You: "+result_str)
                        else:
                            result_received = True
                            logging.info("TTS Receive done")
                            return
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(f"Connection closed with error code {e.code}: {e.reason}")
                        break
                    except Exception as e:
                        print(f"Unexpected error: {e}")
                        break
        
        send_result, receive_result = await asyncio.gather(send(), receive())



def speech_to_text():

    # Create an event object to signal the thread to stop
    stop_event = threading.Event()

    def watch_results():
        global result_received
        global result_str
        while not stop_event.is_set():
            if result_received:
                #print("Result received:", send_receive_py.result_str)
                result_received = False

                # Set the event to signal the thread to stop
                stop_event.set()

            time.sleep(0.1)

        # Join the thread to wait for it to finish
        #print("Joining thread...")
        thread.join()
        #print("Thread stopped")

        #Enable the ability to exit the program in a keyboard blocking state
        if not constants.args.hardware_mode:
            exit_string = functions.remove_non_alpha(result_str.lower())
            if exit_string == "exitprogram":
                print("Exiting program...")
                sys.exit(0)

        return result_str


    #Set up AssemblyAI send_receive loop
    def start_send_receive():
        asyncio.run(send_receive())

    # Create and start the send_receive thread
    thread = threading.Thread(target=start_send_receive)
    thread.start()

    # Start watching results in the main thread
    return watch_results()


