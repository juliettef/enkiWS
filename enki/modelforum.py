from google.appengine.ext.ndb import model


class EnkiModelForum( model.Model ):

	#=== MODEL ====================================================================

	title = model.StringProperty()
	description = model.StringProperty()
	group = model.StringProperty() # group of forums
	group_order = model.IntegerProperty( default = 0 ) # order the groups appear in on the page
	forum_order = model.IntegerProperty( default = 0 ) # order the forums appear in within a group

	num_threads = model.IntegerProperty( default = 0 )  # number of threads in the forum
	num_posts = model.IntegerProperty( default = 0 )    # number of posts in the forum's threads

	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )

	#=== QUERIES ==================================================================

	@classmethod
	def exist( cls ):
		count = cls.query().count( 1 )
		return count > 0

	@classmethod
	def fetch( cls ):
		return cls.query().order( cls.group_order, cls.forum_order ).fetch()
