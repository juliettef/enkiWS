from google.appengine.ext import ndb
from google.appengine.ext.ndb import model


class EnkiModelApp( model.Model ):

	user_id = model.IntegerProperty()
	name = model.StringProperty()
	secret = model.StringProperty()
	time_created = model.DateTimeProperty( auto_now_add = True )

	@classmethod
	def exist_by_name( cls, name ):
		count = cls.query( cls.name == name ).count( 1 )
		return count > 0

	@classmethod
	def count_by_user_id( cls, user_id ):
		return cls.query( cls.user_id == user_id ).count()

	@classmethod
	def fetch_by_user_id( cls, user_id ):
		list = cls.query( cls.user_id == user_id ).order( cls.time_created ).fetch()
		return list

	@classmethod
	def exist_by_app_id_app_secret( cls, app_id, app_secret ):
		item = ndb.Key( cls, int( app_id )).get()
		if item and item.secret == app_secret:
			return True
		return False
