from google.appengine.ext.ndb import model


class EnkiModelRestAPIDataStore( model.Model ):

	user_id = model.IntegerProperty()
	app_id = model.StringProperty()
	data_type = model.StringProperty()
	data_id = model.StringProperty()
	data_payload = model.JsonProperty()
	time_expires = model.DateTimeProperty( auto_now_add = False )
	read_access = model.StringProperty( choices = [ 'private', 'friends', 'public' ], default = 'private' )
