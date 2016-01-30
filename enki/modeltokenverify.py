from google.appengine.ext.ndb import model


class EnkiModelTokenVerify( model.Model ):

	token = model.StringProperty()
	email = model.StringProperty()
	user_id = model.IntegerProperty() # ndb user ID
	time_created = model.DateTimeProperty( auto_now_add = True )
	type = model.StringProperty( choices = [ 'register',
	                                         'passwordchange',
	                                         'emailchange',
	                                         'accountdelete',
	                                         'accountandpostsdelete',
	                                         'preventmultipost',
	                                         'purchasebyuser',
	                                         ] )
	auth_ids_provider = model.StringProperty() # store auth Id info for registration
