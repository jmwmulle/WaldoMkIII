import random
# KlibsTesting Param overrides
#
# Any param that is commented out by default is either deprecated or else not yet implemented--don't uncomment or use
#
#########################################
# Available Hardware
#########################################
eye_tracker_available = True
eye_tracking = True
labjack_available = True
labjacking = False
#
#########################################
# Environment Aesthetic Defaults
#########################################
default_fill_color = (45, 45, 45, 255)
default_color = (255, 255, 255, 255)
default_response_color = default_color
default_input_color = default_color
default_font_size = 28
default_font_name = 'Frutiger'
default_timeout_message = "Too slow!"
#
#########################################
# EyeLink Sensitivities
#########################################
saccadic_velocity_threshold = 20
saccadic_acceleration_threshold = 5000
saccadic_motion_threshold = 0.15
#
fixation_size = 1,  # deg of visual angle
box_size = 1,  # deg of visual angle
cue_size = 1,  # deg of visual angle
cue_back_size = 1,  # deg of visual angle
#
#########################################
# Experiment Structure
#########################################
multi_session_project = False
collect_demographics = True
practicing = True
trials_per_block = 240
blocks_per_experiment = 2
trials_per_participant = 0
table_defaults = {}
#
#########################################
# Development Mode Settings
#########################################
dm_suppress_debug_pane = False
dm_auto_threshold = True
dm_trial_show_mouse = True
#
#########################################
# Data Export Settings
#########################################
data_columns = None
default_participant_fields = [["userhash", "participant"], "sex", "age", "handedness"]
default_participant_fields_sf = [["userhash", "participant"], "random_seed", "sex", "age", "handedness"]

#
#########################################
# Demographics Questions
#########################################
# Note: This list must supply all columns in the configured Participants table except:
# 	- id
# 	- participant id
# 	- random_seed
#	- klibs_commit (if present)
#	- created
# These columns must be present in the participants table (except klibs_commit) and are supplied automatically by klibs
demographic_questions = [
	['sex', "What is your sex? \nAnswer with:  (m)ale,(f)emale", ('m', 'M', 'f', 'F'), 'str', random.choice(['m', 'f'])],
	['handedness', "Are right-handed, left-handed or ambidextrous? \nAnswer with (r)ight, (l)eft or (a)mbidextrous.",
	 ('r', 'R', 'l', 'L', 'a', 'A'), 'str', 'r'],
	['age', 'What is  your age?', None, 'int', -1]
]

#
#########################################
# PROJECT-SPECIFIC VARS
#########################################
# The following constants are imported by experiment.py and DiscLocation.py
PRESENT_INTER_SACCADE = "pres_inter_saccade"
PRESENT_ON_FIXATION = "pres_on_fixation"
REMOVE_ON_DECAY = "rem_on_decay"
REMOVE_ON_PRESENTATION = "rem_on_presentation"
REMOVE_INTER_SACCADE = "rem_inter_saccade"

target_removal_behavior = {REMOVE_ON_DECAY: False, REMOVE_ON_PRESENTATION: False, REMOVE_INTER_SACCADE: True}
target_presentation_behavior = {PRESENT_INTER_SACCADE: True, PRESENT_ON_FIXATION: False}

use_bg_images = True

fixation_interval = 2984  # ms, remember to remove 16ms to allow for screen refresh (ie. 3000 = 2984)
drift_correct_initial_persist = 1000  # ms
disc_timeout_interval = 10000  # ms
final_disc_timeout_interval = 2000  # ms

fixation_top = [None, None]
fixation_central = [None, None]
fixation_bottom = [None, None]

exp_meta_factors = {"fixation": [fixation_top, fixation_central, fixation_bottom]}