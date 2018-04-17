import datetime
import time

from google.appengine.ext import ndb
from google.appengine.ext.ndb import model
from webapp2_extras import security


class EnkiModelTokenVerify( model.Model ):

	#=== MODEL ====================================================================

	token = model.StringProperty()
	email = model.StringProperty()
	user_id = model.IntegerProperty() # ndb user ID
	state = model.StringProperty() # store misc info
	time_created = model.DateTimeProperty( auto_now_add = True )
	type = model.StringProperty()

	#=== CONSTANTS ================================================================

	TIMEOUT_S = 0.1

	#=== QUERIES ==================================================================

	@classmethod
	def get_by_token( cls, token ):
		return cls.query( cls.token == token ).get()

	@classmethod
	def get_by_user_id_email_type( cls, user_id, email, type ):
		return cls.query( ndb.AND( cls.user_id == user_id, cls.email == email, cls.type == type )).get()

	@classmethod
	def get_by_user_id_state_type( cls, user_id, state, type ):
		return cls.query( ndb.AND( cls.user_id == user_id, cls.state == state, cls.type == type )).get()

	@classmethod
	def get_by_user_id_type( cls, user_id, type ):
		return cls.query( ndb.AND( cls.user_id == user_id, cls.type == type )).get( )

	@classmethod	
	def get_by_state_type( cls, state, type ):
		return cls.query( ndb.AND( cls.state == state, cls.type == type )).get()

	@classmethod
	def get_by_email_state_type( cls, email, state, type ):
		return cls.query( ndb.AND( cls.email == email, cls.state == state, cls.type == type )).get()

	@classmethod
	def count_by_user_id_type( cls, user_id, type ):
		return cls.query( ndb.AND( cls.user_id == user_id, cls.type == type )).count()

	@classmethod
	def fetch_by_user_id_type( cls, user_id, type ):
		return cls.query( ndb.AND( cls.user_id == user_id, cls.type == type )).order( -cls.time_created ).fetch()

	@classmethod	
	def fetch_keys_by_user_id_type( cls, user_id, type ):
		return cls.query( ndb.AND( cls.user_id == user_id, cls.type == type )).fetch( keys_only = True )

	@classmethod	
	def fetch_keys_by_user_id_except_type( cls, user_id, type ):
		return cls.query( ndb.AND( cls.user_id == user_id, cls.type != type )).fetch( keys_only = True )
	
	@classmethod
	def fetch_keys_by_email_type( cls, email, type ):
		return cls.query( ndb.AND( cls.email == email, cls.type == type )).fetch( keys_only = True )

	@classmethod	
	def exist_by_token_type( cls, token, type ):
		count = cls.query( ndb.AND( cls.token == token, cls.type == type )).count( 1 )
		return count > 0

	@classmethod	
	def exist_by_user_id_token( cls, user_id, token ):
		count = cls.query( ndb.AND( cls.user_id == user_id, cls.token == token )).count( 1 )
		return count > 0

	@classmethod
	def fetch_keys_old_tokens_by_types( cls, days_old, types ):
		return cls.query( ndb.AND( cls.type.IN( types ) , cls.time_created <= ( datetime.datetime.now( ) - datetime.timedelta( days = days_old )))).fetch( keys_only = True )

	#=== UTILITIES ================================================================

	@classmethod
	def get_by_token_type( cls, token, type, retry = 0 ):
		entity = cls.query(ndb.AND(cls.token == token, cls.type == type)).get()
		if retry and not entity:
			timeout = cls.TIMEOUT_S
			for i in range(retry):
				entity = cls.query(ndb.AND(cls.token == token, cls.type == type)).get()
				if entity:
					break
				else:
					time.sleep(timeout)
					timeout *= 2
		return entity

	@classmethod
	def delete_by_user_id_token( cls, user_id, token ):
		key = cls.query(ndb.AND(cls.user_id == user_id, cls.token == token)).fetch(keys_only = True)
		if key:
			key[ 0 ].delete()
			return True
		return False

	@classmethod
	def delete_token_by_id( cls, token_id ):
		ndb.Key(cls, int(token_id)).delete()

	@classmethod
	def delete_by_email_type( cls, email, type ):
	# delete all verify tokens for a given email and type (cleanup)
		entities = cls.fetch_keys_by_email_type(email, type)
		if entities:
			ndb.delete_multi(entities)

	@classmethod
	def add_preventmultipost_token( cls, type ):
	# prevent accidental multiple posting
		token = security.generate_random_string( entropy = 256 )
		pmtoken = cls( token = token, type = type )
		pmtoken.put()
		return token

	@classmethod
	def check_and_delete_preventmultipost_token( cls, token, type ):
	# prevent accidental multiple posting
		result = False
		verify_token = cls.get_by_token_type( token, type )
		if verify_token:
			verify_token.key.delete()
			result = True
		return result
