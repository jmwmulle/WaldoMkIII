__author__ = "Jonathan Mulle"

from os.path import join, isfile
import traceback, sys
from klibs.KLExceptions import *
from klibs import P

from klibs import Experiment
from klibs.KLConstants import CIRCLE_BOUNDARY, TK_S, BL_CENTER
from klibs.KLUtilities import deg_to_px, px_to_deg
from klibs.KLUserInterface import ui_request
from klibs.KLGraphics import blit, fill, flip
from klibs.KLGraphics.KLDraw import Annulus, drift_correct_target
from klibs.KLGraphics.KLNumpySurface import NumpySurface as NpS
from klibs.KLCommunication import message
from klibs.KLEventInterface import TrialEventTicket as TET

from random import randrange
from klibs.KLBoundary import BoundaryInspector
from DiscLocation import DiscLocation

LOC = "location"
AMP = "amplitude"
ANG = "angle"
NEW = "new"
OLD = "old"
RED = [236, 88, 64, 255]
BLUE = [15, 75, 255, 255]
WHITE = [255,255,255,255]
GREY = [125,125,125,255]
BLACK = [0,0,0,255]
GREEN = [0,255,0,255]
BG_ABSENT = "absent"
BG_PRESENT = "present"
BG_INTERMITTENT = "intermittent"

INITIAL_FIXATION = "initial fixation"

# TODO: MARK UP THE EDF YOU TIT

class WaldoMkIII(Experiment, BoundaryInspector):
	max_amplitude_deg = 6  # degrees of visual angle
	min_amplitude_deg = 3  # degrees of visual angle
	max_amplitude = None  # px
	min_amplitude = None  # px
	min_saccades = 5
	max_saccades = 12
	disc_diameter_deg = 1
	disc_diameter = None
	search_disc_proto = None
	penultimate_disc_color = BLUE
	search_disc_color = RED
	display_margin = None  # ie. the area in which targets may not be presented
	allow_intermittent_bg = True
	fixation_boundary_tolerance = 1.5  # scales boundary (not image) if drift_correct target too small to fixate
	disc_boundary_tolerance = 1.25  # scales boundary (not image) if drift_correct target too small to fixate
	looked_away_msg = None
	eyes_moved_message = None

	# trial vars
	log_f = None
	disc_locations = []
	trial_type = None
	backgrounds = {}
	bg = None
	bg_state = None
	saccade_count = None
	frame_size = "1024x768"
	n_back = None  # populated from config
	angle = None   # populated from config
	n_back_index = None
	inter_disc_event_label = None  # set after each disc has been saccaded to
	show_dc_target = True
	departed_dc = False

	def __init__(self, *args, **kwargs):
		super(WaldoMkIII, self).__init__(*args, **kwargs)

	def setup(self):
		self.log_f = open(join(P.local_dir, "logs", "P{0}_log_f.txt".format(P.participant_id)), "w+")
		header = {"target_presentation_behavior":P.target_presentation_behavior,
				  "target_removal_behavior": P.target_removal_behavior,
				  "fixation_interval": P.fixation_interval,
				  "disc_timeout_interval" : P.disc_timeout_interval,
				  "drift_correct_initial_persist": P.drift_correct_initial_persist,
				  "final_disc_timeout_interval": P.final_disc_timeout_interval
		}
		if P.development_mode:
			for k in header:
				self.log_f.write("{0}: {1}\n".format(k, header[k]))

		self.max_amplitude = deg_to_px(self.max_amplitude_deg)
		self.min_amplitude = deg_to_px(self.min_amplitude_deg)
		self.disc_diameter = deg_to_px(self.disc_diameter_deg)
		self.display_margin = int(self.disc_diameter * 1.5)
		self.search_disc_proto = Annulus(self.disc_diameter, int(self.disc_diameter * 0.25), (2,WHITE), BLACK)
		# if P.inter_disc_interval and P.persist_to_exit_saccade:
		# 	raise RuntimeError("P.inter_disc_interval and P.persist_to_exit_saccade cannot both be set.")
		r = drift_correct_target().width * self.fixation_boundary_tolerance
		self.el.add_gaze_boundary(INITIAL_FIXATION, [P.screen_c, r], CIRCLE_BOUNDARY)
		fill(P.default_fill_color)
		self.txtm.add_style("msg", 32, WHITE)
		self.txtm.add_style("err", 64, WHITE)
		self.txtm.add_style("disc test", 48, (245,165,5))
		self.txtm.add_style("tny", 12)
		self.looked_away_msg = message("Looked away too soon.", "err", blit_txt=False)
		message("Loading, please hold...", "msg", flip_screen=True)
		if not P.testing:
			scale_images = False
			for i in range(1, 10):
				ui_request()
				image_key = "wally_0{0}".format(i)
				#  there are 3 sizes of image included by default; if none match the screen res, choose 1080p then scale
				image_f = join(P.image_dir, image_key,"{0}x{1}.jpg".format(*P.screen_x_y))
				with open(join(P.image_dir, image_key, "average_color.txt")) as color_f:
					avg_color = eval(color_f.read())
				if not isfile(image_f):
					image_f = join(P.image_dir, image_key, "1920x1080.jpg")
					scale_images = True
				img_ns = NpS(image_f)

				self.backgrounds[image_key] = ([image_key, img_ns, avg_color])
				if scale_images:
					self.backgrounds[image_key][1].scale(P.screen_x_y)
				self.backgrounds[image_key][1] = self.backgrounds[image_key][1].render()

	def block(self):
		pass

	def setup_response_collector(self):
		pass

	def trial_prep(self):
		self.show_dc_target = True
		self.departed_dc = False
		print "angle before type change is: {0}".format(self.angle)
		self.angle = int(self.angle)
		print "angle after type change is: {0}".format(self.angle)
		self.n_back = int(self.n_back)
		self.saccade_count = randrange(self.min_saccades, self.max_saccades)
		fill()
		m = message("Generating targets...", blit_txt=False)
		blit(m)
		flip()
		errors = 0
		print "Generating targets, final angle should be: {0}".format(self.angle)
		while len(self.disc_locations) != self.saccade_count:
			fill()
			blit(m, location=(25,25))
			try:
				self.generate_locations()
			except (TrialException, ValueError):
				errors += 1
				message("Failed attempts: {0}".format(errors), location=(25,50))
				self.disc_locations = []
			flip()

		self.bg = self.backgrounds[self.bg_image]
		self.evm.register_ticket(TET("initial fixation end", P.fixation_interval))
		self.el.drift_correct(boundary=INITIAL_FIXATION)
		self.display_refresh()

	def trial(self):
		if P.development_mode:
			self.log_f.write("{0} TRIAL {1} START {0}".format("*" * 52, P.trial_number, "*" * 52))
			data = [self.show_dc_target, self.departed_dc]
			self.log_f.write("\n*\tshow_dc_target: {0}, departed_dc: {1}".format(*data))
			self.log_f.write("\n{0}".format("*" * 120))

		self.initial_fixation()

		for dl in self.disc_locations:
			self.display_refresh(dl)
			while self.evm.before(dl.event_timeout_label, True):
				if P.development_mode:
					self.exp.log_f.write("\n\t**D{0} times out in {1}".format(dl.index, self.evm.until(dl.event_timeout_label)))

				if dl.boundary_check(not dl.first_disc): # Only final disc will return True
					break
				self.display_refresh(dl)
				ui_request()

			if dl.timed_out:  # ie. should be False by now
				if P.development_mode:
					self.log_f.write("\n\t*** D{0} TIMED OUT ***".format(dl.index))
					self.log_f.write("\n{0} {1} {0}\n".format("*" * 55, "TRIAL END", "*" * 54))
				if not dl.final_disc:
					raise TrialException("Timeout detected.")
				else:
					dl.rt = -1.0
					dl.fixation_timestamp = [-1.0, -1.0]

		if P.development_mode:
			self.log_f.write("\n{0} {1} {0}\n".format("*" * 55, "TRIAL END", "*" * 54))

		return {"trial_num": P.trial_number,
				"block_num": P.block_number,
				"bg_image": self.bg[0],
				"timed_out": self.disc_locations[-1].timed_out,
				"rt": self.disc_locations[-1].rt,
				"target_type": "NBACK" if self.disc_locations[-1].n_back else "NOVEL",
				"bg_state": self.bg_state,
				"n_back": self.n_back,
				"amplitude": px_to_deg(self.disc_locations[-1].amplitude),
				"angle": self.angle,
				"saccades": self.saccade_count}

	def trial_clean_up(self):
		if P.development_mode:
			self.log_f.write("\n\ntrial_clean_up() for trial".format(P.trial_id))
		if P.trial_id:  # ie. if this isn't a recycled trial
			for l in self.disc_locations:
				self.database.insert( {
				'participant_id': P.participant_id,
				'trial_id': P.trial_id,
				'trial_num': P.trial_number,
				'block_num': P.block_number,
				'location_num': l.index,
				'x': l.x_y_pos[0],
				'y': l.x_y_pos[1],
				'amplitude': l.amplitude,
				'angle': l.angle,
				'n_back': l.n_back,
				'penultimate': l.penultimate_disc,
				'final': l.final_disc,
				'timed_out': l.timed_out,
				'rt': -1.0 if l.rt is None else l.rt,
				'fixate_trial_time': l.fixation_timestamp[0],
				'fixate_el_time': l.fixation_timestamp[1],
				},'trial_locations', False)
		self.disc_locations = []
		self.el.clear_boundaries([INITIAL_FIXATION])
		self.bg = None
		self.angle = None

	def clean_up(self):
		pass

	def initial_fixation(self):
		self.display_refresh()
		while self.evm.before("initial fixation end", True):
			if not self.el.within_boundary(INITIAL_FIXATION):
				self.evm.register_ticket(TET("failed initial fixation", self.evm.trial_time + 1.0, None, False, TK_S))
				while self.evm.before("failed initial fixation", True):
					fill(RED)
					blit(self.looked_away_msg, BL_CENTER, P.screen_c)
					flip()
				raise TrialException("Gaze out of bounds.")
		self.display_refresh()

	def display_refresh(self, disc_location=None):
		#  handle the removal of background image on absent condition trials
		ui_request()
		if self.bg_state != BG_ABSENT:
			if (disc_location is not None and disc_location.final_disc) and self.bg_state == BG_INTERMITTENT:
				fill(self.bg[2])
			else:
				blit(self.bg[1])
		else:
			fill(GREY)

		#  show the drift correct target if need be
		if self.show_dc_target:
			blit(drift_correct_target(), position=P.screen_c, registration=5)

		#  blit passed discs if they're allow_blit attribute is set
		if P.development_mode:
			if disc_location:
				disc_args = [disc_location.index, self.evm.trial_time_ms, "F" if disc_location.final_disc else "x", \
							 "P" if disc_location.penultimate_disc else "x", "N" if disc_location.n_back else "x"]
				self.log_f.write("\n\n*** Current Disc: {0} ({2}{3}{4}) at {1} ***".format(*disc_args))
				for d in [disc_location, disc_location.previous_disc, disc_location.next_disc]:
					try:
						try:
							until_timeout = self.evm.until(d.event_timeout_label) if d.timing_out else None
						except EventError:
							until_timeout = "ELAPSED"
						try:
							until_decay = self.evm.until(d.offset_decay_label) if d.decaying else None
						except EventError:
							until_decay = "ELAPSED"

						disc_attrs = [d.initial_blit, d.allow_blit, d.index, d.on_timestamp, d.off_timestamp, d.fixation_timestamp, d.exit_time, until_timeout, until_decay, d.timed_out]
						self.log_f.write("\nD{2}, initial_blit: {0}, allow_blit: {1}, on: {3}, off: {4}, fixation: {5}, exit: {6}, decay_in: {8},  timed_out: {9}, timeout_in: {7}".format(*disc_attrs))
						self.log_f.write(" +")
					except AttributeError:
						pass
				self.log_f.write("\n")

		if disc_location:
			# display discs
			for d in [disc_location, disc_location.previous_disc, disc_location.next_disc]:
				if isinstance(d, DiscLocation) and d.allow_blit: d.blit()

		flip()

		if disc_location:
			#  log timestamps for discs turning on or off
			for d in [disc_location, disc_location.previous_disc, disc_location.next_disc]:
				if isinstance(d, DiscLocation):
					timestamp = [self.evm.trial_time, self.el.now()]
					if d.allow_blit:
						if not d.on_timestamp:
							d.record_presentation(timestamp)
						if d.decaying:
							d.check_decay()
					elif d.initial_blit and not d.off_timestamp:
						d.record_removal(timestamp)

	def generate_locations(self):
		self.n_back_index = self.saccade_count - (2 + self.n_back)  # 1 for index, 1 b/c  n_back counts from penultimate saccade
		failed_generations = 0

		# generate locations until there are enough for the trial
		while len(self.disc_locations) < self.saccade_count:
			ui_request()
			try:
				self.disc_locations.append(DiscLocation())
			except TrialException:
				failed_generations += 1
				if failed_generations > 10:
					raise
				self.generate_locations()

	def quit(self):
		if P.development_mode:
			exception_list = traceback.format_stack()
			exception_list = exception_list[:-2]
			exception_list.extend(traceback.format_tb(sys.exc_info()[2]))
			exception_list.extend(traceback.format_exception_only(sys.exc_info()[0], sys.exc_info()[1]))

			exception_str = "Traceback (most recent call last):\n"
			exception_str += "".join(exception_list)
			self.log_f.write(exception_str[:-1])
		self.log_f.close()
		super(WaldoMkIII, self).quit()






"""
1. if l_prev has been exited, l_next should be displayed
 1a. if there is no l_prev, when initial fixation has been left, l_next should be displayed
 1b. once displayed, the absolute value of the disc's timeout should be the idi plus the time remaining
     on l_current before it would time out

"""