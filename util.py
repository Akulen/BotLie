
def uniforme(liste):
	'''
	Teste si une liste contient un seul type d'élément.
	'''
	return liste[1:] == liste[:-1]

def ascii(msg):
	'''
	Retire les accents minuscule d'une chaîne donnée.
	'''
	accents = {'à' : 'a',
		   'â' : 'a',
		   'é' : 'e',
		   'è' : 'e',
		   'ê' : 'e',
		   'ë' : 'e',
		   'î' : 'i',
		   'ï' : 'i',
		   'ô' : 'o',
		   'ö' : 'o',
		   'ù' : 'u',
		   'û' : 'u',
		   'ü' : 'u' }
	for accent, eq in accents.items():
		msg = msg.replace(accent, eq)
	return msg

