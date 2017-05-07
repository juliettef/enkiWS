import datetime

from google.appengine.ext import ndb
from google.appengine.ext.ndb import model

import settings


class EnkiModelTokenAuth( model.Model ):

	#=== MODEL ====================================================================

	token = model.StringProperty() # unique
	user_id = model.IntegerProperty() # the ndb ID nr
	keep_logged_in = model.BooleanProperty( default = False )
	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )

	#=== QUERIES ==================================================================

	@classmethod
	def query_by_user_id( cls, user_id ):
		return cls.query( ndb.OR( ndb.AND( cls.user_id == user_id,
										   cls.time_updated > ( datetime.datetime.now() - datetime.timedelta( seconds = settings.SESSION_MAX_IDLE_AGE ))),
								  ndb.AND( cls.user_id == user_id,
										   cls.keep_logged_in == True,
										   cls.time_updated > ( datetime.datetime.now() - datetime.timedelta( seconds = settings.SESSION_MAX_IDLE_AGE_KEEP_LOGGED_IN )))))

	@classmethod
	def query_by_user_id_token( cls, user_id, token ):
		return cls.query_by_user_id( user_id ).filter( cls.token == token )

	@classmethod
	def count_by_user_id( cls, user_id ):
		return cls.query_by_user_id( user_id ).count()

	@classmethod
	def fetch_keys_by_user_id( cls, user_id ):
		return cls.query_by_user_id( user_id ).fetch( keys_only = True )

	@classmethod
	def fetch_by_user_id( cls, user_id ):
		return cls.query_by_user_id( user_id ).order( -cls.time_updated ).fetch()

	@classmethod
	def fetch_keys_by_user_id_token( cls, user_id, token ):
		return cls.query_by_user_id_token( user_id, token ).fetch( keys_only = True )

	@classmethod
	def get_by_user_id_token( cls, user_id, token ):
		return cls.query_by_user_id_token( user_id, token ).get()

	@classmethod
	def fetch_keys_expired( cls ):
		return cls.query( ndb.OR( cls.time_updated > ( datetime.datetime.now() - datetime.timedelta( seconds = settings.SESSION_MAX_IDLE_AGE_KEEP_LOGGED_IN )),
								  ndb.AND( cls.keep_logged_in == False,
										   cls.time_updated > ( datetime.datetime.now() - datetime.timedelta( seconds = settings.SESSION_MAX_IDLE_AGE ))))
						  ).fetch( keys_only = True )

	#=== UTILITIES ================================================================

	@classmethod
	def delete( cls, token_auth_id ):
		ndb.Key( cls, int( token_auth_id )).delete()

	@classmethod
	def revoke_user_authentications( cls, user_id ):
		tokens = cls.fetch_keys_by_user_id( user_id )
		if tokens:
			ndb.delete_multi( tokens )
