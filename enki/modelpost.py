from google.appengine.ext.ndb import model


class EnkiModelPost( model.Model ):

	author = model.IntegerProperty()
	body = model.TextProperty()

	thread = model.IntegerProperty()    # thread the post belongs to

	sticky_order = model.IntegerProperty( default = 0 )  # admin can set sticky_order > 0 to get threads 'stuck'

	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )
