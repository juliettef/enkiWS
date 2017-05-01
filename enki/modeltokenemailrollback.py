from google.appengine.ext import ndb
from google.appengine.ext.ndb import model


class EnkiModelTokenEmailRollback( model.Model ):

	#=== MODEL ====================================================================

	token = model.StringProperty()
	email = model.StringProperty()
	user_id = model.IntegerProperty() # ndb user ID
	time_created = model.DateTimeProperty( auto_now_add = True )

	#=== QUERIES ==================================================================
	
	@classmethod
	def get_by_user_id_email( cls, user_id, email ):
		return cls.query( ndb.AND( cls.user_id == user_id, cls.email == email )).get()

	@classmethod
	def get_by_token( cls, token ):
		return cls.query( cls.token == token ).get()

	@classmethod
	def fetch_keys_by_user_id( cls, user_id ):
		return cls.query( cls.user_id == user_id ).fetch( keys_only = True )

	@classmethod
	def fetch_keys_by_user_id_time( cls, user_id, time_created ):
		return cls.query( ndb.AND( cls.time_created >= time_created, cls.user_id == user_id )).fetch( keys_only = True )
