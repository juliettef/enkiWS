from google.appengine.ext import ndb
from google.appengine.ext.ndb import model

from enki.modeltokenverify import EnkiModelTokenVerify


class EnkiModelRestAPITokenVerify( EnkiModelTokenVerify ):

	app_id = model.StringProperty()
	app_secret = model.StringProperty()

	@classmethod
	def get_by_user_id_token( cls, user_id, token ):
		entity = cls.query( ndb.AND( cls.user_id == user_id, cls.token == token )).get()
		return entity
