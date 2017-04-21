import datetime
import time

from google.appengine.ext import ndb
from google.appengine.ext.ndb import model

TIMEOUT_S = 0.1

class EnkiModelTokenVerify( model.Model ):

	token = model.StringProperty()
	email = model.StringProperty()
	user_id = model.IntegerProperty() # ndb user ID
	time_created = model.DateTimeProperty( auto_now_add = True )
	type = model.StringProperty()
	auth_ids_provider = model.StringProperty() # store auth Id info for registration

	@classmethod
	def get_by_token( cls, token ):
		entity = cls.query( cls.token == token ).get()
		return entity

	@classmethod
	def get_by_token_type( cls, token, type, retry = 0 ):
		entity = cls.query( ndb.AND( cls.token == token, cls.type == type )).get()
		if retry and not entity:
			timeout = TIMEOUT_S
			for i in range( retry ):
				entity = cls.query(ndb.AND(cls.token == token, cls.type == type)).get()
				if entity:
					break
				else:
					time.sleep(timeout)
					timeout *= 2
		return entity


	@classmethod
	def get_by_user_id_email_type( cls, user_id, email, type ):
		entity = cls.query( ndb.AND( cls.user_id == user_id, cls.email == email, cls.type == type )).get()
		return entity

	@classmethod
	def get_by_user_id_auth_id_type( cls, user_id, auth_id, type ):
		entity = cls.query( ndb.AND( cls.user_id == user_id, cls.auth_ids_provider == auth_id, cls.type == type )).get()
		return entity

	@classmethod
	def get_by_user_id_type( cls, user_id, type ):
		entity = cls.query( ndb.AND( cls.user_id == user_id, cls.type == type )).get( )
		return entity

	@classmethod	
	def get_by_auth_id_type( cls, auth_id, type ):
		entity = cls.query( ndb.AND( cls.auth_ids_provider == auth_id, cls.type == type )).get()
		return entity

	@classmethod
	def count_by_user_id_type( cls, user_id, type ):
		count = cls.query( ndb.AND( cls.user_id == user_id, cls.type == type )).count()
		return count

	@classmethod
	def fetch_by_user_id_type( cls, user_id, type ):
		list = cls.query( ndb.AND( cls.user_id == user_id, cls.type == type )).order( -cls.time_created ).fetch()
		return list

	@classmethod	
	def fetch_keys_by_user_id_type( cls, user_id, type ):
		keys = cls.query( ndb.AND( cls.user_id == user_id, cls.type == type )).fetch( keys_only = True )
		return keys

	@classmethod	
	def fetch_keys_by_user_id_except_type( cls, user_id, type ):
		keys = cls.query( ndb.AND( cls.user_id == user_id, cls.type != type )).fetch( keys_only = True )
		return keys
	
	@classmethod
	def fetch_keys_by_email_type( cls, email, type ):
		keys = cls.query( ndb.AND( cls.email == email, cls.type == type )).fetch( keys_only = True )
		return keys

	@classmethod	
	def exist_by_token_type( cls, token, type ):
		count = cls.query( ndb.AND( cls.token == token, cls.type == type )).count( 1 )
		return count > 0

	@classmethod	
	def exist_by_user_id_token( cls, user_id, token ):
		count = cls.query( ndb.AND( cls.user_id == user_id, cls.token == token )).count( 1 )
		return count > 0

	@classmethod
	def delete_by_user_id_token( cls, user_id, token ):
		key = cls.query( ndb.AND( cls.user_id == user_id, cls.token == token )).fetch( keys_only = True )
		if key:
			key[ 0 ].delete()
			return True
		return False

	@classmethod
	def delete_token_by_id( cls, token_id ):
		ndb.Key( cls, int( token_id )).delete()

	@classmethod
	def fetch_old_tokens_by_types( cls, days_old, types ):
		list = cls.query( ndb.AND( cls.type.IN( types ) , cls.time_created <= ( datetime.datetime.now( ) - datetime.timedelta( days = days_old )))).fetch( keys_only = True )
		return list
