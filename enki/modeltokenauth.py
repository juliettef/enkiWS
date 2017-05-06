import datetime

from google.appengine.ext import ndb
from google.appengine.ext.ndb import model

import settings


class EnkiModelTokenAuth( model.Model ):

	#=== MODEL ====================================================================

	token = model.StringProperty() # unique
	user_id = model.IntegerProperty() # the ndb ID nr
	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )

	#=== QUERIES ==================================================================

	@classmethod
	def count_by_user_id( cls, user_id ):
		count = cls.query( cls.user_id == user_id, cls.time_updated > ( datetime.datetime.now() - datetime.timedelta( hours = settings.SESSION_MAX_IDLE_AGE ))).count()
		return count

	@classmethod
	def fetch_keys_by_user_id( cls, user_id ):
		keys = cls.query( cls.user_id == user_id, cls.time_updated > ( datetime.datetime.now() - datetime.timedelta( hours = settings.SESSION_MAX_IDLE_AGE ))).fetch(keys_only = True)
		return keys

	@classmethod
	def fetch_by_user_id( cls, user_id ):
		list = cls.query( cls.user_id == user_id, cls.time_updated > ( datetime.datetime.now() - datetime.timedelta( hours = settings.SESSION_MAX_IDLE_AGE ))).order( -cls.time_updated ).fetch()
		return list

	@classmethod
	def fetch_keys_by_user_id_token( cls, user_id, token ):
		return cls.query( ndb.AND( cls.user_id == user_id, cls.token == token, cls.time_updated > ( datetime.datetime.now() - datetime.timedelta( hours = settings.SESSION_MAX_IDLE_AGE )))).fetch( keys_only = True )

	@classmethod
	def get_by_user_id_token( cls, user_id, token ):
		return cls.query( ndb.AND( cls.user_id == user_id, cls.token == token, cls.time_updated > ( datetime.datetime.now() - datetime.timedelta( hours = settings.SESSION_MAX_IDLE_AGE )))).get()

	@classmethod
	def fetch_keys_expired( cls ):
		return cls.query( cls.time_updated < ( datetime.datetime.now() - datetime.timedelta( hours = settings.SESSION_MAX_IDLE_AGE ))).fetch( keys_only = True )

	#=== UTILITIES ================================================================

	@classmethod
	def delete( cls, token_auth_id ):
		ndb.Key( cls, int( token_auth_id )).delete()

	@classmethod
	def revoke_user_authentications( cls, user_id ):
		tokens = cls.fetch_keys_by_user_id( user_id )
		if tokens:
			ndb.delete_multi( tokens )

	@classmethod
	def get_user_authentications( cls, user_id, token ):
		item = cls.get_by_user_id_token( user_id, token )
		if item:
			item.put_async()
			return True
		return False
