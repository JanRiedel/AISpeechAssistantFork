from loguru import logger
import yaml
import time
import sys

import pvporcupine
from pvrecorder import PvRecorder
import struct
import os


from TTS import Voice
import multiprocessing

CONFIG_FILE = "config.yml"

class VoiceAssistant():

	def __init__(self):
		logger.info("Initialisiere VoiceAssistant...")
		
		# Lese Konfigurationsdatei
		logger.debug("Lese Konfiguration...")
		
		# Verweise lokal auf den globalen Kontext und hole die Variable CONFIG_FILE
		global CONFIG_FILE
		with open(CONFIG_FILE, "r", encoding='utf8') as ymlfile:
			# Lade die Konfiguration im YAML-Format
			self.cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
		if self.cfg:
			logger.debug("Konfiguration gelesen.")
		else:
			# Konnto keine Konfiguration gefunden werden? Dann beende die Anwendung
			logger.debug("Konfiguration konnte nicht gelesen werden.")
			sys.exit(1)
		language = self.cfg['assistant']['language']
		if not language:
			language = "de"
		logger.info("Verwende Sprache {}", language)
			
		# Initialisiere Wake Word Detection
		logger.debug("Initialisiere Wake Word Erkennung...")
		
		# Lies alle wake words aus der Konfigurationsdatei
		self.wake_words = self.cfg['assistant']['wakewords']

		# Lese pvporcupine Access Key
		authkey = self.cfg['keys']['porcupine']
		logger.debug("Porcupine Access Key lautet {}", authkey)

		# Wird keins gefunden, nimm 'bumblebee'
		if not self.wake_words:
			self.wake_words = ['bumblebee']
		logger.debug("Wake Words sind {}", ','.join(self.wake_words))
		self.porcupine = pvporcupine.create(access_key=authkey, keywords=self.wake_words)
		# Sensitivities (sensitivities=[0.6, 0.35]) erweitert oder schränkt
		# den Spielraum bei der Intepretation der Wake Words ein
		logger.debug("Wake Word Erkennung wurde initialisiert.")

		# Initialisiere Recorder/Audio Stream
		logger.debug("Initialisiere Audioeingabe...")
		self.recorder = PvRecorder(
			frame_length=self.porcupine.frame_length,
			device_index=1)
		# Liste alle Audio Devices auf
		devices = self.recorder.get_available_devices()
		for i in range(len(devices)):
			logger.debug('index: %d, device name: %s' % (i, devices[i]))

		self.recorder.start()
		logger.debug("PVRecorder Version: {}", self.recorder.version)
		logger.debug("Audiostream geöffnet: {}", self.recorder.selected_device)
		
		# Initialisiere TTS
		logger.info("Initialisiere Sprachausgabe...")
		self.tts = Voice()
		voices = self.tts.get_voice_keys_by_language(language)
		if len(voices) > 0:
			logger.info('Stimme {} gesetzt.', voices[0])
			self.tts.set_voice(voices[0])
		else:
			logger.warning("Es wurden keine Stimmen gefunden.")
		self.tts.say("Initialisierung abgeschlossen")
		logger.debug("Sprachausgabe initialisiert")
		
	def run(self):
		# Versuche folgenden Code auszuführen. Sollte eine Ausnahme auftreten, wird der except Block behandelt.
		try:
			while True:
				pcm = self.recorder.read()
				result = self.porcupine.process(pcm)

				if result >= 0:
					logger.info("Wake Word {} wurde verstanden.", self.wake_words[result])
					
		# Der Except Block ist hier in seiner Behandlung eingeschränkt auf den Typ KeyboardInterrupt,
		# also falls der Benutzer die Ausführung des Programms mit STRG+C unterbricht.
		except KeyboardInterrupt:
			logger.debug("Per Keyboard beendet")
		# Egal ob erfolgreicher Durchlauf oder Exception: Finally wird am Ende dieses Blocks ausgeführt.
		# Das erlaubt uns die Fehlerbehandlung und das Aufräumen von Ressourcen.
		finally:
			logger.debug('Beginne Aufräumarbeiten...')
			if self.porcupine:
				self.porcupine.delete()
				
			if self.recorder is not None:
				self.recorder.delete()

if __name__ == '__main__':
	multiprocessing.set_start_method('spawn')

	# VoiceAssistant muss außerhalb des try-except-finally Blocks initialisiert werden,
	# da die Instanz sonst nicht in finally bekannt ist.
	va = VoiceAssistant()
	logger.info("Anwendung wurde gestartet")
	va.run()