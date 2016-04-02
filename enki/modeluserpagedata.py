from google.appengine.ext.ndb import model
from google.appengine.ext import ndb


class EnkiModelUserPageData( model.Model ):

	user_id = model.IntegerProperty()
	route = model.StringProperty()
	data = model.PickleProperty( )

	@classmethod
	def get_by_user_id_route( cls, user_id, route ):
		entity = cls.query( ndb.AND( cls.user_id == user_id, cls.route == route )).get()
		return entity
