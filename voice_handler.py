import requests
import json
import os
import signal
import subprocess
from pydub import AudioSegment
import simpleaudio
import constants


class VoiceHandler:
    def __init__(self):
        self.tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{constants.ELEVEN_CHINESE_VOICE_ID}/stream"
        self.headers = { "Accept": "application/json",
                         "xi-api-key": constants.ELEVEN_API_KEY }
        self.vlc = None


    def writeTTSChineseFile(self, text_to_voice):
        data = { "text": text_to_voice,
                 "model_id": "eleven_multilingual_v2",
                 "voice_settings": { "stability": 0.5,
                                     "similarity_boost": 0.8,
                                     "style": 0.0,
                                     "use_speaker_boost": True } }

        # Make the POST request to the TTS API with headers and data, enabling streaming response
        response = requests.post(self.tts_url, headers=self.headers, json=data, stream=True)
        if response.ok:
            with open("./output.mp3", "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            print("Audio stream saved successfully.")
            return True
        else:
            print(response.text)
            return False


    def playWithVLC(self, path):
        if os.path.exists(path):
            # subprocess.Popen(["/Applications/VLC.app/Contents/MacOS/VLC", path])

            # The os.setsid() is passed in the argument preexec_fn so
            # it's run after the fork() and before  exec() to run the shell.
            self.vlc = subprocess.Popen(["/Applications/VLC.app/Contents/MacOS/VLC", path], 
                                   stdout=subprocess.PIPE, 
                                   shell=True,
                                   preexec_fn=os.setsid)
            print("Opened and playing with VLC file: '{}'".format(path))
        else:
            print("path '{}' doesn't exist. Unable to play file.".format(path))


    def closeVLC(self):
        try:
            print("Killing VLC process..")
            os.killpg(os.getpgid(self.vlc.pid), signal.SIGTERM)
        except:
            print("No VLC process to kill?..")



        # TODO - close process (VLC) after playing

