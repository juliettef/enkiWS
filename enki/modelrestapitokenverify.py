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

	@classmethod
	def exist_by_user_id_token_app_secret( cls, user_id, token, app_secret ):
		count = cls.query( ndb.AND( cls.user_id == user_id, cls.token == token, cls.app_secret == app_secret )).count( 1 )
		return count > 0
