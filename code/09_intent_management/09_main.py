import logging
import yaml
import time
import pvporcupine
import pyaudio
import struct
import os
import sys
from vosk import Model, SpkModel, KaldiRecognizer
import json
import tinydb
import numpy as np
from usermgmt import UserMgmt

import io
#from snips_nlu import SnipsNLUEngine
#from snips_nlu.default_configs import CONFIG_DE

from TTS import Voice
import multiprocessing

from intentmgmt import IntentMgmt
logger = logging.getLogger(__name__)
# Zur besseren Übersicht wird das gloale Log-Level reduziert
logging.basicConfig(level=logging.ERROR)
logger.setLevel(logging.DEBUG)
logging.getLogger('comtypes._comobject').setLevel(logging.WARNING)

CONFIG_FILE = "config.yml"


# Spezieller Intent, der Zugriff auf va braucht	
def stop():
	if va.tts.is_busy():
		va.tts.stop()
		return "okay ich bin still"
	return "Ich sage doch garnichts"

class VoiceAssistant():

	def __init__(self):
		logger.info("Initialisiere VoiceAssistant...")
		
		logger.debug("Lese Konfiguration...")
		
		global CONFIG_FILE
		with open(CONFIG_FILE, "r") as ymlfile:
			self.cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
		if self.cfg:
			logger.debug("Konfiguration gelesen.")
		else:
			logger.debug("Konfiguration konnte nicht gelesen werden.")
			sys.exit(1)
		language = self.cfg['assistant']['language']
		if not language:
			language = "German"
		logger.info("Verwende Sprache %s", language)
			
		logger.debug("Initialisiere Wake Word Erkennung...")
		self.wake_words = self.cfg['assistant']['wakewords']
		if not self.wake_words:
			self.wake_words = ['bumblebee']
		logger.debug("Wake words are %s", ','.join(self.wake_words))
		self.porcupine = pvporcupine.create(keywords=self.wake_words)
		logger.debug("Wake Word Erkennung wurde initialisiert.")
		
		logger.debug("Initialisiere Audioeingabe...")
		self.pa = pyaudio.PyAudio()
		
		self.audio_stream = self.pa.open(
			rate=self.porcupine.sample_rate,
			channels=1,
			format=pyaudio.paInt16,
			input=True,
			frames_per_buffer=self.porcupine.frame_length,
			input_device_index=0)
		logger.debug("Audiostream geöffnet.")

		logger.info("Initialisiere Sprachausgabe...")
		self.tts = Voice()
		voices = self.tts.get_voice_keys_by_language(language)
		if len(voices) > 0:
			logger.info('Stimme %s gesetzt.', voices[0])
			self.tts.set_voice(voices[0])
		else:
			logger.warning("Es wurden keine Stimmen gefunden.")
		self.tts.say("Initialisierung abgeschlossen")
		logger.debug("Sprachausgabe initialisiert")
		
		logger.info("Initialisiere Spracherkennung...")
		stt_model = Model('./vosk-model-de-0.6')
		speaker_model = SpkModel('./vosk-model-spk-0.4')
		self.rec = KaldiRecognizer(stt_model, speaker_model, 16000)
		self.is_listening = False
		logger.info("Initialisierung der Spracherkennung abgeschlossen.")
		
		logger.info("Initialisiere Benutzerverwaltung...")
		self.user_management = UserMgmt(init_dummies=True)
		self.allow_only_known_speakers = self.cfg["assistant"]["allow_only_known_speakers"]
		logger.info("Benutzerverwaltung initialisiert")
		
		# Initialisiere den Chatbot. Ersetzen von ChatbotAI durch SNIPS-NLU		
		logger.info("Initialisiere Intent-Management...")
		self.intent_management = IntentMgmt()
		logger.info('%d intents geladen', self.intent_management.get_count())
	
	# Finde den besten Sprecher aus der Liste aller bekannter Sprecher aus dem User Management
	def __detectSpeaker__(self, input):
		bestSpeaker = None
		bestCosDist = 100
		for speaker in self.user_management.speaker_table.all():
			nx = np.array(speaker.get('voice'))
			ny = np.array(input)
			cosDist = 1 - np.dot(nx, ny) / np.linalg.norm(nx) / np.linalg.norm(ny)
			if (cosDist < bestCosDist):
				if (cosDist < 0.3):
					bestCosDist = cosDist
					bestSpeaker = speaker.get('name')
		return bestSpeaker		
			
	def run(self):
		logger.info("VoiceAssistant Instanz wurde gestartet.")

if __name__ == '__main__':
	multiprocessing.set_start_method('spawn')

	va = VoiceAssistant()
	logger.info("Anwendung wurde gestartet")
	va.run()
		
	try:
		while True:
		
			pcm = va.audio_stream.read(va.porcupine.frame_length)
			pcm_unpacked = struct.unpack_from("h" * va.porcupine.frame_length, pcm)		
			keyword_index = va.porcupine.process(pcm_unpacked)
			if keyword_index >= 0:
				logger.info("Wake Word %s wurde verstanden.", va.wake_words[keyword_index])
				va.is_listening = True
				
			# Spracherkennung
			if va.is_listening:
				if va.rec.AcceptWaveform(pcm):
					recResult = json.loads(va.rec.Result())
					
					speaker = va.__detectSpeaker__(recResult['spk'])
					if (speaker == None) and (va.allow_only_known_speakers == True):
						print("Ich kenne deine Stimme nicht und darf damit keine Befehle von dir entgegen nehmen.")
						va.current_speaker = None
					else:
						if speaker:
							logger.debug("Sprecher ist %s", speaker)
						va.current_speaker = speaker
						va.current_speaker_fingerprint = recResult['spk']
						logger.debug('Ich habe verstanden "%s"', recResult['text'])
						
						# Lasse den Assistenten auf die Spracheingabe reagieren
						
						#va.tts.say(output)
						
						va.is_listening = False
						va.current_speaker = None
				
	except KeyboardInterrupt:
		logger.debug("Per Keyboard beendet")
	finally:
		logger.debug('Beginne Aufräumarbeiten...')
		if va.porcupine:
			va.porcupine.delete()
			
		if va.audio_stream is not None:
			va.audio_stream.close()
			
		if va.pa is not None:
			va.pa.terminate()			