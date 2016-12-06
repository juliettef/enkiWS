from google.appengine.ext.ndb import model


class EnkiModelThread( model.Model ):

	author = model.IntegerProperty()
	title = model.StringProperty()

	forum = model.IntegerProperty()     # forum the thread belongs to

	num_posts = model.IntegerProperty( default = 0 )    # number of posts in the thread

	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )
