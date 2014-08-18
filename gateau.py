
from random import shuffle
from threading import Thread

import irc
import irc.bot

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

	def __init__(self, pseudo):
		self.pseudo = pseudo
		self.cartes = []
	
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
		for index in range(len(valeurs) - 4):
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
	
	def __repr__(self):
		return '{}({})'.format(self.pseudo, len(self.cartes))



class Partie:
	
	def __init__(self, createur):
		self.createur = createur
		self.commencee = False

		self.pseudos = [createur]
		self.joueurs = [Joueur(createur)]

	def __bool__(self):
		return self.commencee

	def ajouter(self, joueur):
		nouveau = joueur not in self.pseudos
		if nouveau:
			self.pseudos.append(joueur)
			self.joueurs.append(Joueur(joueur))
		return nouveau

	def commencer(self):
		cartes = []
		for i in range(len(Carte.VALEURS)):
			for j in range(len(Carte.COULEURS)):
				cartes.append(Carte(i, j))
		shuffle(cartes)

		while cartes:
			for joueur in self.joueurs:
				if not cartes:
					break
				carte = cartes[0]
				del cartes[0]
				joueur.cartes.append(carte)

		self.joueur = -1
		self.precedent = -1
		self.tas = []
		self.mensonge = False
		self.commencee = True
		self._valeur = None

	def joue(self, joueur):
		try:
			index = self.pseudos.index(joueur)
		except ValueError:
			return None
		else:
			return self.joueurs[index]

	def poser(self, cartes):
		self.mensonge = False
		for index in cartes:
			carte = self.joueurs[self.joueur].cartes[index-1]
			if carte.valeur != self.valeur:
				self.mensonge = True
			self.tas.append(carte)
			del self.joueurs[self.joueur].cartes[index-1]
		return len(cartes)
	
	def joueurId(self, src):
		for index, pseudo in enumerate(self.pseudos):
			if pseudo == src:
				return index
		return -1
	
	def penaliser(self, joueur):
		self.joueurs[joueur].cartes += self.tas
		total = len(self.tas)
		self.tas = []
		self.joueur = -1
		self._valeur = None
		return total

	def suivant(self, joueur = -1):
		self.precedent = self.joueur
		if joueur < 0:
			self.joueur = (self.joueur + 1) % len(self.joueurs)
		else:
			self.joueur = joueur
		return self.joueurs[self.joueur]

	def gagnant(self):
		if self.precedent < 0 or self.joueurs[self.precedent].cartes:
			return False
		if self.precedent > 0:
			del self.joueurs[self.precedent]
			del self.pseudo[self.precedent]
			self.precedent = self.precedent % len(self.pseudo)
		return True

	def _getvaleur(self):
		return self._valeur
	def _setvaleur(self, valeur):
		self._valeur = valeur
	
	valeur = property(_getvaleur, _setvaleur)



class Jeu:

	COMMANDES = ['init', 'join', 'start', 'cards', 'value', 'place', 'lie', 'help']
	
	def __init__(self, pubmsg, privmsg):
		self.pubmsg = pubmsg
		self.privmsg = privmsg

		self.partie = None
	
	def commande(self, src, nom, args):
		if nom in Jeu.COMMANDES:
			getattr(self, nom)(src, args)
	
	def init(self, src, args):
		if self.partie is None:
			self.partie = Partie(src)
			self.pubmsg(speech.initier_partie)
		else:
			self.pubmsg(speech.partie_deja_initiee)
	
	def join(self, src, args):
		if self.partie is not None:
			if not self.partie:
				if self.partie.joue(src) is None:
					if self.partie.ajouter(src):
						self.pubmsg(speech.ajout.format(src))
					else:
						self.pubmsg(speech.ERREUR_ajout.format(src))
				else:
					self.pubmsg(speech.deja_ajoute.format(src))
			else:
				self.privmsg(src, speech.partie_deja_commencee)
		else:
			self.pubmsg(speech.partie_non_initiee)
	
	def start(self, src, args):
		if self.partie is not None:
			if not self.partie:
				if len(self.partie.joueurs) > 2:
					self.partie.commencer()
					self.pubmsg(speech.commencer_partie)
					for joueur in self.partie.joueurs:
						while True:
							valeur = joueur.doublons()
							if not valeur:
								break
							self.pubmsg('On a retire les 4 %s de %s.' % (valeur, joueur.pseudo))
						self.pubmsg(repr(joueur))
						Thread(target=self.cards, args=(joueur.pseudo, [])).start()
					self.pubmsg(speech.suivant.format(repr(self.partie.suivant())))
				else:
					self.pubmsg(speech.manque_joueurs.format(len(self.partie.joueurs), 3))
			else:
				self.privmsg(src, speech.partie_deja_commencee)
		else:
			self.pubmsg(speech.partie_non_initiee)
	
	def terminer():
		self.partie = None
		self.pubmsg(speech.partie_finie)
	
	def cards(self, src, args = []):
		if self.partie is not None:
			if self.partie:
				joueur = self.partie.joue(src)
				if joueur is not None:
					self.privmsg(src, joueur.jeu())
				else:
					self.privmsg(src, speech.ne_joue_pas)
			else:
				self.privmsg(src, speech.partie_non_commencee)
		else:
			self.privmsg(src, speech.partie_non_initiee)
	
	def value(self, src, args):
		if self.partie is not None:
			if self.partie:
				joueur = self.partie.joue(src)
				if joueur is not None:
					if joueur.pseudo == self.partie.pseudos[self.partie.joueur]:
						if len(args):
							if self.partie.precedent == -1:
								if args[0].capitalize() in Carte.VALEURS:
									self.partie.valeur = args[0].capitalize()
									self.privmsg(src, speech.valeur_valide.format(args[0].capitalize()))
								else:
									self.privmsg(src, speech.valeur_invalide)
							else:
								self.privmsg(src, speech.valeur_deja_definie)
						else:
							self.privmsg(src, speech.args_manquants)
					else:
						self.privmsg(src, speech.non_courrant)
				else:
					self.privmsg(src, speech.ne_joue_pas)
			else:
				self.privmsg(src, speech.partie_non_commencee)
		else:
			self.privmsg(src, speech.partie_non_initiee)
	
	def place(self, src, args):
		if self.partie is not None:
			if self.partie:
				joueur = self.partie.joue(src)
				if joueur is not None:
					if joueur.pseudo == self.partie.pseudos[self.partie.joueur]:
						if self.partie.valeur is not None:
							if len(args):
								if util.contient_nombres(args):
									args = [int(val) for val in args]
									if util.dans_intervalle(args, 1, len(joueur.cartes)):
										if not util.doublon(args):
											if self.partie.gagnant():
												self.pubmsg(speech.gagnant.format(self.partie.joueurs[self.partie.precedent]))
											if len(self.partie.joueurs) > 1:
												args.sort(reverse=True)
												if self.partie.precedent == -1:
													self.pubmsg(speech.nouveau_tour.format(self.partie.valeur))
												self.pubmsg(speech.poser_cartes.format(src, self.partie.poser(args), self.partie.valeur))
												self.pubmsg(speech.suivant.format(repr(self.partie.suivant())))
												self.cards(self.partie.pseudos[self.partie.joueur])
											else:
												self.terminer()
										else:
											self.privmsg(src, speech.carte_double)
									else:
										self.privmsg(src, speech.carte_invalide)
								else:
									self.privmsg(src, speech.args_invalide)
							else:
								self.privmsg(src, speech.args_manquants)
						else:
							self.privmsg(src, speech.valeur_non_definie)
					else:
						self.privmsg(src, speech.non_courrant)
				else:
					self.privmsg(src, speech.ne_joue_pas)
			else:
				self.privmsg(src, speech.partie_non_commencee)
		else:
			self.privmsg(src, speech.partie_non_initiee)
		
	def lie(self, src, args):
		if self.partie is not None:
			if self.partie:
				joueur = self.partie.joue(src)
				if joueur is not None:
					if self.partie.precedent != -1:
						if self.partie.mensonge:
							self.pubmsg(speech.correct.format(src, self.partie.pseudos[self.partie.precedent]))
							if len(self.partie.joueurs[self.partie.precedent].cartes) > 10:
								self.privmsg(self.partie.pseudos[self.partie.precedent],
											 speech.recolte_cartes_soft.format(self.partie.penaliser(self.partie.precedent)))
							else:
								self.privmsg(self.partie.pseudos[self.partie.precedent],
											 speech.recolte_cartes_dur.format(self.partie.penaliser(self.partie.precedent)))
							joueur = self.partie.joueurs[self.partie.precedent]
							while True:
								valeur = joueur.doublons()
								if not valeur:
									break
								self.pubmsg('On a retire les 4 %s de %s.' % (valeur, joueur.pseudo))
							if len(self.partie.joueurs) > 1:
								self.pubmsg(speech.suivant.format(repr(self.partie.suivant(self.partie.joueurId(src)))))
								self.cards(self.partie.pseudos[self.partie.joueur])
							else:
								self.terminer()
								return
						else:
							self.pubmsg(speech.incorrect.format(self.partie.pseudos[self.partie.precedent], src))
							if self.partie.gagnant():
								self.pubmsg(speech.gagnant.format(self.partie.joueurs[self.partie.precedent]))
							if len(self.partie.joue(src).cartes) > 10:
								self.privmsg(src,
											 speech.recolte_cartes_soft.format(self.partie.penaliser(self.partie.joueurId(src))))
							else:
								self.privmsg(src,
											 speech.recolte_cartes_dur.format(self.partie.penaliser(self.partie.joueurId(src))))
							joueur = self.partie.joue(src)
							while True:
								valeur = joueur.doublons()
								if not valeur:
									break
								self.pubmsg('On a retire les 4 %s de %s.' % (valeur, joueur.pseudo))
							if len(self.partie.joueurs) > 1:
								self.pubmsg(speech.suivant.format(repr(self.partie.suivant(self.partie.precedent))))
								self.cards(self.partie.pseudos[self.partie.joueur])
							else:
								self.terminer()
								return
					else:
						self.privmsg(src, speech.tas_vide)
				else:
					self.privmsg(src, speech.ne_joue_pas)
			else:
				self.privmsg(src, speech.partie_non_commencee)
		else:
			self.privmsg(src, speech.partie_non_initiee)
	
	def help(self, src, args):
		self.pubmsg("The cake is a lie. https://www.youtube.com/watch?v=Y6ljFaKRTrI")



class Gateau(irc.bot.SingleServerIRCBot):

	def __init__(self, adresse, pseudo, canal):
		self.adresse = adresse
		self.pseudo = pseudo
		self.canal = canal

		super().__init__([adresse], pseudo, pseudo)

		self.jeu = Jeu(self.pubmsg, self.privmsg)

	def on_welcome(self, serv, ev):
		self.connection.join(self.canal)
		self.privmsg('mango', 'identify 123456')
	
	def on_message(self, serv, ev):
		self.message(ev.source.nick, ev.arguments[0])

	on_pubmsg  = on_message
	on_privmsg = on_message

	def get_version(self):
		return speech.version


	def message(self, src, msg):
		msg = util.ascii(msg.strip().lower())
		if msg and msg[0] == '!':
			args = msg[1:].split()
			if args:
				target = self.jeu.commande
				args = (src, args[0], args[1:])
				Thread(target=target, args=args).start()

	def pubmsg(self, msg):
		self.privmsg(self.canal, msg)
	
	def privmsg(self, dst, msg):
		msg = msg.split('\n')
		for ligne in msg:
			self.connection.privmsg(dst, ligne)


irc.client.ServerConnection.buffer_class = irc.buffer.LenientDecodingLineBuffer

if __name__ == '__main__':
	bot = Gateau(('irc.smoothirc.net', 6667), 'BotLie', '#YouLie')
	bot.start()


