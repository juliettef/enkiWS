import os
import urllib
import datetime

import webapp2
import webapp2_extras
import webapp2_extras.i18n
import webapp2_extras.security

from markdown2 import markdown2

import settings
import enki.textmessages as MSG


ENKILIB_OK = 1
ENKILIB_ERROR = -1


def format_timedelta( timedelta ):
	seconds = minutes = hours = days = 0
	result = ''
	if timedelta.days:
		days = timedelta.days
		result = " ".join([ str( days ), MSG.UNIT_DAY( days )])
	if timedelta.seconds:
		seconds = timedelta.seconds
		hours = seconds // 3600
		if hours:
			result = " ".join([ result, str( hours ), MSG.UNIT_HOUR( hours )])
		minutes = ( seconds % 3600 ) // 60
		if minutes:
			result = " ".join([ result, str( minutes ), MSG.UNIT_MINUTE( minutes )])
		seconds = seconds - hours * 3600 - minutes * 60
		result = " ".join([ result, str( seconds ), MSG.UNIT_SECOND( seconds )])
	return result


def make_local_url( locale, route_name, parameters ):
# example input: make_local_url( 'fr_FR' , 'login', { 'key1':'value1', 'key2':'value2', '_fragment':'top' })
# example output: http://www.mysite.com/login?locale=fr_FR&key1=value1&key2=value2#top
	temp_params = {} # modify a temporary dict so as not to modify parameters as this affects the jinja template
	url = ''
	for key, value in parameters.items():
		# parameters cleanup: remove parameters with blank values and UTF-8 encode the remaining values.
		if value:
			temp_params[ key ] = value.encode('utf-8')
	if locale:
		# add locale parameter to the parameters dictionnary
		# temp_params[ 'locale' ] = locale.encode('utf-8')
		url = webapp2.uri_for( 'locale-' + route_name, locale = locale.encode('utf-8'), _full = True, **temp_params )
	else:
		url = webapp2.uri_for( route_name, _full = True, **temp_params )
	return url


def get_local_url( route_name = 'home', parameters = {} ):
	return make_local_url( webapp2_extras.i18n.get_i18n().locale, route_name, parameters )


def strip_locale_from_path( path, localetostrip ):
	output_path = path
	if not localetostrip:
		localetostrip = 'en_US'
	llength = len(localetostrip)
	if output_path[1:llength + 1] == localetostrip:
		output_path = output_path[llength + 1:]
	return output_path


def strip_current_locale_from_path( path ):
	dirstrip = webapp2_extras.i18n.get_i18n().locale
	return strip_locale_from_path( path , dirstrip )


def urlencode( fields ):
	fields_non_unicode = {}
	for i, item in fields.iteritems():
		if isinstance( item, unicode ):
			item = item.encode( 'utf8' )
		fields_non_unicode[ i ] = item
	return urllib.urlencode( fields_non_unicode )


def is_debug():
# check whether we're running locally or on GAE, or in forced debug mode
	output = os.environ[ "SERVER_SOFTWARE" ]
	if "Development" in output or settings.ENKI_FORCE_DEBUG == True:
		return True
	else:
		return False

def is_develop_server():
# check whether we're running locally or on GAE, or in forced debug mode
	output = os.environ[ "SERVER_SOFTWARE" ]
	if "Development" in output:
		return True
	else:
		return False

def xstr( value ):
	if not value:
		return ''
	else:
		if type( value ) is not unicode:
			value = str( value )
		import cgi
		escaped = cgi.escape( value, quote = True )
		return escaped

def xint( value ):
	if not value or not value.isdigit():
		return 0
	else:
		return int( value )

def seconds_from_epoch( date_time ):
	return int(( date_time - datetime.datetime.utcfromtimestamp( 0 )).total_seconds())

def generate_auth_token():
	return webapp2_extras.security.generate_random_string( length = 42, pool = webapp2_extras.security.ALPHANUMERIC )

def generate_connect_code():
	return webapp2_extras.security.generate_random_string( length = 5, pool = webapp2_extras.security.UPPERCASE_ALPHANUMERIC )

def markdown_escaped_nofollow( text ):
	# safe version of markdown
	return markdown2.markdown( text, safe_mode='escape', extras=["nofollow"])
