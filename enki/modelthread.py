import collections

from google.appengine.ext.ndb import model

import enki.libutil

from enki.modeldisplayname import EnkiModelDisplayName
from enki.modelforum import EnkiModelForum


forumData = collections.namedtuple( 'forumData', 'forums_url, forum, num_posts, list, markdown_escaped_nofollow, forum_selected' )


class EnkiModelThread( model.Model ):

	#=== MODEL ====================================================================

	author = model.IntegerProperty()
	title = model.StringProperty()

	forum = model.IntegerProperty()     # forum the thread belongs to

	num_posts = model.IntegerProperty( default = 0 )    # number of posts in the thread

	sticky_order = model.IntegerProperty( default = 0 )  # admin can set sticky_order > 0 to get threads 'stuck'

	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )

	#=== CONSTANTS ================================================================

	THREAD_TITLE_LENGTH_MAX = 200

	#=== QUERIES ==================================================================

	@classmethod
	def fetch_by_forum( cls, forum ):
		return cls.query( cls.forum == forum ).order( -cls.sticky_order, -cls.time_updated ).fetch()

	#=== UTILITIES ================================================================

	@classmethod
	def get_forum_data( cls, forum_selected ):
		forums_url = enki.libutil.get_local_url( 'forums' )
		forum = EnkiModelForum.get_by_id( int( forum_selected ))
		num_posts = 0
		list = cls.fetch_by_forum( int( forum_selected ))
		if list:
			for i, item in enumerate(list):
				num_posts += item.num_posts
				url = enki.libutil.get_local_url('thread', { 'thread':str(item.key.id()) })
				item.url = url
				item.author_data = EnkiModelDisplayName.get_user_id_display_name_url(
					EnkiModelDisplayName.get_by_user_id_current(item.author))
				item.sticky = True if (item.sticky_order > 0) else False
				list[ i ] = item
		forum_data = forumData(forums_url, forum, num_posts, list, enki.libutil.markdown_escaped_nofollow, forum_selected)
		return forum_data

	@classmethod
	def validate_thread_pagination( cls, thread, post_requested, post_count ):
		result = enki.libutil.ENKILIB_ERROR
		if thread:
			if thread.isdigit():
				thread_entity = cls.get_by_id( int( thread ))
				if thread_entity:
					if post_requested and post_count:
						if post_requested.isdigit() and post_count.isdigit() :
							if int( post_requested ) > 0 and int( post_requested ) <= thread_entity.num_posts and int( post_count ) > 0:
								result = enki.libutil.ENKILIB_OK
						elif post_requested == 'last' and post_count.isdigit():
							result = enki.libutil.ENKILIB_OK
					elif post_requested == '' and post_count == '':
						result = enki.libutil.ENKILIB_OK
		return result
