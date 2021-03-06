#!/usr/bin/env python3
# coding: utf-8

# Copyright © 2016 Bharadwaj Raju <bharadwaj.raju777@gmail.com>
# All Rights Reserved.

# This file is part of WeatherDesk.
#
# WeatherDesk is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# WeatherDesk is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WeatherDesk (in the LICENSE file).
# If not, see <http://www.gnu.org/licenses/>.

from urllib.request import urlopen
import urllib.error
import os
import time
import datetime
import json
import sys
import argparse
import Desktop
import traceback
import psutil
import subprocess as sp

NAMING_RULES = '''
This is how to name files in the wallpaper directory:\n

	   WEATHER		   |	FILENAME
_________________________|________________
 Clear, Calm, Fair:	  | normal{0}
 Thunderstorm:		   | thunder{0}
 Windy, Breeze, Gale:	| wind{0}
 Drizzle, Rain, Showers: | rain{0}
 Snow:				   | snow{0}
 Cloudy:				 | cloudy{0}
 Other:				  | normal{0}

 If using with --time or --time 3, add:
 "day-", "night-" or "evening-" in front of filename.

 If using with --time 4, add:
 "morning-", "day-", "evening-" or "night-"

 If using with --time 2, add:
 "day-" or "night-"
'''


# Arguments

arg_parser = argparse.ArgumentParser(
	description='''WeatherDesk - Change the wallpaper based on the weather
	(Uses the Yahoo! Weather API)''',
	formatter_class=argparse.RawTextHelpFormatter)

arg_parser.add_argument(
	'-d', '--dir', metavar='directory', type=str,
	help='Specify wallpaper directory. Default: %s' % '~/.weatherdesk_walls',
	required=False)

arg_parser.add_argument(
	'-f', '--format', metavar='format', type=str,
	help='Specify image file format. Default: %s' % '.jpg',
	required=False)

arg_parser.add_argument(
	'-w', '--wait', metavar='seconds', type=int,
	help='Specify time (in seconds) to wait before updating. Default: 600',
	required=False)

arg_parser.add_argument(
	'-t', '--time', nargs='?',
	help='''Use different backgrounds for different times.\n
Variations:
  2 = day/night
  3 = day/evening/night [Default]
  4 = morning/day/evening/night

See --naming.''',
	type=int, choices=[2, 3, 4], const=3, required=False)

arg_parser.add_argument(
	'-n', '--naming', action='store_true',
	help='Show the image file-naming rules and exit.',
	required=False)

arg_parser.add_argument(
	'-c', '--city', metavar='name', type=str,
	help=str('Specify city for weather. If not given, taken from ipinfo.io.'),
	nargs='+', required=False)

arg_parser.add_argument(
	'-s', '--skipweather', action='store_true',
	help='Skip fetching the weather from web. Uses only normal weather.',
	required=False)

arg_parser.add_argument(
	'-i', '--intervals', type=str,
	help='Skip fetching the weather from web. Uses only normal weather. Overwrites the --time argument.',required=False)

args = arg_parser.parse_args()

if not args.skipweather:

	# assign city only if fetching
	if args.city:

		city = ' '.join(args.city).replace(' ', '%20')

	else:

		try:

			city_json_url = 'http://ipinfo.io/json'

			city_json = urlopen(city_json_url).read().decode('utf-8')

			city = json.loads(city_json)
			city = city['city'].replace(' ', '%20')

		except urllib.error.URLError:

			sys.stderr.write(
				'Finding city from IP failed! Specify city manually with --city.')

			sys.exit(1)

		except ValueError:

			sys.stderr.write(
				'Finding city from IP failed! Specify city manually with --city.')

			sys.exit(1)

		if not city:

			sys.stderr.write(
				'Finding city from IP failed! Specify city manually with --city.')

			sys.exit(1)

	# Check if city is valid

	try:

		city_check_json_url = r'https://query.yahooapis.com/v1/public/yql?q=select%20%2A%20from%20geo.places(5)%20where%20text%3D"' + city + r'"&format=json'

		city_check_json = urlopen(city_check_json_url).read().decode('utf-8')

		city_check_json = json.loads(city_check_json)

		if city_check_json['query']['results'] in (None, 'null'):

			city_is_invalid = True

		else:

			city_is_invalid = False

		city_is_invalid = city_check_json['query']['results'] in (None, 'null')

		city_checked = True

	except:

		trace_city_check = '[City checking]\n' + traceback.format_exc()

		city_checked = True

		city_is_invalid = True  # exit, but after printing stack trace

	else:

		trace_city_check = '[City checking] No error.'

	finally:

		print(trace_city_check)

	if city_checked and city_is_invalid:

		sys.stderr.write('Invalid city! Please check the name.')

		sys.exit(1)
else:
	print('Skipping weather, thus no city checking.')

use_time = bool(args.time) or bool(args.intervals)
use_intervals = bool(args.intervals)

intervals = None

if use_intervals:
	# parse intervals

	intervals_str = str(args.intervals).split(':')

	#TODO check correct format
	if len(intervals_str) < 2 or len(intervals_str) > 4:

		sys.stderr.write('Invalid intervals! Please check the number of intervals and the separator used.')

		sys.exit(1)

	intervals = [];
	for interv in intervals_str:

		try:

			intervals.append(int(interv))

		except ValueError:

			sys.stderr.write('Invalid value for interval! Please check the intervals.')

			sys.exit(1)


if use_time and not use_intervals:
	# set intervals if not specified by arg

	'''
	For detail level 2:
	06 to 20: day
	20 to 06: night
	'''

	'''
	For detail level 3:
	06 to 17: day
	17 to 20: evening
	20 to 06: night
	'''

	'''
	For detail level 4:
	06 to 08: morning
	08 to 17: day
	17 to 20: evening
	20 to 06: night
	'''

	if args.time == 2:

		intervals = [6,20]

	elif args.time == 3:

		intervals = [6,17,20]

	elif args.time == 4:

		intervals = [6,8,17,20]

	else:

		intervals = [6,20]

len_intervals = 0

#print intervals
if intervals is None:

	print('No times used.')

else:

	len_intervals = len(intervals)

	print('Using times:')

	for interv in intervals:

		print(interv)


if args.dir:

	# User provided a directory
	walls_dir = os.path.abspath(args.dir)

	if not os.path.isdir(walls_dir):

		sys.stderr.write('Invalid directory %s.' % walls_dir)
		sys.exit(1)
else:

	walls_dir = os.path.join(os.path.expanduser('~'), '.weatherdesk_walls')

	if not os.path.isdir(walls_dir):

		os.mkdir(walls_dir)
		fmt = '''No directory specified.
Creating in {}... Put files there or specify directory with --dir'''
		sys.stderr.write(fmt.format(walls_dir))
		sys.exit(1)

if args.format:

	if not args.format.startswith('.'):

		args.format = '.' + args.format

	file_format = args.format

else:

	file_format = '.jpg'

wait_time = args.wait or 600  # ten minutes

if args.naming:

	print(NAMING_RULES.format(file_format))
	sys.exit(0)

# Functions

def get_time_of_day(intervals):

	current_time = datetime.datetime.now()

	level = len(intervals)

	if level == 3:

		if current_time.hour in range(intervals[0], intervals[1]):

			return 'day'

		elif current_time.hour in range(intervals[1], intervals[2]):

			return 'evening'

		else:

			return 'night'

	elif level == 4:

		if current_time.hour in range(intervals[0], intervals[1]):

			return 'morning'

		elif current_time.hour in range(intervals[1], intervals[2]):

			return 'day'

		elif current_time.hour in range(intervals[2], intervals[3]):

			return 'evening'

		else:

			return 'night'

	else:

		if current_time.hour in range(intervals[0], intervals[1]):

			return 'day'

		else:

			return 'night'

def get_file_name(weather_name, intervals, skipweather=False):

	summaries = {'rain': 'drizzle rain shower',
				 'wind': 'breez gale wind',  # breez matches both breeze and breezy
				 'thunder': 'thunder',
				 'snow': 'snow',
				 'cloudy': 'cloud'}

	def get_weather_summary(skipweather=False):

		if not skipweather:

			for summary, words in summaries.items():

				for word in words.split():

					if word in weather_name:

						return summary

		return 'normal'

	weather_file = get_weather_summary(skipweather) + file_format

	if intervals is not None:

		return get_time_of_day(intervals) + '-' + weather_file

	return weather_file


def check_if_all_files_exist(time=False, level=3, skipweather=False):

	all_exist = True

	required_files = ['rain', 'snow', 'normal', 'cloudy', 'wind', 'thunder']

	if skipweather:

		required_files = [ 'normal' ]


	if time:

		if level == 3:

			daytime = ['day', 'evening', 'night']

		elif level == 4:

			daytime = ['morning', 'day', 'evening', 'night']

		else:  # level 2

			daytime = ['day', 'night']

		required_files = [
			moment + '-' + weather

			for moment in daytime
			for weather in required_files]

	for i in required_files:

		file_path = os.path.join(walls_dir, (i + file_format))

		if not os.path.isfile(file_path):

			all_exist = False

			sys.stderr.write(file_path + '\n')

	return all_exist


if not check_if_all_files_exist(time=use_time, level=len_intervals, skipweather=args.skipweather):

	sys.stderr.write(
		'\nNot all required files were found.\n %s' % NAMING_RULES.format(
			file_format))

	sys.exit(1)

def restart_program():

	# Restarts the current program, with file objects and descriptors cleanup

	new_weatherdesk_cmd = ''

	for i in sys.argv:

		new_weatherdesk_cmd = ' ' + i

	sp.Popen([new_weatherdesk_cmd], shell=True)

	sys.exit(0)

# Main loop

while True:

	try:
		weather = 'normal'
		if not args.skipweather:

			weather_json_url = r'https://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20weather.forecast%20where%20woeid%20in%20(select%20woeid%20from%20geo.places(1)%20where%20text%3D%22' + city + '%22)&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys'

			weather_json = json.loads(urlopen(weather_json_url).read().decode('utf-8'))

			weather = str(weather_json['query']['results']['channel']['item']['condition']['text']).lower()

			city_with_area=str(weather_json['query']['results']['channel']['location']['city']) + str(weather_json['query']['results']['channel']['location']['region'])

			print(weather)
			print(city_with_area)

		else:

			print('Skipping weather, using ' + weather + '.')

		file_name =  get_file_name(weather, intervals, skipweather=args.skipweather)
		print(os.path.join(walls_dir,file_name))

		Desktop.set_wallpaper(os.path.join(walls_dir, file_name))

	except urllib.error.URLError:

		# Don't shut off on temporary network problems

		trace_main_loop = '[Main loop] \n' + traceback.format_exc()


		if sys.platform.startswith('linux'):

			# HACK: glibc on Linux only loads /etc/resolv.conf once
			# This breaks our network communications after suspend/resume
			# So we force it to reload using the res_init() function

			# But sometimes res_init() mysteriously crashes the program
			# and it's too low-level for any try-except to catch.

			# So we restart the whole thing!

			restart_program()

	except ValueError:

		# Sometimes JSON returns a null value for no reason

		trace_main_loop = '[Main loop] \n' + traceback.format_exc()

	except:

		# All other errors (except KeyboardInterrupt ^C)
		# We'll still have a full stack trace

		trace_main_loop = '[Main loop] \n' + traceback.format_exc()

	else:

		trace_main_loop = '[Main loop] No error.'

	finally:

		print(trace_main_loop)

	time.sleep(wait_time)
