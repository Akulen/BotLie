
import irc

import util
import speech


class Carte:

	VALEURS = ['As', 'Deux', 'Trois', 'Quatre', 'Cinq', 'Six', 'Sept',
		   'Huit', 'Neuf', 'Dix', 'Valet', 'Dame', 'Roi']
	COULEURS = ['Carreau', 'Coeur', 'Pique', 'Trèfle']


	def __init__(self, valeur, couleur):
		self._valeur = valeur
		self._couleur = couleur
	
	def __lt__(self, other):
		if self._valeur == other._valeur:
			return self._couleur < other._couleur
		return self._valeur < other._valeur
	
	def __repr__(self):
		return '%s de %s' % (self.valeur, self.couleur)
	
	@property
	def valeur(self):
		return Carte.VALEURS[self._valeur]
	
	@property
	def couleur(self):
		return Carte.COULEURS[self._couleur]


class Joueur:

	def __init__(self, pseudo, cartes=[]):
		self.pseudo = pseudo
		self.cartes = cartes
	
	def doublons(self):
		'''
		Regarde s'il existe des doublons (en vrai, 4 cartes de valeurs
		identiques) dans le jeu du joueur, et les supprime.

		Renvoie le nom de la valeur en doublon, ou None sinon.

		Doit être appelée plusieurs fois pour éliminer l'ensemble des
		doublons.
		'''
		self.cartes.sort()
		valeurs = [carte.valeur for carte in self.cartes]
		for index in range(len(valeurs) - 3):
			if util.uniforme(valeurs[index:index + 3]):
				del self.cartes[index:index + 3]
				return valeurs[index]
		return None

	def jeu(self):
		'''
		Renvoie le jeu actuel du joueur sous forme de chaîne de
		caractères.
		'''
		self.cartes.sort()
		if not self.cartes:
			return speech.plus_cartes
		
		cartes = []
		for index, carte in enumerate(self.cartes):
			cartes.append('  %2d.  %s' % (index + 1, repr(carte)))
		cartes = '\n'.join(cartes)
		message = speech.cartes_restantes.format(len(self.cartes))
		return message + '\n' + cartes


class Gateau(irc.bot.SingleServerIRC):

	def __init__(self, adresse, pseudo, canal):
		self.adresse = adresse
		self.pseudo = pseudo
		self.canal = canal

		super().__init([adresse], pseudo, pseudo)

		self.jeu = Jeu(self.pubmsg, self.privmsg)

	def on_welcome(self, serv, ev):
		self.connection.join(self.canal)
	
	def on_message(self, serv, ev):
		self.message(self, ev.source.nick, ev.arguments[0])

	on_pubmsg  = on_message
	on_privmsg = on_message

	def get_version(self):
		return speech.version


	def message(self, src, msg):
		msg = util.ascii(msg.strip().lower())
		if msg and msg[0] == '!':
			args = msg[1:].split()
			if args:
				self.jeu.commande(args[0], args[1:])

	def pubmsg(self, msg):
		self.privmsg(self.canal, msg)
	
	def privmsg(self, dst, msg):
		msg = msg.split('\n')
		for ligne in msg:
			self.connection.privmsg(dst, ligne)

