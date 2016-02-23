from google.appengine.ext.ndb import model


class EnkiModelRestAPIConnectToken( model.Model ):

	token = model.StringProperty()
	display_name = model.StringProperty()
	user_id = model.IntegerProperty()
	time_created = model.DateTimeProperty( auto_now_add = True )
