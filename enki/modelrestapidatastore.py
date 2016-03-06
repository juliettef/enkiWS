from google.appengine.ext.ndb import model


class EnkiModelRestAPIDataStore( model.Model ):

	user_id = model.IntegerProperty()
	app_id = model.StringProperty()
	data_key = model.StringProperty()
	data_payload = model.JsonProperty()
	read_access = model.StringProperty( choices = [ 'private', 'friends', 'public' ], default = 'private' )
	time_updated = model.DateTimeProperty( auto_now = True )
