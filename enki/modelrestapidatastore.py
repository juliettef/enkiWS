import datetime
import random

from google.appengine.ext import ndb
from google.appengine.ext.ndb import model


class EnkiModelRestAPIDataStore( model.Model ):

	#=== MODEL ====================================================================

	user_id = model.IntegerProperty()
	app_id = model.StringProperty()
	data_type = model.StringProperty()
	data_id = model.StringProperty()
	data_payload = model.JsonProperty()
	time_expires = model.DateTimeProperty( auto_now_add = False )
	read_access = model.StringProperty( choices = [ 'private', 'friends', 'public' ], default = 'private' )

	#=== CONSTANTS ================================================================

	DATASTORE_EXPIRY_DEFAULT = 86400    # 24h
	DATASTORE_NON_EXPIRING = 3154000000 # 100 years
	DATASTORE_NON_EXPIRING_REFRESH = DATASTORE_NON_EXPIRING / 2

	#=== QUERIES ==================================================================

	@classmethod
	def get_by_user_id_app_id_data_type_data_id( cls, user_id, app_id, data_type, data_id ):
		return cls.query( ndb.AND( cls.user_id == user_id, cls.app_id == app_id,
								   cls.data_type == data_type, cls.data_id == data_id )).get()

	@classmethod
	def get_by_user_id_app_id_data_type_data_id_not_expired( cls, user_id, app_id, data_type, data_id ):
		return cls.query( ndb.AND( cls.user_id == user_id, cls.app_id == app_id,
								   cls.data_type == data_type, cls.data_id == data_id,
								   cls.time_expires > datetime.datetime.now())).get()

	@classmethod
	def fetch_by_user_id( cls, user_id ):
		return cls.query( cls.user_id == user_id ).order( cls.app_id, cls.data_type, cls.data_id, cls.time_expires ).fetch()

	@classmethod
	def fetch_by_user_id_app_id( cls, user_id, app_id ):
		return cls.query( ndb.AND( cls.user_id == user_id,
														 cls.app_id == app_id )).fetch( keys_only = True )

	@classmethod
	def fetch_by_user_id_app_id_data_type_read_access_not_expired( cls, user_id, app_id, data_type, read_access ):
		return cls.query( ndb.AND( cls.user_id == user_id,
														   cls.app_id == app_id,
														   cls.data_type == data_type,
														   cls.read_access == read_access,
														   cls.time_expires > datetime.datetime.now())).fetch()

	@classmethod
	def fetch_by_app_id_data_type_read_access_not_expired( cls, app_id, data_type, read_access ):
		return cls.query( ndb.AND( cls.app_id == app_id,
														 cls.data_type == data_type,
														 cls.read_access == read_access,
														 cls.time_expires > datetime.datetime.now())).fetch()

	@classmethod
	def fetch_by_user_id_app_id_data_type_data_id( cls, user_id, app_id, data_type, data_id ):
		return cls.query( ndb.AND( cls.user_id == user_id,
														 cls.app_id == app_id,
														 cls.data_type == data_type,
														 cls.data_id == data_id )).fetch( keys_only = True )

	@classmethod
	def fetch_expired( cls ):
		return cls.query( cls.time_expires < datetime.datetime.now()).fetch( keys_only = True )

	@classmethod
	def fetch_non_expiring( cls ):
		return cls.query( cls.time_expires > ( datetime.datetime.now() + datetime.timedelta( seconds = cls.DATASTORE_NON_EXPIRING_REFRESH ))).fetch()

	#=== UTILITIES ================================================================

	@classmethod
	def refresh_non_expiring( cls ):
		likelihood = 10 # occurs with a probability of 1%
		number = random.randint( 1, 1000 )
		if number < likelihood:
			list = cls.fetch_non_expiring()
			for item in list:
				item.time_expires = datetime.datetime.now() + datetime.timedelta( seconds = cls.DATASTORE_NON_EXPIRING )
			ndb.put_multi_async( list )

	@classmethod
	def delete_user_app_data( cls, user_id, app_id ):
		keys = cls.fetch_by_user_id_app_id( user_id, app_id )
		ndb.delete_multi( keys )
