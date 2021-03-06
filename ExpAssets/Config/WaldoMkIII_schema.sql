/*

******************************************************************************************
						NOTES ON HOW TO USE AND MODIFY THIS FILE
******************************************************************************************
This file is used at the beginning of your project to create the database in 
which trials and participants are stored.

As the project develops, you may change the number of columns, add other tables,
or change the names/datatypes of columns that already exist.

That said,  You *really* do not need to be concerned about datatypes; in the end, everything will be a string when the data
is output. The *only* reason to change the datatypes here are to ensure that the program will throw an error if, for
example, a string is returned for something like reaction time. BUT, you should be catching this in your experiment.py
file; if the error is caught here it means you've already been collecting the wrong information and it should have
been caught much earlier.

To do this, modify the document as needed, then, in your project. To rebuild the database with
your changes just delete your database files, or just run:

  rm /KLAB/2016-2017/Projects/WaldoMkIII/ExpAssets/WaldoMkIII.db*

and run the experiment, this will force klibs to rebuild your database.

But be warned: THIS WILL DELETE ALL YOUR CURRENT DATA. The database will be completely 
destroyed and rebuilt. If you wish to keep the data you currently have, be sure to first run:

  klibs export /KLAB/2016-2017/Projects/WaldoMkIII

This wil export the database in it's current state to text files found in /KLAB/2016-2017/Projects/Data.

*/

CREATE TABLE participants (
	id integer primary key autoincrement not null,
	userhash text not null unique,
	random_seed text not null,
	sex text not null,
	age integer not null, 
	handedness text not null,
	created text not null,
	klibs_commit text not null

);

CREATE TABLE events (
	id integer primary key autoincrement not null,
	user_id integer not null,
	trial_id integer not null,
	trial_num integer not null,
	label text not null,
	trial_clock float not null,
	eyelink_clock integer
);

CREATE TABLE logs (
	id integer primary key autoincrement not null,
	user_id integer not null,
	message text not null,
	trial_clock float not null,
	eyelink_clock integer
);

CREATE TABLE trials (
	id integer primary key autoincrement not null,
	participant_id integer key not null,
	block_num integer not null,
	trial_num integer not null,
	bg_image text not null,
  timed_out text not null,
  rt float not null,
  primary_target_type text not null,
  secondary_target_type text not null,
  target_count text not null,
  target_choice text not null,
  bg_state text not null,
  n_back integer not null,
  amplitude numeric not null,
  primary_angle integer not null,
  secondary_angle integer not null,
  saccades integer not null
);

CREATE TABLE trial_locations (
  id integer primary key autoincrement not null,
  participant_id integer key not null,
  trial_id integer not null,
  trial_num integer not null,
  block_num integer not null,
  location_num integer not null,
  x integer not null,
  y integer not null,
  amplitude numeric not null,
  angle integer not null,
  n_back text not null,
  penultimate text not null,
  final text not null,
  timed_out text not null,
  rt float not null,
  fixate_trial_time float not null,
  fixate_el_time float not null
);