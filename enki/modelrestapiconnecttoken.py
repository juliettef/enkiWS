import datetime
import webapp2_extras.security

from google.appengine.ext import ndb
from google.appengine.ext.ndb import model


class EnkiModelRestAPIConnectToken( model.Model ):

	#=== MODEL ====================================================================

	token = model.StringProperty()
	user_id = model.IntegerProperty()
	time_created = model.DateTimeProperty( auto_now_add = True )

	#=== CONSTANTS ================================================================

	MAX_AGE = 5    # in minutes, duration of a connection token validity

	#=== QUERIES ==================================================================

	@classmethod
	def get_by_user_id_token_valid_age( cls, user_id, token ):
		return cls.query( ndb.AND( cls.user_id == user_id, cls.token == token,
								   cls.time_created > ( datetime.datetime.now() - datetime.timedelta( minutes = cls.MAX_AGE )))).get()

	@classmethod
	def fetch_by_user( cls, user_id ):
		return cls.query( cls.user_id == user_id ).fetch( keys_only = True )

	@classmethod
	def fetch_expired( cls ):
		return cls.query( cls.time_created < ( datetime.datetime.now() - datetime.timedelta( minutes = cls.MAX_AGE ))).fetch( keys_only = True )

	#=== UTILITIES ================================================================

	@classmethod
	def cleanup_and_get_new_connection_token( cls, user_id ):
		# note: ensure user is logged in and has display name before calling this function
		if user_id:
			# delete any existing connect token for the user
			ndb.delete_multi_async( cls.fetch_by_user( user_id ))
			# create a new token and return it
			token = cls.generate_connect_code()
			entity = cls( token = token, user_id = int( user_id ))
			entity.put()
			return token
		return None

	@classmethod
	def generate_connect_code( cls ):
		return webapp2_extras.security.generate_random_string( length = 5, pool = webapp2_extras.security.UPPERCASE_ALPHANUMERIC)
