
from threading import Thread


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
	
	def __repr__(self):
		return '{}({})'.format(self.pseudo, len(self.cartes))



class Partie:
	
	def __init__(self, pubmsg, privmsg, createur):
		'''
		Il faut passer le nom du créateur pour qu'il soit
		automatiquement ajouté à la liste des joueurs, et aussi pour
		qu'il puisse (potentiellement) arrêter la partie dans une
		future implémentation
		'''
		self.pubmsg = pubmsg
		self.privmsg = privmsg
		self.createur = createur


		'''
		L'attribut d'instance valeur contient le type de carte en
		cours.
		Il peut être modifié directement.
		'''
		self.valeur = None
	
		'''
		L'attribut d'instance joueur contient l'index du joueur qui
		joue au tour actuel.
		Ne doit pas être modifié.
		'''
		self.joueur = None

		'''
		L'attribut d'instance precedent contient l'index du joueur qui
		a joué au tour d'avant, ou None si aucun joueur n'a encore
		joué.
		Ne doit pas être modifié.
		'''
		self.precedent = None

		'''
		L'attribut d'instance joueurs contient la liste des joueur
		en jeu.
		Ne doit pas être modifié directement.
		'''
		self.joueurs = []

		'''
		L'attribut mensonge est vrai si le joueur du tour précédent a
		menti.
		Ne doit pas être modifié.
		'''
		self.mensonge = False


	def __bool__(self):
		'''
		Permet d'avoir la syntaxe:
			if self.partie:
				print('Une partie est en cours !')
		dans la classe Jeu.
		Le corps du if ne sera exécuté que si une partie est en cours,
		conformément à la définition de cette méthode
		'''
	
	def ajouter(self, joueur):
		'''
		Ajoute un joueur à la partie.
		Qu'il soit déjà dans la partie ou non relève de la classe
		Partie, pas de la classe Jeu, donc il n'y a pas besoin de
		l'implémenter dans la classe Jeu.

		Renvoie True si le joueur a pu être ajouté, false sinon

		'''
	
	def commencer(self):
		'''
		Démarre la partie.
		Les cartes sont générées et distribuées ici.
		'''
	def interrompre(self):
		'''
		Stoppe la partie.
		La partie ne peut être reprise, il faut en créer une autre.
		'''
	
	def poser(self, cartes):
		'''
		Indique que le joueur courant a posé l'ensemble des cartes
		numérotées dans la liste cartes.
		Renvoie une liste contenant le nom des cartes posées
		'''
	
	def penaliser(self, joueur):
		'''
		Donne le tas au joueur à l'index joueur indiqué.
		Renvoie une liste contenant le nom des cartes ajoutées
		'''
	
	def suivant(self):
		'''
		Passe au joueur suivant pour le jeu.
		Renvoie le joueur qui joue au tour actuel.
		'''		



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
			self.partie = Partie(self.pubmsg, self.privmsg, src)
			self.pubmsg(speech.initier_partie)
		else:
			self.pubmsg(speech.partie_deja_initiee)
	
	def join(self, src, args):
		if self.partie is not None:
			if self.partie.joue(src) is None:
				if self.partie.ajouter(src):
					self.pubmsg(speech.ajout.format(src))
				else:
					self.pubmsg(speech.ERREUR_ajout.format(src))
			else:
				self.pubmsg(speech.deja_ajoute.format(src))
		else:
			self.pubmsg(speech.partie_non_initiee)
	
	def start(self, src, args):
		if self.partie is not None:
			if !self.partie:
				if len(self.partie.joueurs) > 2:
					self.partie.commencer():
					self.pubmsg(speech.commencer_partie)
					for joueur in self.partie.joueurs:
						self.pubmsg(repr(joueur))
						self.cards(joueur.pseudo, [])
				else:
					self.pubmsg(speech.manque_joueurs.format(len(self.partie.joueurs), 3))
			else:
				self.privmsg(src, speech.partie_deja_commencee)
		else:
			self.pubmsg(speech.partie_non_initiee)
	
	def terminer():
		self.partie.interrompre()
	
	def cards(self, src, args):
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
								if args[0] in Carte.VALEURS:
									self.partie.valeur = args[0]
									self.privmsg(src, speech.valeur_valide.format(args[0]))
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
						if len(args):
							if contient_nombres(args):
								if util.dans_intervalle(args, 1, len(joueur.cartes)):
									if !util.doublon(args):
										if self.partie.gagnant():
											self.pubmsg(speech.gagnant.format(self.partie.joueurs[self.partie.prec]))
										if len(self.partie.joueurs) > 1:
											self.pubmsg(speech.suivant.format(self.partie.suivant().pseudo))
										else:
											self.terminer()
											return
										self.pubmsg(speech.poser_cartes.format(src, self.partie.poser(args), self.partie.valeur))
										self.pubmsg(speech.suivant.format(self.partie.suivant().pseudo))
									else:
										self.privmsg(src, speech.carte_double)
								else:
									self.privmsg(src, speech.carte_invalide)
							else:
								self.privmsg(src, speech.arg_invalide)
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
		
	def lie(self, src, args):
		if self.partie is not None:
			if self.partie:
				joueur = self.partie.joue(src)
				if joueur is not None:
					if self.partie.precedent != -1:
						if self.partie.mensonge:
							self.pubmsg(speech.correct)
							self.privmsg(self.partie.pseudos[self.partie.precedent],
										 speech.recolte_cartes.format(self.partie.penaliser(self.partie.precedent)))
						else:
							self.pubmsg(speech.incorrect)
							if self.partie.gagnant():
								self.pubmsg(speech.gagnant.format(self.partie.joueurs[self.partie.prec]))
							self.privmsg(self.partie.pseudos[self.partie.joueur],
										 speech.recolte_cartes.format(self.partie.penaliser(self.partie.joueur)))
						if len(self.partie.joueurs) > 1:
							self.pubmsg(speech.suivant.format(self.partie.suivant().pseudo))
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



class Gateau(irc.bot.SingleServerIRC):

	def __init__(self, adresse, pseudo, canal):
		self.adresse = adresse
		self.pseudo = pseudo
		self.canal = canal

		super().__init__([adresse], pseudo, pseudo)

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
				target = self.jeu.commande
				args = (src, args[0], args[1:])
				Thread(target=target, args=args).start()

	def pubmsg(self, msg):
		self.privmsg(self.canal, msg)
	
	def privmsg(self, dst, msg):
		msg = msg.split('\n')
		for ligne in msg:
			self.connection.privmsg(dst, ligne)

