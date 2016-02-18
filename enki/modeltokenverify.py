from google.appengine.ext import ndb
from google.appengine.ext.ndb import model


class EnkiModelTokenVerify( model.Model ):

	token = model.StringProperty()
	email = model.StringProperty()
	user_id = model.IntegerProperty() # ndb user ID
	time_created = model.DateTimeProperty( auto_now_add = True )
	type = model.StringProperty()
	auth_ids_provider = model.StringProperty() # store auth Id info for registration

	@classmethod
	def get_VerifyToken( cls, token ):
		entity = cls.query( cls.token == token ).get()
		return entity

	@classmethod
	def get_VerifyToken_by_user_id_email_type( cls, user_id, email, type ):
		entity = cls.query( ndb.AND( cls.user_id == user_id, cls.email == email, cls.type == type )).get()
		return entity

	@classmethod
	def get_VerifyToken_by_token_type( cls, token, type ):
		entity = cls.query( ndb.AND( cls.token == token, cls.type == type )).get()
		return entity

	@classmethod	
	def get_VerifyToken_by_authid_type( cls, authId, type ):
		entity = cls.query( ndb.AND( cls.auth_ids_provider == authId, cls.type == type )).get()
		return entity

	@classmethod	
	def fetch_keys_VerifyToken_by_user_id_type( cls, user_id, type ):
		keys = cls.query( ndb.AND( cls.user_id == user_id, cls.type == type )).fetch( keys_only = True )
		return keys

	@classmethod	
	def fetch_keys_VerifyToken_by_user_id_except_type( cls, user_id, type ):
		keys = cls.query( ndb.AND( cls.user_id == user_id, cls.type != type )).fetch( keys_only = True )
		return keys
	
	@classmethod
	def fetch_keys_VerifyToken_by_email_type( cls, email, type ):
		keys = cls.query( ndb.AND( cls.email == email, cls.type == type )).fetch( keys_only = True )
		return keys

	@classmethod	
	def exist_VerifyToken( cls, token, type ):
		count = cls.query( ndb.AND( cls.token == token, cls.type == type )).count( 1 )
		return count > 0

	@classmethod	
	def exist_VerifyToken_by_user_id_token( cls, user_id, token ):
		count = cls.query( ndb.AND( cls.user_id == user_id, cls.token == token )).count( 1 )
		return count > 0
