from tinydb import TinyDB, Query
#import json

class UserMgmt:

	def __add_dummies__(self):
		
		# Füge zwei Sprecher hinzu
		Speaker = Query()
		if (not self.speaker_table.contains(Speaker.name == 'jonas')):
			self.speaker_table.insert({'name': 'jonas', 'gender': 'male', 'voice': [6.448483, 3.302678, 3.766785, -2.584503, 4.197047, 1.612695, 4.894525, 1.101822, -0.385377, 1.414407, 6.241484, 2.498986, 5.021112, -2.533914, -1.070522, 2.464833, 5.422098, 3.239231, 4.598713, 6.079732, -0.612436, -3.131733, 3.764071, 2.898125, 2.632231, 0.327163, 4.299379, 6.27173, 6.720829, 3.266853, 4.450684, -0.354963, -6.221786, 5.144508, 0.299108, -6.882116, 7.149723, -3.464576, 3.951359, 4.163059, -3.3212, 0.458154, 0.653759, 2.154661, 2.271815, 0.91119, -3.71623, 2.355904, 4.212521, 4.423264, 2.84015, 4.832661, 3.54575, 4.889555, 1.524147, 3.463018, 6.789889, -3.25227, -0.235607, 4.481417, -2.852158, -2.979775, 3.346377, 1.513499, -1.246751, 2.385767, 7.415844, 0.461825, 4.751189, 4.357193, 6.603981, 2.468827, 7.672635, -0.709006, 2.307403, 4.672907, 1.443786, 5.920113, 4.748209, 3.114192, 4.522695, 2.368259, 3.29633, 1.812458, 3.652013, -6.488424, 3.633734, 0.624184, 6.842927, 12.378441, -1.34367, 2.71211, 0.580662, 4.711989, 3.651287, 2.403205, 2.724817, 3.344514, 4.247672, -0.596305, -0.550065, 5.275489, 4.387664, 4.238325, 4.594451, 4.982614, -1.423761, 1.365213, -4.784701, 2.229842, 1.574221, 0.325415, 1.692554, 0.825549, 5.550143, 3.37925, 5.009644, 3.744156, 3.778469, 5.803823, 3.803166, 6.268604, 2.118448, -1.19695, -1.747697, -6.198786, 4.999674, -2.381053], 'phone':'4915229209413', 'intents':['*']})
	
		if (not self.speaker_table.contains(Speaker.name == 'sarah')):
			self.speaker_table.insert({'name': 'sarah', 'gender': 'female', 'voice': [6.568451, 6.784739, 5.919335, -0.037495, 5.012778, 3.429874, 0.197787, 4.527809, 4.255286, -2.130709, 5.589361, -3.622524, 4.508074, 3.356104, 3.682185, 0.044928, 0.479103, 2.203794, 3.632379, 3.791435, -0.37931, 1.265373, 6.435224, 4.998378, 1.799174, 0.382703, 3.253555, 7.215866, 5.043785, 2.663403, 7.665906, -3.570974, 1.6675, 4.020483, -4.763138, 3.499512, 1.714248, -0.560638, 4.49633, 1.303618, -6.767202, 2.607261, 2.53354, 3.470852, 5.046845, 0.081558, -0.458351, 6.547997, 4.702069, 1.162, 7.732637, 4.443409, 2.84802, 3.515044, 1.404639, -2.716206, 7.028213, -0.252494, 0.31498, 2.893929, -3.77118, 1.205617, 1.795407, 4.893912, 0.521469, -4.615733, 2.547347, -1.403257, 2.687941, 3.193995, 5.99359, 1.825902, 1.973971, 2.642833, 4.234736, 1.145308, -0.519826, 7.352092, 1.77186, 1.947172, 6.951781, 2.769729, 4.519409, 8.090642, 3.032326, 2.692257, 0.98964, -4.389252, 5.47305, 3.880094, -3.5125, 1.346476, 1.295684, 8.435177, 4.487869, 1.237189, 3.073678, -5.445618, 5.607491, 6.903141, 0.258461, 4.483095, 6.992905, 3.336628, 5.016744, 3.078014, 2.637331, 2.047266, 2.220054, 3.3177, 4.209452, -3.704949, 5.010245, -4.430152, -1.731702, 3.403976, 6.573786, 1.421829, 5.792188, 1.567448, 0.59064, 4.689801, 3.367578, 2.579401, -6.780087, -1.828632, 4.636183, 0.699218], 'phone':'4915208768386', 'intents':['animalsounds', 'gettime']})
			
	def authenticate_intent(self, speaker, intent):
		Speaker = Query()
		# Hole den Eintrag für den Sprecher
		result = self.speaker_table.get(Speaker.name == speaker)
		if not result is None:
			# Hole die Intents, die der Sprechner nutzen darf
			intents = result['intents']
			if intents:
				# Ist ein Eintrag in der Intent-Liste mit dem Wert "*" oder der exakte Name des Intents?
				return (((len(intents) == 1) and (intents[0] == '*')) or (intent in intents))
		return False

	def __init__(self, init_dummies=False):
		# initialize a db to store speaker data
		self.db = TinyDB('./users.json')
		self.speaker_table = self.db.table('speakers')
		if init_dummies:
			self.__add_dummies__()