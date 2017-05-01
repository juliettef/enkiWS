from google.appengine.ext.ndb import model


class EnkiModelTokenEmailRollback( model.Model ):

	#=== MODEL ====================================================================

	token = model.StringProperty()
	email = model.StringProperty()
	user_id = model.IntegerProperty() # ndb user ID
	time_created = model.DateTimeProperty( auto_now_add = True )
