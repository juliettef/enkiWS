from google.appengine.ext.ndb import model


class EnkiModelRestAPIDataStore( model.Model ):

	user_id = model.IntegerProperty()
	app_id = model.StringProperty()
	data_key = model.StringProperty()
	data_json = model.JsonProperty()
	time_updated = model.DateTimeProperty( auto_now = True )
