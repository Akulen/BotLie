import random
import time

from irc.bot import SingleServerIRCBot as IRCBot
import irc
import util

irc.client.ServerConnection.buffer_class = irc.buffer.LenientDecodingLineBuffer



def is_number(s):
	try:
		val = int(s)
		return val
	except ValueError:
		return -1


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



class BotLie(IRCBot):
	def ginit(self, serv, chan, user, msg):
		if self.partie:
			serv.privmsg(chan, "Il y a deja une partie en cours.")
		else:
			serv.privmsg(chan, "Vous avez initie une partie de 'Tu Mens !'.")
			serv.privmsg(chan, "Veillez rejoindre la partie en utilisant '!join'.")
			serv.privmsg(chan, "Une fois que vous etes prets a commencer, tapez '!start'.")
			self.joueurs = []
			self.initie = True
			self.partie = False
	
	def gjoin(self, serv, chan, user, msg):
		if self.initie:
			if self.partie:
				serv.privmsg(chan, "Il y a deja une partie en cours.")
			else:
				for joueur in self.joueurs:
					if joueur.nom == user:
						serv.privmsg(chan, "Vous jouez deja.")
						return
				serv.privmsg(chan, user+" joue.")
				self.joueurs.append(Joueur(user))
		else:
			serv.privmsg(chan, "Vous n'avez pas initialise la partie avec '!init'.")
	
	def gshowCartes(self, serv, joueur):
		serv.privmsg(joueur.nom, "Voici vos cartes :")
		print(joueur.nom+": affichage...")
		for iCarte, carte in enumerate(joueur.cartes):
			serv.privmsg(joueur.nom, str(iCarte)+". "+carte.__repr__())
			print(str(iCarte)+". "+carte.__repr__())
			time.sleep(0.4)
		print("fini")
	
	def gstart(self, serv, chan, user, msg):
		if self.initie:
			if self.partie:
				serv.privmsg(chan, "Il y a deja une partie en cours.")
			else:
				if len(self.joueurs) < 2:
					serv.privmsg(chan, "Il n'y a pas assez de joueurs. (>= 2)")
				else:
					self.partie = True
					serv.privmsg(chan, "Vous avez lance la partie, voici les joueurs :")
					for joueur in self.joueurs:
						serv.privmsg(chan, joueur.nom)
					self.cartes = []
					for i in range(len(Carte.VALEURS)):
						for j in range(len(Carte.COULEURS)):
							self.cartes.append(Carte(i, j))
					random.shuffle(self.cartes)

					while len(self.cartes):
						for joueur in self.joueurs:
							if len(self.cartes) == 0:
								break
							joueur.cartes.append(self.cartes[0])
							del self.cartes[0]
					
					serv.privmsg(chan, "Distribution ...")
					
					for joueur in self.joueurs:
						while True:
							valeur = joueur.doublons()
							if not valeur:
								break
							serv.privmsg(chan, 'On a retire quatre ' + valeur + ' a ' + joueur.pseudo)
						self.gshowCartes(serv, joueur)
					
					self.curCarte = None
					self.tempCarte = None
					self.curJoueur = 0
					self.tas = []
					self.play(serv, chan)
							
		else:
			serv.privmsg(chan, "Vous n'avez pas initialise la partie avec '!init'.")
	
	def glie(self, serv, chan, user, msg):
		if self.partie:
			if len(self.tas):
				curJoueur = None
				for id, joueur in enumerate(self.joueurs):
					if joueur.nom == user:
						curJoueur = joueur
						iJoueur = id
						break
				if curJoueur is None:
					serv.privmsg(chan, "Vous ne jouez pas.")
					return
				if self.curLie:
					serv.privmsg(chan, "Correct.")
					self.joueurs[(self.curJoueur-1+len(self.joueurs))%len(self.joueurs)].cartes += self.tas
					serv.privmsg(self.joueurs[(self.curJoueur-1+len(self.joueurs))%len(self.joueurs)].nom, "Voici vos nouvelles cartes :")
					for carte in self.tas:
						serv.privmsg(self.joueurs[(self.curJoueur-1+len(self.joueurs))%len(self.joueurs)].nom, carte.__repr__())
						time.sleep(0.4)
					self.joueurs[(self.curJoueur-1+len(self.joueurs))%len(self.joueurs)].check(serv,chan)
					self.curJoueur = iJoueur
				else:
					serv.privmsg(chan, "Faux.")
					self.joueurs[iJoueur].cartes += self.tas
					serv.privmsg(self.joueurs[iJoueur].nom, "Voici vos nouvelles cartes :")
					for carte in self.tas:
						serv.privmsg(self.joueurs[iJoueur].nom, carte.__repr__())
						time.sleep(0.4)
					self.joueurs[iJoueur].check(serv,chan)
					self.curJoueur = (self.curJoueur-1+len(self.joueurs))%len(self.joueurs)
				
				iJoueur = 0
				while iJoueur < len(self.joueurs):
					print(self.joueurs[iJoueur].nom)
					if len(self.joueurs[iJoueur].cartes) == 0:
						serv.privmsg(chan, self.joueurs[iJoueur].nom+" a gagne.")
						del self.joueurs[iJoueur]
					else:
						iJoueur = iJoueur+1
				
				if len(self.joueurs) < 3:
					serv.privmsg(chan, "Partie terminee.")
					self.partie = False
				else:
					self.curCarte = None
					self.tempCarte = None
					self.curLie = False
					self.tas = []
					self.play(serv, chan)
					print("RESET")
					print("-----")
			else:
				serv.privmsg(chan, "Il n'y a pas encore de cartes.")
		else:
			serv.privmsg(chan, "Il n'y a pas de partie en cours.")
	
	def play(self, serv, chan):
		serv.privmsg(chan, "C'est a "+self.joueurs[self.curJoueur].nom+"("+str(len(self.joueurs[self.curJoueur].cartes))+") de jouer.")
	
	def gtype(self, serv, user, msg):
		if self.partie:
			if user != self.joueurs[self.curJoueur].nom:
				serv.privmsg(user, "Ce n'est pas votre tour.")
				return
			if self.curCarte is not None:
				serv.privmsg(user, "Le type est deja defini.")
				return
			if len(msg) < 2:
				serv.privmsg(user, "Il n'y a pas assez d'arguments ('!type <valeur>').")
				return
			if len(msg) > 2:
				serv.privmsg(user, "Il y a trop d'arguments ('!type <valeur>').")
				return
			tempVal = [item.lower() for item in self.valeurs]
			if msg[1] not in tempVal:
				serv.privmsg(user, "Cette valeur n'existe pas.")
				print(msg[1])
				return
			self.tempCarte = Carte(Carte.VALEURS.index(msg[1].capitalize()), 0)
			serv.privmsg(user, "Vous placez des "+self.tempCarte.valeur+".")
		else:
			serv.privmsg(user, "Il n'y a pas de partie en cours.")
	
	def gplace(self, serv, user, msg):
		if self.partie:
			if user != self.joueurs[self.curJoueur].nom:
				serv.privmsg(user, "Ce n'est pas votre tour.")
				return
			if self.curCarte is None and self.tempCarte is None:
				serv.privmsg(user, "Vous devez d'abord specifier la carte avec '!type <valeur>'.")
				return
			if len(msg) < 2:
				serv.privmsg(user, "Il n'y a pas assez d'arguments ('!place <iCarte1> <iCarte2> ...').")
				return
			if len(msg) > len(self.joueurs[self.curJoueur].cartes)+1:
				serv.privmsg(user, "Vous n'avez pas autant de cartes.")
				return
			args = []
			for id, iCarte in enumerate(msg):
				if id != 0:
					args.append(is_number(iCarte))
			for iCarte in args:
				if iCarte < 0:
					serv.privmsg(user, "Vous devez donner un nombre.")
					return
				if iCarte >= len(self.joueurs[self.curJoueur].cartes):
					serv.privmsg(user, "Vous n'avez que "+str(len(self.joueurs[self.curJoueur].cartes))+" carte(s).")
					return
			curCartes = []
			for iCarte in args:
				curCartes.append((iCarte, self.joueurs[self.curJoueur].cartes[iCarte]))
			curCartes.sort(reverse=True, key=lambda tup: tup[0]);
			for id, carte in enumerate(curCartes):
				if id != 0:
					print(str(carte[0]) + " " + str(id))
					if carte[0] == curCartes[id-1][0]:
						serv.privmsg(user, "Vous ne pouvez pas placer deux foix la meme carte.")
						return
			if self.tempCarte is not None:
				self.curCarte = self.tempCarte
				self.tempCarte = None
				print("***"+self.curCarte.valeur+"***")
			self.curLie = False
			while len(curCartes):
				if curCartes[0][1].valeur != self.curCarte.valeur:
					self.curLie = True
				self.tas.append(curCartes[0][1])
				print(curCartes[0][1])
				del self.joueurs[self.curJoueur].cartes[curCartes[0][0]]
				del curCartes[0]
			serv.privmsg(self.chan, user+" a place "+str(len(args))+" "+self.curCarte.valeur+".")
			self.curJoueur = (self.curJoueur+1)%len(self.joueurs)
			self.play(serv, self.chan)
			self.gshowCartes(serv, self.joueurs[self.curJoueur])
		else:
			serv.privmsg(user, "Il n'y a pas de partie en cours.")
	
	def gcartes(self, serv, user, msg):
		if self.partie:
			curJoueur = None
			for id, joueur in enumerate(self.joueurs):
				if joueur.nom == user:
					curJoueur = joueur
					iJoueur = id
					break
			if curJoueur is None:
				serv.privmsg(chan, "Vous ne jouez pas.")
				return
			self.gshowCartes(serv, curJoueur)
		else:
			serv.privmsg(chan, "Il n'y a pas de partie en cours.")
	
	def __init__(self, chan):
		super().__init__([("irc.smoothirc.net",
		    6667)], "BotLie_", "Tu Mens !")
		self.pubCommands = [("!init", self.ginit),
							("!join", self.gjoin),
							("!lie", self.glie),
							("!start", self.gstart)]
		self.privCommands = [("!type", self.gtype),
							 ("!place", self.gplace),
							 ("!cards", self.gcartes)]
		self.chan = chan
		self.initie = False
		self.partie = False
		self.couleurs = ["Carreau", "Coeur", "Pique", "Trefle"]
		self.valeurs = ["As","Deux","Trois","Quatre","Cinq","Six","Sept","Huit","Neuf","Dix","Valet","Dame","Roi"]
	
	def on_welcome(self, serv, ev):
		serv.privmsg('Mango', 'identify 123456')
		serv.join(self.chan)
	
	def on_pubmsg(self, serv, ev):
		user = ev.source.nick
		chan = ev.target
		msg = ev.arguments[0].lower()
		
		if msg[0] == '!':
			self.pubCommand(serv, chan, user, msg.split(' '))
	
	def pubCommand(self, serv, chan, user, msg):
		for chaine, fonction in self.pubCommands:
			if chaine == msg[0]:
				fonction(serv, chan, user, msg)
	
	def on_privmsg(self, serv, ev):
		user = ev.source.nick
		msg = ev.arguments[0].lower()
		
		if msg[0] == '!':
			self.privCommand(serv, user, msg.split(' '))
	
	def privCommand(self, serv, user, msg):
		for chaine, fonction in self.privCommands:
			if chaine == msg[0]:
				fonction(serv, user, msg)

if __name__ == "__main__":
	bot = BotLie("#YouLie")
	bot.start()
