from pyht import Client
from pyht.client import TTSOptions
from pyht.client import Language

import vlc

import PySimpleGUI

import requests
import json
import os
import signal
import subprocess
from pydub import AudioSegment
import simpleaudio
import constants


#TODO - english language also generated for the card

def is_alphabet_char(char):
    if ord(char) <= constants.UNICODE_ALPHABET_LOWERCASE_END and ord(char) >= constants.UNICODE_ALPHABET_LOWERCASE_START:
        return True
    if ord(char) <= constants.UNICODE_ALPHABET_UPPERCASE_END and ord(char) >= constants.UNICODE_ALPHABET_UPPERCASE_START:
        return True

    return False


class VoiceHandler:
    def __init__(self):
        self._pyht_client = Client(user_id=constants.PLAYHT_USER_ID,
                                   api_key=constants.PLAYHT_API_KEY)

        self._pyht_options = TTSOptions(voice=constants.PLAYHT_VOICE,
                                        language=Language("mandarin"),
                                        speed=0.6)


    def play_audio_file(self, card_english):
        audio_name = self.parse_audio_filename(card_english)
        for filename in os.listdir(constants.AUDIO_PATH):
            if filename == audio_name:
                p = vlc.MediaPlayer(constants.AUDIO_PATH + "/" + filename)
                p.play()
                return
        print("Couldn't find an audio file for filename: {}".format(audio_name))


    def parse_audio_filename(self, card_english):
        filename = card_english
        for char in filename:
            if not is_alphabet_char(char):
                print("replacing char: {} with _".format(char))
                filename = filename.replace(char, "_")
        return filename + ".mp3"


    def playht_write_tts_chinese_file(self, text_to_voice, filename):
        print("Writing PlayHT TTS Chinese file - ttv: {} filename: {}".format(text_to_voice, filename))
        with open(filename, "wb") as audio_file:
            for chunk in self._pyht_client.tts(text_to_voice, self._pyht_options, voice_engine=constants.PLAYHT_VOICE_ENGINE):
                audio_file.write(chunk)
        print("Audio saved as {}".format(filename))


    def generate_audio_files(self, deck, window):
        generated_count = 0
        card_count = len(deck.cards)
        for card in deck.cards:
            filename = self.parse_audio_filename(card.english)
            self.playht_write_tts_chinese_file(card.hanzi, "{0}{1}.mp3".format(constants.AUDIO_PATH, filename))
            generated_count += 1
            window["GEN-AUDIO"].update(current_count=generated_count)
            window["GEN-AUDIO-TEXT"].update(value="Generating audio {}/{}".format(generated_count, card_count))


