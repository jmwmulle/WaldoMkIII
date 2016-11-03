__author__ = "Jonathan Mulle"

from random import randrange
from klibs.KLExceptions import TrialException
from klibs import P
from klibs.KLEnvironment import EnvAgent
from klibs.KLConstants import CIRCLE_BOUNDARY, EL_GAZE_POS, EL_FIXATION_END, EL_SACCADE_END
from klibs.KLUtilities import line_segment_len, angle_between, point_pos
from klibs.KLUserInterface import ui_request
from klibs.KLGraphics import blit
from klibs.KLCommunication import message
from klibs.KLEventInterface import TrialEventTicket as TET

LOC = "location"
AMP = "amplitude"
ANG = "angle"
NEW = "new"
OLD = "old"
RED = [236, 88, 64, 255]
WHITE = [255,255,255,255]
GREY = [125,125,125,255]
BLACK = [0,0,0,255]
BG_ABSENT = "absent"
BG_PRESENT = "present"
BG_INTERMITTENT = "intermittent"

INITIAL_FIXATION = "initial fixation"

class DiscLocation(EnvAgent):

	def __init__(self):
		super(DiscLocation, self).__init__()
		self.__exit_time__ = None
		self.__timed_out__ = True # only set to false once fixated
		self.errors = 0
		try:
			self.origin = self.exp.disc_locations[-1].x_y_pos
		except IndexError:
			self.origin = P.screen_c
		self.initial_blit = False
		self.amplitude = None
		self.angle = None
		self.secondary_angle = None
		self.rotation = 0
		self.index = len(self.exp.disc_locations)
		self.boundary = "saccade_{0}".format(self.index)
		self.secondary_boundary = "saccade_{0}_secondary".format(self.index)
		self.x_y_pos = (None, None)
		self.secondary_x_y_pos = (None, None)
		self.x_range = range(self.exp.display_margin, P.screen_x - self.exp.display_margin)
		self.y_range = range(self.exp.display_margin, P.screen_y - self.exp.display_margin)
		self.viable = True
		self.exp.search_disc_proto.fill = self.exp.search_disc_color
		self.decaying = False
		self.timing_out = False
		if P.target_presentation_behavior[P.PRESENT_INTER_SACCADE] is True:
			self.presentation_behavior = P.PRESENT_INTER_SACCADE
		else:
			self.presentation_behavior = P.PRESENT_ON_FIXATION

		if P.target_removal_behavior[P.REMOVE_ON_PRESENTATION] is True:
			self.removal_behavior = P.REMOVE_ON_PRESENTATION
		elif P.target_removal_behavior[P.REMOVE_INTER_SACCADE] is True:
			self.removal_behavior = P.REMOVE_INTER_SACCADE
		else:
			self.removal_behavior = P.REMOVE_ON_DECAY
		self.timeout_interval = P.disc_timeout_interval + P.target_presentation_behavior[P.PRESENT_ON_FIXATION]
		self.penultimate_disc = self.index == self.exp.saccade_count - 2
		self.n_back = self.index == self.exp.n_back_index

		# next attributes are for use during trial
		self.on_timestamp = None
		self.off_timestamp = None

		# records the onset time of the timeout event, to be updated after first blit
		self.fixation_timestamp = None  # will be self.evm.trial_time & eyelink.now() if fixated before timeout
		self.rt = None  # only the final location will populate this value
		self.first_disc = False
		self.final_disc = self.index == self.exp.saccade_count - 1
		self.using_secondary_pos = (self.final_disc and self.exp.target_count == 2)
		self.saccade_choice = None
		self.allow_blit = False
		
		self.decay_interval = P.target_removal_behavior[P.REMOVE_ON_DECAY]
		if self.index == 0:
			self.first_disc = True
			self.allow_blit = True

		if self.final_disc:
			self.timeout_interval = P.final_disc_timeout_interval

		while self.angle is None:
			ui_request()
			try:
				self.__generate_location__()
			except TrialException:
				self.errors += 1
				if self.errors > 10:
					raise

		self.disc = self.exp.search_disc_proto.render()
		self.name = "L_{0}_{1}x{2}".format(self.index, self.x_y_pos[0], self.x_y_pos[1])
		self.event_start_label = self.name + "_start"
		self.event_timeout_label = self.name + "_timeout"
		self.event_fixate_label = self.name + "_fixate"
		self.event_exit_label = self.name + "_exit"
		self.onset_delay_label = self.name + "_onset_delay_disc"
		self.offset_decay_label = self.name + "_offset_decay_disc"
		if P.dm_show_disc_indices:
			self.index_str = message(str(self.index), "disc test", blit_txt=False)
			self.secondary_index_str = message(str(self.index) + "-2", "disc test", blit_txt=False)

	def __str__(self):
		f = "F" if self.final_disc else "x"
		p = "P"if self.penultimate_disc else "x"
		n = "N"if self.n_back else "x"
		str_vars = list(self.x_y_pos) + list(self.origin)
		str_vars.extend([self.amplitude, self.angle, hex(id(self)), self.index, f, p, n])
		return "<DiscLocation {7}{8}{9}{10} ({0},{1}) from ({2},{3}) ({4}px along {5} deg) at {6}>".format(*str_vars)

	def __generate_location__(self):
		if self.final_disc:
			n_back = self.exp.disc_locations[self.exp.n_back_index]
			penultimate = self.exp.disc_locations[-1]
			angle = self.exp.angle
			amplitude = int(line_segment_len(n_back.x_y_pos, penultimate.x_y_pos))
			self.rotation = angle_between(penultimate.x_y_pos, n_back.x_y_pos)
			if self.using_secondary_pos:
				self.secondary_angle = angle - 180
				if self.secondary_angle < 0:
					self.secondary_angle = angle + 180
				self.secondary_x_y_pos = point_pos(self.origin, amplitude, self.secondary_angle, self.rotation)
		else:
			amplitude = randrange(self.exp.min_amplitude, self.exp.max_amplitude)
			angle = randrange(0, 360)
		self.x_y_pos = point_pos(self.origin, amplitude, angle, self.rotation)
		# ensure disc is inside drawable bounds; if penultimate saccade, ensure all final saccade angles are possible
		self.__margin_check()
		self.__penultimate_viability_check__()

		# assign generation output
		self.angle = angle
		self.amplitude = amplitude
		self.__add_eyelink_boundary__()

	def __margin_check(self, p=None, penultimate=False):
		if not p: p = self.x_y_pos
		m = self.exp.display_margin
		if not (m < p[0] < P.screen_x - m and m < p[1] < P.screen_y - m):
			raise TrialException("{0}ocation inviable.".format("(P)l" if penultimate else "L"))

	def __penultimate_viability_check__(self):
		if not self.penultimate_disc:
			return
		d_xy = line_segment_len(self.x_y_pos, self.exp.disc_locations[self.exp.n_back_index].x_y_pos)
		disc_diam = self.exp.search_disc_proto.surface_width
		if d_xy - disc_diam < disc_diam:
			raise ValueError("Penultimate target too close to n-back target.")
		theta = angle_between(self.x_y_pos, self.exp.disc_locations[self.exp.n_back_index].x_y_pos)
		for a in range(0, 360, 60):
			self.__margin_check(point_pos(self.x_y_pos, d_xy, a + theta))
		self.exp.search_disc_proto.fill = self.exp.penultimate_disc_color
		self.penultimate_disc = True

	def __add_eyelink_boundary__(self):
		r = int(self.exp.search_disc_proto.surface_width + self.exp.disc_boundary_tolerance) // 2

		try:
			self.el.add_boundary(self.boundary, [self.x_y_pos, r], CIRCLE_BOUNDARY)
			if self.using_secondary_pos:
				self.el.add_boundary(self.secondary_boundary, [self.secondary_x_y_pos, r], CIRCLE_BOUNDARY)
		except AttributeError:
			self.exp.add_boundary(self.boundary, [self.x_y_pos, r], CIRCLE_BOUNDARY)
			if self.using_secondary_pos:
				self.exp.add_boundary(self.secondary_boundary, [self.secondary_x_y, r], CIRCLE_BOUNDARY)

	def __start_decay__(self):
		if P.development_mode:
			self.exp.log_f.write("\n\tD{0}: start_decay()".format(self.index))

		self.evm.register_ticket(TET(self.offset_decay_label, self.decay_interval, relative=True))
		self.decaying = True

	def blit(self):
		if P.development_mode:
			self.exp.log_f.write("\n\tD{0}: blit()".format(self.index))

		if self.allow_blit:
			blit(self.disc, 5, self.x_y_pos)
			if self.using_secondary_pos:
				blit(self.disc, 5, self.secondary_x_y_pos)
			if P.development_mode and P.dm_show_disc_indices:
				blit(self.index_str, 5, self.x_y_pos)
				if self.using_secondary_pos:
					blit(self.secondary_index_str, 5, self.secondary_x_y_pos)
			self.initial_blit = True
			if self.first_disc and self.removal_behavior == P.REMOVE_ON_PRESENTATION:
				self.exp.show_dc_target = False  # after the first disc is shown, dc_target should be off

	def boundary_check(self, check_previous=True):
		if P.development_mode:
			self.exp.log_f.write("\n\tD{0}: boundary_check(check_previous={1})".format(self.index, check_previous))

		if not self.initial_blit:
			return

		# when dc has been left for first disc, on inter_saccade trials, turn on next disc
		if self.first_disc and not self.exp.departed_dc:
			if self.presentation_behavior == P.PRESENT_INTER_SACCADE and not self.exp.el.within_boundary(INITIAL_FIXATION):
				self.next_disc.allow_blit = True
				self.exp.departed_dc = True
				if P.development_mode:
					self.exp.log_f.write("\n\tDeparted from initial fixation.")

		trial_time = self.evm.trial_time
		el_time = None
		if self.final_disc:
			event_queue = self.el.get_event_queue(include=[EL_SACCADE_END])
			el_time = self.el.saccade_to_boundary(self.boundary, EL_SACCADE_END, event_queue)
			if el_time:
				self.saccade_choice = 1
			elif self.using_secondary_pos:
				el_time = self.el.saccade_to_boundary(self.secondary_boundary, EL_SACCADE_END, event_queue)
				if el_time:
					self.saccade_choice = 2
			if P.development_mode:
				self.exp.log_f.write("\n\tD{0} checked for saccade with result: {1}".format(self.index, el_time))
		elif self.fixation_timestamp is None:
			el_time = self.el.fixated_boundary(self.boundary, EL_FIXATION_END)
		elif not self.el.within_boundary(self.boundary, EL_GAZE_POS):
			return self.record_exit([trial_time, self.el.now()])

		if check_previous and not self.previous_disc.off_timestamp:
			if P.development_mode:
				self.exp.log_f.write("\n\tBoundary checking D{0} from D{1}".format(self.previous_disc.index, self.index))
			self.previous_disc.boundary_check(False)

		return self.record_fixation([trial_time, el_time]) if el_time else False

	def check_decay(self):
		if P.development_mode:
			self.exp.log_f.write("\n\tD{0}: check_decay()".format(self.index))

		if self.removal_behavior == P.REMOVE_ON_DECAY and self.evm.registered(self.offset_decay_label):
			self.allow_blit = self.evm.before(self.offset_decay_label)

	def record_fixation(self, timestamp):
		# note: this method also records the timestamp for the **saccade** to the final disc

		if P.development_mode:
			self.exp.log_f.write("\n\tD{0}: record_fixation(timestamp={1})".format(self.index, timestamp))

		# self.evm.log_data_event(self.event_fixate_label + " (trial_time={0})".format(timestamp[0]))
		self.timed_out = False
		self.fixation_timestamp = timestamp
		self.rt = timestamp[1] - self.on_timestamp[1]  # use eye_link time for for RT
		if self.presentation_behavior == P.PRESENT_ON_FIXATION:
			self.next_disc.allow_blit = True
		if not self.final_disc:
			self.next_disc.start_timeout()
		return True

	def record_removal(self, timestamp):
		if P.development_mode:
			self.exp.log_f.write("\n\tD{0}: record_removal(timestamp={1})".format(self.index, timestamp))

		if self.off_timestamp is None:
			self.off_timestamp = timestamp

	def record_exit(self, timestamp):
		if P.development_mode:
			self.exp.log_f.write("\n\tD{0}: record_exit(timestamp={1})".format(self.index, timestamp))
		# if not self.el.within_boundary(self.boundary, EL_GAZE_POS):
		if not self.fixation_timestamp:
			raise RuntimeError("Exit timestamp recorded before fixation")
		self.exit_time = timestamp
		if self.removal_behavior == P.REMOVE_ON_DECAY:
			self.__start_decay__()
		if self.removal_behavior == P.REMOVE_INTER_SACCADE:
			self.allow_blit = False
		if self.presentation_behavior == P.PRESENT_INTER_SACCADE and not (self.penultimate_disc or self.final_disc):
			if P.development_mode:
				self.exp.log_f.write("\n\t\t*** Allowing D{0} to blit. ***".format(self.next_disc.next_disc.index))
			self.next_disc.next_disc.allow_blit = True
		else:
			if P.development_mode:
				self.exp.log_f.write("\n\t\t*** Exit Behavior Cond: {0}, Exit Disc ID: {1}***".format(self.presentation_behavior == P.PRESENT_INTER_SACCADE, not (self.penultimate_disc or self.final_disc)))

	def record_presentation(self, timestamp):
		if P.development_mode:
			self.exp.log_f.write("\n\tD{0}: record_presentation(timestamp={1})".format(self.index, timestamp))

		# eye-link time unnecessary as the eyelink will supply this in the EDF when written
		# todo: work out a coherent data-event system
		# self.evm.log_data_event(DataEvent(self.event_start_label + " (trial_time={0})".format(timestamp[0])))
		if self.on_timestamp is None:
			self.on_timestamp = timestamp
			if self.first_disc:
				self.start_timeout()

			if self.removal_behavior == P.REMOVE_ON_PRESENTATION:
				try:
					self.previous_disc.allow_blit = False
				except AttributeError:  # first disc won't have a previous disc
					pass

	def start_timeout(self):
		ticket = TET(self.event_timeout_label, self.timeout_interval, relative=True)
		if P.development_mode:
			self.exp.log_f.write("\n\tD{0}: start_timeout()".format(self.index))
			data = [ticket.name, self.evm.trial_time_ms, ticket.onset]
			self.exp.log_f.write("\n\t\tTicket '{0}' created at {1} with onset {2}".format(*data))

		self.evm.register_ticket(ticket)
		self.timing_out = True
		if P.development_mode:
			data = [self.index, self.evm.issued_tickets[self.event_timeout_label].onset, self.evm.trial_time_ms]
			self.exp.log_f.write("\n\t\tD{0} will time out at {1}, currently: {2}".format(*data))

	@property
	def exit_time(self):
		return self.__exit_time__

	@exit_time.setter
	def exit_time(self, t):
		if P.development_mode:
			self.exp.log_f.write("\n\tD{0}: exit_time = {1}".format(self.index, t))
		self.__exit_time__ = t

	@property
	def timed_out(self):
		return self.__timed_out__

	@timed_out.setter
	def timed_out(self, state):
		self.__timed_out__ = state is not False
		if self.__timed_out__:
			self.fixation_timestamp = [-1, -1]
			self.allow_blit = False

	@property
	def next_disc(self):
		try:
			return self.exp.disc_locations[self.index + 1]
		except IndexError:
			return False

	@property
	def previous_disc(self):
		if self.index > 0:
			return self.exp.disc_locations[self.index - 1]
		return False
