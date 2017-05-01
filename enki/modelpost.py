import collections

from google.appengine.ext import ndb
from google.appengine.ext.ndb import model

import enki.libutil

from enki.modeldisplayname import EnkiModelDisplayName
from enki.modelforum import EnkiModelForum
from enki.modelthread import EnkiModelThread


threadData = collections.namedtuple( 'threadData', 'forums_url, forum, forum_url, thread, thread_url, list, markdown_escaped_nofollow, thread_selected' )
postData = collections.namedtuple( 'postData', 'forums_url, forum, forum_url, thread, thread_url, post, sticky, post_page, author_data, markdown_escaped_nofollow' )
authorpostsData = collections.namedtuple( 'authorpostsData', 'forums_url, author_data, list, markdown_escaped_nofollow' )
pagination = collections.namedtuple( 'pagination', 'page_first, page_previous, page_current, page_list, page_next, page_last' )


class EnkiModelPost( model.Model ):
	
	#=== MODEL ====================================================================
	
	author = model.IntegerProperty()
	body = model.TextProperty()

	thread = model.IntegerProperty()    # thread the post belongs to

	sticky_order = model.IntegerProperty( default = 0 )  # admin can set sticky_order > 0 to get threads 'stuck'

	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )

	#=== CONSTANTS ================================================================

	POST_LENGTH_MAX = 10000
	POST_DELETED = '[deleted]'
	POSTS_PER_PAGE = 10
	POST_DEFAULT = 1
	POST_LAST = 'last'
	PAGES_BEFORE = 3
	PAGES_AFTER = 3

	ERROR_POST_LENGTH = -51
	ERROR_POST_CREATION = -52
	ERROR_POST_EDITION = -53
	ERROR_POST_DELETION = -54

	#=== QUERIES ==================================================================

	@classmethod
	def fetch_by_thread( cls, thread, limit, offset ):
		return cls.query( cls.thread == thread ).order( -cls.sticky_order, cls.time_created ).fetch( limit = limit, offset = offset )

	@classmethod
	def fetch_by_author( cls, author ):
		return cls.query( cls.author == author ).order( -cls.time_created ).fetch()

	@classmethod
	def fetch_keys_by_author( cls, author ):
		return cls.query( cls.author == author ).fetch( keys_only = True )

	#=== UTILITIES ================================================================

	#--- DISPLAY DATA -------------------------------------------------------------

	@classmethod
	def get_thread_data( cls, thread_selected, post_requested = POST_DEFAULT, post_count = POSTS_PER_PAGE ):
		# get posts by thread
		forums_url = enki.libutil.get_local_url( 'forums' )
		thread = EnkiModelThread.get_by_id( int( thread_selected ))
		thread_url = enki.libutil.get_local_url( 'thread', { 'thread': str( thread_selected )})
		forum = EnkiModelForum.get_by_id( thread.forum )
		forum_url = enki.libutil.get_local_url( 'forum', { 'forum': str( forum.key.id())})
		if post_requested == cls.POST_LAST:
			post_requested = thread.num_posts
		list = cls.fetch_by_thread( int( thread_selected ), offset = (int( post_requested ) - 1), limit = int( post_count ))
		if list:
			for i, item in enumerate( list ):
				item.author_data = EnkiModelDisplayName.get_user_id_display_name_url( EnkiModelDisplayName.get_by_user_id_current( item.author ))
				item.post_page = enki.libutil.get_local_url( 'post', { 'post': str( item.key.id())})
				item.sticky = True if ( item.sticky_order > 0 ) else False
				list[ i ] = item
		thread_data = threadData( forums_url, forum, forum_url, thread, thread_url, list, enki.libutil.markdown_escaped_nofollow, thread_selected )
		return thread_data

	@classmethod
	def get_post_data( cls, post_selected ):
		# get a post
		forums_url = enki.libutil.get_local_url( 'forums' )
		post = cls.get_by_id( int( post_selected ))
		sticky = True if ( post.sticky_order > 0 ) else False
		post_page = enki.libutil.get_local_url('post', { 'post':str( post.key.id())})
		thread = EnkiModelThread.get_by_id( post.thread )
		thread_url = enki.libutil.get_local_url('thread', { 'thread':str( thread.key.id())})
		forum = EnkiModelForum.get_by_id( thread.forum )
		forum_url = enki.libutil.get_local_url('forum', { 'forum':str( forum.key.id())})
		author_data = EnkiModelDisplayName.get_user_id_display_name_url( EnkiModelDisplayName.get_by_user_id_current( post.author ))
		post_data = postData( forums_url, forum, forum_url, thread, thread_url, post, sticky, post_page, author_data, enki.libutil.markdown_escaped_nofollow, )
		return post_data

	@classmethod
	def get_author_posts( cls, author_selected ):
		# get posts by author to display on their profile. If the author hasn't set a display name, return nothing
		author_display_name = EnkiModelDisplayName.get_by_user_id_current( int( author_selected ))
		if author_display_name:
			forums_url = enki.libutil.get_local_url( 'forums' )
			author_data = EnkiModelDisplayName.get_user_id_display_name_url( author_display_name )
			list = cls.fetch_by_author( int( author_selected ))
			if list:
				for i, item in enumerate( list ):
					thread = EnkiModelThread.get_by_id( item.thread )
					forum = EnkiModelForum.get_by_id( thread.forum )
					item.thread_title = thread.title
					item.thread_url = enki.libutil.get_local_url( 'thread', { 'thread':str( item.thread) })
					item.forum_title = forum.title
					item.forum_group = forum.group
					item.forum_url = enki.libutil.get_local_url( 'forum', { 'forum':str( forum.key.id()) })
					item.post_page = enki.libutil.get_local_url( 'post', { 'post':str( item.key.id()) })
					item.sticky = True if ( item.sticky_order > 0 ) else False
					list[ i ] = item
			author_posts_data = authorpostsData( forums_url, author_data, list, enki.libutil.markdown_escaped_nofollow )
			return author_posts_data

	@classmethod
	def get_page( cls, thread, post_requested, post_count ):
		if post_requested == cls.POST_LAST:
			post_requested = thread.num_posts
		page = 1
		if post_count == 1:
			page = post_requested
		elif post_count > 1 and post_count <= thread.num_posts:
			mod_req_post = post_requested % post_count
			if mod_req_post == 0:
				page = ( post_requested - mod_req_post + 1 - post_count ) / post_count + 1
			else:
				page = ( post_requested - mod_req_post + 1 ) / post_count + 1
		return page

	@classmethod
	def get_first_post_on_page( cls, page, post_count ):
		post = ( page - 1 ) * post_count + 1
		return post

	@classmethod
	def get_thread_pagination_data( cls, thread_selected, post_requested = POST_DEFAULT,
									post_count = POSTS_PER_PAGE ):
		thread = EnkiModelThread.get_by_id(int(thread_selected))
		post_requested = thread.num_posts if post_requested == cls.POST_LAST else int(post_requested)
		post_count = int(post_count)
		page_first = ''
		page_previous = ''
		page_current = [ ]
		page_next = ''
		page_last = ''
		page_list = [ ]

		# first page
		first_post_first_page = 1
		if post_requested <> 1:
			page_first = enki.libutil.get_local_url('thread',
													{ 'thread':thread_selected, 'start':str(first_post_first_page),
													  'count':str(post_count) })

		# last page
		first_post_last_page = cls.get_first_post_on_page( cls.get_page( thread, thread.num_posts, post_count ), post_count )
		if post_requested + post_count <= thread.num_posts:
			page_last = enki.libutil.get_local_url('thread',
												   { 'thread':thread_selected, 'start':str(first_post_last_page ),
													 'count':str( post_count )})

		# current, previous and next pages
		first_post_previous_page = cls.get_first_post_on_page( cls.get_page( thread, post_requested, post_count ), post_count )
		first_post_next_page = cls.get_first_post_on_page( cls.get_page( thread, ( post_requested + post_count ), post_count ),
													  post_count)
		if cls.get_first_post_on_page( cls.get_page( thread, post_requested, post_count ), post_count ) == post_requested:
			page = enki.libutil.get_local_url( 'thread', { 'thread':thread_selected, 'start':str( post_requested ),
														  'count':str( post_count )})
			page_current = [ page, cls.get_page( thread, post_requested, post_count )]
			if page_current[ 1 ] > first_post_first_page:
				first_post_previous_page = cls.get_first_post_on_page( page_current[ 1 ] - 1, post_count )
			if page_current[ 1 ] < cls.get_page( thread, thread.num_posts, post_count ):
				first_post_next_page = cls.get_first_post_on_page( page_current[ 1 ] + 1, post_count )
		if page_first:
			page_previous = enki.libutil.get_local_url('thread', { 'thread':thread_selected,
																   'start':str( first_post_previous_page ),
																   'count':str( post_count )})
		if page_last:
			page_next = enki.libutil.get_local_url('thread', { 'thread':thread_selected, 'start':str(first_post_next_page),
													 'count':str( post_count )})

		# list of posts
		start = cls.get_page( thread, post_requested, post_count ) - cls.PAGES_BEFORE
		while start < 1:
			start += 1
		stop = cls.get_page( thread, post_requested, post_count ) + cls.PAGES_AFTER
		while stop > cls.get_page( thread, thread.num_posts, post_count ):
			stop -= 1
		index = start
		while index <= stop:
			first_post = cls.get_first_post_on_page( index, post_count )
			page = enki.libutil.get_local_url( 'thread', { 'thread':thread_selected, 'start':str( first_post ),
														  'count':str( post_count )})
			page_list.append([ page, index ])
			index += 1

		result = pagination( page_first, page_previous, page_current, page_list, page_next, page_last )
		return result

	#--- ADD DATA -----------------------------------------------------------------

	@classmethod
	def add_thread_and_post( cls, user_id, forum, thread_title, thread_sticky_order, post_body, post_sticky_order ):
		result = enki.libutil.ENKILIB_OK
		if user_id and forum and thread_title and post_body:
			if len( thread_title ) <= EnkiModelThread.THREAD_TITLE_LENGTH_MAX and len( post_body ) <= cls.POST_LENGTH_MAX:
				if EnkiModelDisplayName.get_by_user_id_current( user_id ):
					thread = EnkiModelThread( author = user_id, forum = int( forum ), title = thread_title, num_posts = 1, sticky_order = int( thread_sticky_order ) )
					thread.put()
					post = cls( author = user_id, body = post_body, thread = thread.key.id(), sticky_order = int( post_sticky_order ))
					post.put()
					forum_selected = ndb.Key( EnkiModelForum, int( forum )).get()
					forum_selected.num_posts += 1
					forum_selected.num_threads += 1
					forum_selected.put()
				else:
					result = cls.ERROR_POST_CREATION
			else:
				result = cls.ERROR_POST_LENGTH
		else:
			result = cls.ERROR_POST_CREATION
		return result

	@classmethod
	def add_post( cls, user_id, thread, post_body, sticky_order ):
		result = enki.libutil.ENKILIB_OK
		if user_id and thread and post_body:
			if len( post_body ) <= cls.POST_LENGTH_MAX:
				post = cls( author = user_id, thread = int( thread ), body = post_body, sticky_order = int( sticky_order ))
				post.put()
				thread_selected = ndb.Key( EnkiModelThread, int( thread )).get()
				thread_selected.num_posts += 1
				thread_selected.put()
				forum_selected = ndb.Key( EnkiModelForum, thread_selected.forum ).get()
				forum_selected.num_posts += 1
				forum_selected.put()
			else:
				result = cls.ERROR_POST_LENGTH
		else:
			result = cls.ERROR_POST_CREATION
		return result

	@classmethod
	def edit_post( cls, user_id, post_id, post_body, sticky_order ):
		thread = ''
		result = enki.libutil.ENKILIB_OK
		if user_id and post_id and post_body:
			if len( post_body ) <= cls.POST_LENGTH_MAX:
				post = cls.get_by_id( int( post_id ))
				if post:
					post.body = post_body
					post.sticky_order = int( sticky_order )
					thread = str( post.thread )
				post.put()
			else:
				result = cls.ERROR_POST_LENGTH
		else:
			result = cls.ERROR_POST_EDITION
		return result, thread

	@classmethod
	def delete_post( cls, user_id, post_id ):
		thread = ''
		result = enki.libutil.ENKILIB_OK
		if user_id and post_id:
			post = cls.get_by_id( int( post_id ))
			if post:
				post.body = cls.POST_DELETED
				thread = str( post.thread )
			post.put()
		else:
			result = cls.ERROR_POST_DELETION
		return result, thread

	@classmethod
	def delete_user_posts( cls, user_id ):
		result = enki.libutil.ENKILIB_OK
		posts = cls.fetch_keys_by_author(user_id)
		if posts:
			for post in posts:
				result = cls.delete_post( user_id, post.id())
				if result == cls.ERROR_POST_DELETION:
					return result
		return result

