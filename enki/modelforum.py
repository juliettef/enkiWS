from google.appengine.ext import ndb
from google.appengine.ext.ndb import model

import settings
import enki.libutil


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

	#=== UTILITIES ================================================================

	@classmethod
	def create_forums( cls ):
		# create an executable string from the forums settings to add the forums
		expression_forum = '''enki.modelforum.EnkiModelForum( group_order = {group_order}, forum_order = {forum_order}, group = "{group}", title = "{title}", description = "{description}" ), '''
		expression = "ndb.put_multi([ "
		increment = 10
		group_order = 0
		forum_order = 0
		current_group = ''
		for index, item in enumerate( settings.FORUMS ):
			if item[ 0 ] != current_group:
			# new group: increment the group order index and reset the forum order index
				current_group = item[ 0 ]
				group_order += increment
				forum_order = increment
			else:
				forum_order += increment
			expression += expression_forum.format( group_order = group_order, forum_order = forum_order, group = current_group, title = item[ 1 ], description = item[ 2 ] )
		expression += " ])"
		exec( expression )

	@classmethod
	def get_forums_data( cls ):
		forums_data = []
		forums_list = cls.fetch()
		if forums_list:
			# get the groups from the list (ordered)
			groups = []
			for forum in forums_list:
				if forum.group not in groups:
					groups.append( forum.group )
			# get the forums for each group (ordered)
			for group in groups:
				group_num_threads = 0
				group_num_posts = 0
				forums = []
				for forum in forums_list:
					if forum.group == group:
						group_num_threads += forum.num_threads
						group_num_posts += forum.num_posts
						url = enki.libutil.get_local_url( 'forum', { 'forum':str( forum.key.id())})
						forums.append({ 'title' : forum.title, 'description' : forum.description, 'time_updated' : forum.time_updated,
										'num_threads' : forum.num_threads, 'num_posts' : forum.num_posts, 'url' : url })
				forums_data.append({ 'name' : group, 'num_threads' : group_num_threads,
									 'num_posts' : group_num_posts, 'forums' : forums })
		return forums_data

