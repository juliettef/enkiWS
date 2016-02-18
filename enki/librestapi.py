import datetime
import webapp2_extras.security

from google.appengine.ext import ndb

import enki.libdisplayname
from enki.modelrestapiconnecttoken import EnkiModelRestAPIConnectToken


MAX_AGE = 5    # in minutes, duration of a connection token validity


def generate_connect_code():
	return webapp2_extras.security.generate_random_string( length = 5, pool = webapp2_extras.security.UPPERCASE_ALPHANUMERIC )


def generate_auth_token():
	return webapp2_extras.security.generate_random_string( length = 42, pool = webapp2_extras.security.ALPHANUMERIC )


def cleanup_and_get_new_connection_token( user_id ):
	# note: ensure user is logged in and has display name before calling this function
	if user_id:
		# delete any existing connect token for the user
		ndb.delete_multi_async( fetch_EnkiModelRestAPIConnectToken_by_user( user_id ))
		# create a new token and return it
		current_display_name = enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( user_id )
		if current_display_name:
			token = generate_connect_code()
			entity = EnkiModelRestAPIConnectToken( token = token, prefix = current_display_name.prefix, user_id = int( user_id ))
			entity.put()
			return token
	return None


#=== QUERIES ==================================================================


def get_EnkiModelRestAPIConnectToken_by_token_prefix_valid_age( token, prefix ):
	entity = EnkiModelRestAPIConnectToken.query( ndb.AND( EnkiModelRestAPIConnectToken.token == token,
	                                                      EnkiModelRestAPIConnectToken.prefix == prefix,
	                                                      EnkiModelRestAPIConnectToken.time_created > ( datetime.datetime.now( ) - datetime.timedelta( minutes = MAX_AGE )))).get()
	return entity


def fetch_EnkiModelRestAPIConnectToken_by_user( user_id ):
	list = EnkiModelRestAPIConnectToken.query( EnkiModelRestAPIConnectToken.user_id == user_id ).fetch( keys_only = True )
	return list


def fetch_old_rest_api_connect_tokens( ):
	list = EnkiModelRestAPIConnectToken.query( EnkiModelRestAPIConnectToken.time_created < ( datetime.datetime.now( ) - datetime.timedelta( minutes = MAX_AGE ))).fetch( keys_only = True )
	return list
