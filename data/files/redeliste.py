#!/usr/bin/env python3

# modules for GUI
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# module for multithreading (only used for stopwatch)
from _thread import start_new_thread

# module to easier handle lists, only use for sorting after erstredner
from operator import itemgetter

# modules for handling time and files/paths
import time
import os


# the stopwatch as a class
class StopWatch():
	def __init__(self,labels): # takes the labels it's going to output
		# to as a list
		# labels (outout) are being defined
		self.lwatch_beam = labels[0]
		self.lwatch_org = labels[1]
		# set basic variables for sw-handling
		self.starttime = 0.0
		self.elapsedtime = 0.0
		# set variable that tells if watch is running
		self.running = False
		self.setTime(self.elapsedtime)
				
	# function that basically prints the watch to the gui
	def setTime(self, elap):
		# get time as nice, readable numbers and put them into nice format
		minutes = int(elap/60)
		seconds = int(elap-minutes*60)
		hseconds = int((elap-minutes*60-seconds)*100)
		zeitangabe = str("%02d:%02d" % (minutes, seconds))
		# do some funny stuff, if speaker gets close to the end of their time
		global redezeit
		if minutes+1 == redezeit and 30 <= seconds <45:
			zeitangabe = "<u>" + zeitangabe + "</u>"
		if minutes+1 == redezeit and seconds >=45 and hseconds > 50:
			zeitangabe = "<u>" + zeitangabe + "</u>"
		if minutes >= redezeit:
			zeitangabe = "<span color='red'><u>" + zeitangabe + "</u></span>"
		# put the watch onto the labels
		self.lwatch_beam.set_markup(zeitangabe)
		self.lwatch_org.set_markup(zeitangabe)
	
	# function that either starts or resets the watch
	def start(self):
		if not self.running:
			self.starttime = time.time()
			self.running = True
			# start the run function in a separate thread, so the rest
			# of the programm can run without caring about the watch
			start_new_thread(self.run, ())
		else:
			self.reset()

	# function that handles the running clock
	def run(self):
		while self.running:
			# actualize the time
			self.elapsedtime = time.time() - self.starttime
			# print time to label
			self.setTime(self.elapsedtime)
			# wait a little bit, so the programm doesn't flush to many resources down the toilet
			time.sleep(.5)
	
	# stops the watch – duh
	def stop(self):
		self.running = False
		self.reset()
	
	# resets all the variables, sets watch to 00:00 without changing running status
	def reset(self):
		self.starttime = time.time()
		self.elapsedtime = 0.0
		self.setTime(self.elapsedtime)


# handles gui input and connects every button/ gui-entity with its action
class Handler:
	def on_next_clicked(self, button):
		next()
	def on_entry_activate(self, entry, *args):
		new_name(entry.get_text())
		entry.set_text("")
	def on_enter_button_clicked(self, button):
		global entry_bar
		new_name(entry_bar.get_text())
		entry_bar.set_text("")
	def on_del_all_clicked(self, button):
		del_all()
	def on_redezeit_toggled(self, box):
		global sw
		sw.lwatch_beam.set_visible(box.get_active())
	def on_startwatch_clicked(self, button):
		global sw
		sw.start()	
	def on_redezeit_länge_changed(self, rz_combo):
		global redezeit
		redezeit = get_redezeit(rz_combo)
	def on_erstredner_toggled(self, button):
		show_liste()
	def on_geschlecht_toggled(self, button):
		show_liste()
	def on_vielredner_toggled(self, button):
		show_liste()
	def on_undo_clicked(self, button):
		undo()
	def on_redo_clicked(self, button):
		redo()


# get active redezeit length using some dirty hack
def get_redezeit(combo):
	return int(combo.get_active_text().split()[0])
	

# kicks active speaker and makes next person on list speaker
def next():
	global liste, sw
	if liste:
		del liste[0]
		show_liste()
	sw.reset()

# handles input of a new name
def new_name(name):
	if not name:
		return
	global liste, schon_gesprochen, history
	snapshoot(liste, schon_gesprochen)

	# catch deletions of names
	if name[0] == "-":
		name = name[1:].strip()
		# delete name if it is found
		try:
			liste = [le for le in liste if le[0] != name]
			schon_gesprochen.remove(name)
			show_liste()
			return

		# print error to organizer if not found
		except ValueError:
			t = label_quotierung2.get_text()
			t = "'{}' nicht in Liste\n".format(name) + t
			label_quotierung.set_text(t)
			return

	# catch GO-Anträge, prioritize them whith some Tricks
	elif name[-3:] == " go":
		liste.insert(1, ["<span color='red'>"+shorten(name[:-3]) + " GO</span>", "go", False])
		liste.insert(2, ["<span color='red'>Gegenrede GO</span>", "geg", False])
		 	
	else:
		# give male gender tag if no gender tag is given, so explicit
		# females are preferred
		if name[-2:] != " m" and shorten(name[-2:]) != " f":
			g = "m"
			name = shorten(name)
		else:
			# get gender tag from input
			g = name[-1]
			name = shorten(name[:-2])
		# set person with all its metadata (gender tag, bool, False if erstredner)
		person = [name, g, name in schon_gesprochen]
		liste.append(person)
		# safe name in a list, so it can be tested if erstredner
		schon_gesprochen.append(name)
	show_liste()


# if a name is too long, shorten it
def shorten(name):
	if len(name) > 20:
		return name[:17] + "…"
	else:
		return name

# reset everything, clear every list, stop watch (no pun intended)
def del_all():
	global liste, sw, schon_gesprochen
	snapshoot(liste, schon_gesprochen)
	liste = []
	schon_gesprochen = []
	show_liste()
	sw.stop()


# sort following the quotation
def quoten_sort(liste):
	# get info if quotation is wished
	geschlecht = builder.get_object("geschlecht").get_active()
	erstredner = builder.get_object("erstredner").get_active()
	vielredner = builder.get_object("vielredner").get_active()
	
	if geschlecht:
		# kinda bubble sort to an alternating list accepting the active
		# speaker and using the gender tag
		# -> starts lagging whith over ~600 speakers
		for h in range(len(liste)-2):
			for i in range(len(liste)-2-h):
				# compares allways three persons and sorts them, accepting
				# the first one like this: XXY -> XYX; XYY -> XYY
				if liste[i][1] == liste[i+1][1] and liste[i+2][1] != liste[i+1][1]:
					temp = liste[i+2]
					liste[i+2] = liste[i+1]
					liste[i+1] = temp
		
	# sort prefering erstredners, accepting active speaker like this:
	# ZEEZZEZE -> ZEEEEZZZ
	if erstredner:
		liste[1:] = sorted(liste[1:], key=itemgetter(2))

	# sort for count of utterances
	elif vielredner:
		liste[1:] = sorted(liste[1:], key=lambda x: schon_gesprochen.count(x[0]))

	return liste


# set tag telling gender for show_liste()
def gendertag(person):
	if builder.get_object("geschlecht").get_active():
		if person[1] == "m":
			return " ♂"
		elif person[1] == "f":
			return " ♀"
	return ""


# set tag telling if erstredner for show_liste()
def rednertag(person):
	global schon_gesprochen
	if builder.get_object("erstredner").get_active() or builder.get_object("vielredner").get_active():
		return " [{}]".format(schon_gesprochen.count(person[0]))
	else:
		return ""


# print names on the labels
def show_liste():
	global liste, schon_gesprochen
	# first sort the list of persons according to active quotation
	liste = quoten_sort(liste)
	
	"""organizing the beamer output"""
	liste_text = ""
	# put first name or placeholder into output variable with some nice
	# formatting
	liste_text += ("<u>" + liste[0][0] + "</u>" + gendertag(liste[0]) + rednertag(liste[0])) if liste else "Dein Name"
	# print either the next name or a cuple endlines, so allways the
	# same space is needed
	for i in range(1,5):
		liste_text += "\n"
		try:
			liste_text += liste[i][0] + gendertag(liste[i]) + rednertag(liste[i])
		except IndexError:
			pass
	
	"""organizing the organizer output"""
	org_text = ["",""] # put everything in a list of two strings, to
	# make it easier to print to two labels
	for i in range(len(org_text)):
		for j in range(10):
			if j != 0:
				org_text[i] += "\n"
			try:
				# add how many times this person has already spoken
				org_text[i] += liste[j+10*i][0] + gendertag(liste[j+10*i]) + rednertag(liste[j+10*i])
				if i == 0 and j == 0:
					org_text[i] = "<u>" + org_text[i] + "</u>"
			except IndexError:
				pass
	
	"""set the markers for quotation"""
	quot_text = "♂/♀" if builder.get_object("geschlecht").get_active() else ""
	quot_text += " ①" if builder.get_object("erstredner").get_active() else ""
	quot_text += " <" if builder.get_object("vielredner").get_active() else ""
	
	# print the quotation symbols
	label_quotierung.set_text(quot_text)
	label_quotierung2.set_text(quot_text)
		
	# print the generated namelists to the labels
	label_org.set_markup(org_text[0])
	label_org2.set_markup(org_text[1])
	label_beam.set_markup(liste_text)


# save stuff to be able to undo later
def snapshoot(liste, schon_gesprochen):
	global history, historyIndex
	# look if there is space in list and adjust new list
	if history.count(None) > 0:
		hist_pre = history[:historyIndex]

	else:
		hist_pre = history[1:historyIndex]

	hist_this = [(liste, schon_gesprochen)]
	hist_post = [None for _ in range(len(history) - historyIndex - 1)]
	history = hist_pre + hist_this + hist_post
	historyIndex += 1
	print(len(history))
	builder.get_object("redo").set_sensitive(False)
	builder.get_object("undo").set_sensitive(True)


def undo():
	print("undo")
	global history, historyIndex, liste, schon_gesprochen
	if historyIndex > 1:
		builder.get_object("redo").set_sensitive(True)
		snapshoot(liste, schon_gesprochen)
		historyIndex -= 1
		liste, schon_gesprochen = history[historyIndex -1]
		if historyIndex == 0:
			builder.get_object("undo").set_sensitive(False)
	else:
		builder.get_object("undo").set_sensitive(False)
		pass

def redo():
	print("redo")
	global history, historyIndex, liste, schon_gesprochen
	liste, schon_gesprochen = history[historyIndex]
	historyIndex += 1
	if historyIndex == len(history) - 1 or all(x == None for x in history[historyIndex:]):
		builder.get_object("redo").set_sensitive(False)


# set up GUI
builder = Gtk.Builder()
path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "redeliste_gui.glade")
# get GUI data from file
builder.add_from_file(path)
# connecting buttons etc. with actions using the Handler-class
builder.connect_signals(Handler())

# set up important global variables
liste = []
schon_gesprochen = []
history = [None for i in range(5)]
historyIndex = 0
redezeit = get_redezeit(builder.get_object("redezeit_länge"))

# disable undo/redo buttons
for x in ["undo", "redo"]:
	builder.get_object(x).set_sensitive(False)

# set up main window
main_window = builder.get_object("redeliste_org")
# define that exiting main window ends program
main_window.connect("destroy", Gtk.main_quit)
main_window.show_all()


# set up second/ beamer window
beam_window = builder.get_object("redeliste")
beam_window.show_all()

# set global variables for the labels, so they can be printed on
# everywhere in the program
label_beam = builder.get_object("liste_beam")
label_org = builder.get_object("liste_org")
label_org2 = builder.get_object("liste_org2")
label_quotierung = builder.get_object("quotierung_anzeige")
label_quotierung2 = builder.get_object("quotierung2")
entry_bar = builder.get_object("entry")

# set up stop watch
sw = StopWatch([builder.get_object("watch"), builder.get_object("watch_org")])
show_liste()

# start GUI mainloop
Gtk.main()
