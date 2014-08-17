
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

def contient_nombres(tab):
	try:
		tab = [int(val) for val in tab]
		return True
	except ValueError:
		return False

def dans_intervalle(tab, mini, maxi):
	if min(tab) < mini or max(tab) > maxi:
		return False
	return True

def doublon(tab):
	tab.sort()
	for index, val in enumerate(tab[1:]):
		if val == tab[index-1]:
			return True
	return False
