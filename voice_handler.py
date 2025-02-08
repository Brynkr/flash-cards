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


def is_alphabet_char(char):
    if ord(char) <= constants.UNICODE_ALPHABET_LOWERCASE_END \
     and ord(char) >= constants.UNICODE_ALPHABET_LOWERCASE_START:
        return True
    if ord(char) <= constants.UNICODE_ALPHABET_UPPERCASE_END \
     and ord(char) >= constants.UNICODE_ALPHABET_UPPERCASE_START:
        return True

    return False


class VoiceHandler:
    def __init__(self):
        self._is_enabled = False
        self._play_english = False

        self._pyht_client = Client(user_id=constants.PLAYHT_USER_ID,
                                   api_key=constants.PLAYHT_API_KEY)

        self._pyht_chinese_options = TTSOptions(voice=constants.PLAYHT_CHINESE_VOICE,
                                                 language=Language("mandarin"), speed=0.6)

        self._pyht_english_options = TTSOptions(voice=constants.PLAYHT_ENGLISH_VOICE,
                                                language=Language("english"), speed=0.6)


    def enable(self):
        self._is_enabled = True
    def disable(self):
        self._is_enabled = False

    @property
    def is_enabled(self):
        return self._is_enabled
    

    def play_audio_files(self, card_english):
        if self._play_english:
            en_audio_name = self.parse_audio_filename(card_english, "_en")
            self.play_audio_file(en_audio_name)

        cn_audio_name = self.parse_audio_filename(card_english, "_cn")
        self.play_audio_file(cn_audio_name)


    def play_audio_file(self, audio_name):
        for filename in os.listdir(constants.AUDIO_PATH):
            if filename == audio_name:
                p = vlc.MediaPlayer("{0}/{1}".format(constants.AUDIO_PATH, filename))
                p.play()
                return
        print("Couldn't find an audio file for file: {}".format(audio_name))


    def parse_audio_filename(self, text, suffix="_cn"):
        for char in text:
            if not is_alphabet_char(char):
                print("replacing char: {} with _".format(char))
                text = text.replace(char, "_")
        return "{0}{1}.mp3".format(text, suffix)


    def write_tts_file(self, text_to_voice, filename, language="chinese"):
        if language == "english":
            print("Writing PlayHT TTS English file - ttv: {} filename: {}".format(text_to_voice, filename))
            pyht_options = self._pyht_english_options
        elif language == "chinese":
            print("Writing PlayHT TTS Chinese file - ttv: {} filename: {}".format(text_to_voice, filename))
            pyht_options = self._pyht_chinese_options

        try:
            with open(filename, "wb") as audio_file:
                for chunk in self._pyht_client.tts(text_to_voice, pyht_options, voice_engine=constants.PLAYHT_VOICE_ENGINE):
                    audio_file.write(chunk)
        except Exception as e:
            print("Writing TTS file: {0} failed. Error: {1}".format(filename, e))
            return

        print("Audio saved as {}".format(filename))


    def generate_audio_files(self, deck, window):
        generated_count = 0
        card_count = len(deck.cards)
        existing_filenames = os.listdir(constants.AUDIO_PATH)

        for card in deck.cards:
            en_filename = self.parse_audio_filename(card.english, "_en")
            if en_filename not in existing_filenames:
                self.write_tts_file(card.english, "{0}/{1}".format(constants.AUDIO_PATH, en_filename), "english")

            cn_filename = self.parse_audio_filename(card.english, "_cn")
            if cn_filename not in existing_filenames:
                self.write_tts_file(card.hanzi, "{0}/{1}".format(constants.AUDIO_PATH, cn_filename), "chinese")

            generated_count += 1
            window["GEN-AUDIO"].update(current_count=generated_count)
            window["GEN-AUDIO-TEXT"].update(value="Generating audio {}/{}".format(generated_count, card_count))


