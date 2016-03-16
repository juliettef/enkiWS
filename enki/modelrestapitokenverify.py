from google.appengine.ext.ndb import model

from enki.modeltokenverify import EnkiModelTokenVerify


class EnkiModelRestAPITokenVerify( EnkiModelTokenVerify ):

	app_id = model.StringProperty()
