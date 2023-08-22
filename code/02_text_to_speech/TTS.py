from loguru import logger
import time, pyttsx3
import multiprocessing

def __speak__(text, voiceId):
	engine = pyttsx3.init()
	engine.setProperty('voice', voiceId)
	engine.setProperty('rate', 175)
	engine.setProperty('pitch', 0.8)
	engine.say(text)
	engine.runAndWait()
		
class Voice:

	def __init__(self):
		self.process = None
		self.voiceId = "com.apple.voice.compact.de-DE.Anna"
		
	def say(self, text):
		if self.process:
			self.stop()
		p = multiprocessing.Process(target=__speak__, args=(text, self.voiceId))
		p.start()
		self.process = p
		
	def set_voice(self, voiceId):
		self.voiceId = voiceId
		
	def stop(self):
		if self.process:
			self.process.terminate()
		
	def get_voice_keys_by_language(self, language=''):
		result = []
		engine = pyttsx3.init()
		voices = engine.getProperty('voices')
		for voice in voices:
			# Schreibe Sprache und Name klein
			if language == '':
				result.append(voice.id)
			elif language.lower() in voice.name.lower():
				result.append(voice.id)
		return result