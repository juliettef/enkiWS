from google.appengine.ext.ndb import model


class EnkiModelForum( model.Model ):

	title = model.StringProperty()
	description = model.StringProperty()
	group = model.StringProperty() # group of forums
	order = model.IntegerProperty( default = 0 ) # sort the forums (within a group)

	num_threads = model.IntegerProperty( default = 0 )  # number of threads in the forum
	num_posts = model.IntegerProperty( default = 0 )    # number of posts in the forum's threads

	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )
