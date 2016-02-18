import collections

from google.appengine.ext import ndb
from webapp2_extras import security
from markdown2 import markdown2

import settings
import enki.libdisplayname
import enki.libuser
import enki.libutil
from enki.modeltokenverify import EnkiModelTokenVerify
from enki.modelforum import EnkiModelForum
from enki.modelpost import EnkiModelPost
from enki.modelthread import EnkiModelThread


POST_LENGTH_MAX = 10000
THREAD_TITLE_LENGTH_MAX = 200
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

forumsData = collections.namedtuple( 'forumsData', 'num_threads, num_posts, list')
forumData = collections.namedtuple( 'forumData', 'forums_url, forum, num_posts, list, markdown, forum_selected')
threadData = collections.namedtuple( 'threadData', 'forums_url, forum, forum_url, thread, thread_url, list, markdown, thread_selected')
postData = collections.namedtuple( 'postData', 'forums_url, forum, forum_url, thread, thread_url, post, post_page, author_data, markdown' )
authorpostsData = collections.namedtuple( 'authorpostsData', 'forums_url, author_data, list, markdown' )
pagination = collections.namedtuple( 'pagination', 'page_first, page_previous, page_current, page_list, page_next, page_last' )


#=== DISPLAY DATA =============================================================


def set_forum():
	ndb.put_multi( settings.get_forum_default_topics())


def get_forums_data( group ):
	num_threads = 0
	num_posts = 0
	list = fetch_EnkiForum_by_group( group )
	if list:
		for i, item in enumerate( list ):
			num_threads += item.num_threads
			num_posts += item.num_posts
			url = enki.libutil.get_local_url( 'forum', { 'forum': str( item.key.id( ) ) } )
			item.url = url
			list[ i ] = item
	forums_data = forumsData( num_threads, num_posts, list )
	return forums_data


def get_forum_data( forum_selected ):
	forums_url = enki.libutil.get_local_url( 'forums' )
	forum = EnkiModelForum.get_by_id( int( forum_selected ))
	num_posts = 0
	list = fetch_EnkiThread_by_forum( int( forum_selected ))
	if list:
		for i, item in enumerate( list ):
			num_posts += item.num_posts
			url = enki.libutil.get_local_url( 'thread', { 'thread': str( item.key.id( ) ) } )
			item.url = url
			item.author_data = enki.libdisplayname.get_user_id_display_name_url( enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( item.author ) )
			list[ i ] = item
	forum_data = forumData( forums_url, forum, num_posts, list, markdown2.markdown, forum_selected )
	return forum_data


def validate_thread_pagination( thread, post_requested, post_count ):
	result = enki.libutil.ENKILIB_ERROR
	if thread:
		if thread.isdigit():
			thread_entity = EnkiModelThread.get_by_id( int( thread ))
			if thread_entity:
				if post_requested and post_count:
					if post_requested.isdigit( ) and post_count.isdigit( ) :
						if int( post_requested ) > 0 and int( post_requested ) <= thread_entity.num_posts and int( post_count ) > 0:
							result = enki.libutil.ENKILIB_OK
					elif post_requested == 'last' and post_count.isdigit( ):
						result = enki.libutil.ENKILIB_OK
				elif post_requested == '' and post_count == '':
					result = enki.libutil.ENKILIB_OK
	return result


def get_thread_data( thread_selected, post_requested = POST_DEFAULT, post_count = POSTS_PER_PAGE ):
	# get posts by thread
	forums_url = enki.libutil.get_local_url( 'forums' )
	thread = EnkiModelThread.get_by_id( int( thread_selected ))
	thread_url = enki.libutil.get_local_url( 'thread', { 'thread': str( thread_selected ) } )
	forum = EnkiModelForum.get_by_id( thread.forum )
	forum_url = enki.libutil.get_local_url( 'forum', { 'forum': str( forum.key.id( ) ) } )
	if post_requested == POST_LAST:
		post_requested = thread.num_posts
	list = fetch_EnkiPost_by_thread( int( thread_selected ), offset = (int( post_requested ) - 1), limit = int( post_count ) )
	if list:
		for i, item in enumerate( list ):
			item.author_data = enki.libdisplayname.get_user_id_display_name_url( enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( item.author ) )
			item.post_page = enki.libutil.get_local_url( 'post', { 'post': str( item.key.id( ) ) } )
			list[ i ] = item
	thread_data = threadData( forums_url, forum, forum_url, thread, thread_url, list, markdown2.markdown, thread_selected )
	return thread_data


def get_page( thread, post_requested, post_count ):
	if post_requested == POST_LAST:
		post_requested = thread.num_posts
	page = 1
	if post_count == 1:
		page = post_requested
	elif post_count > 1 and post_count <= thread.num_posts:
		mod_req_post = post_requested % post_count
		if mod_req_post == 0:
			page = (post_requested - mod_req_post + 1 - post_count) / post_count + 1
		else:
			page = (post_requested - mod_req_post + 1) / post_count + 1
	return page


def get_first_post_on_page( page, post_count ):
	post = (page - 1) * post_count + 1
	return post


def get_thread_pagination_data( thread_selected, post_requested = POST_DEFAULT, post_count = POSTS_PER_PAGE ):
	thread = EnkiModelThread.get_by_id( int( thread_selected ))
	post_requested = thread.num_posts if post_requested == POST_LAST else int( post_requested )
	post_count = int( post_count )
	page_first = ''
	page_previous = ''
	page_current = []
	page_next = ''
	page_last = ''
	page_list = []


	# first page
	first_post_first_page = 1
	if post_requested <> 1:
		page_first = enki.libutil.get_local_url( 'thread', { 'thread': thread_selected, 'start': str( first_post_first_page ), 'count': str( post_count ) } )

	# last page
	first_post_last_page = get_first_post_on_page( get_page( thread, thread.num_posts, post_count ), post_count)
	if post_requested + post_count <= thread.num_posts:
		page_last = enki.libutil.get_local_url( 'thread', { 'thread': thread_selected, 'start': str( first_post_last_page ), 'count': str( post_count ) } )

	# current, previous and next pages
	first_post_previous_page = get_first_post_on_page( get_page( thread, post_requested, post_count ), post_count )
	first_post_next_page = get_first_post_on_page( get_page( thread, ( post_requested + post_count ), post_count ), post_count )
	if get_first_post_on_page( get_page( thread, post_requested, post_count ), post_count ) == post_requested:
		page = enki.libutil.get_local_url( 'thread', { 'thread': thread_selected, 'start': str( post_requested ), 'count': str( post_count ) } )
		page_current = [ page, get_page( thread, post_requested, post_count )]
		if page_current[ 1 ] > first_post_first_page:
			first_post_previous_page = get_first_post_on_page( page_current[ 1 ] - 1, post_count )
		if page_current[ 1 ] < get_page( thread, thread.num_posts, post_count ):
			first_post_next_page = get_first_post_on_page( page_current[ 1 ] + 1, post_count )
	if page_first:
		page_previous = enki.libutil.get_local_url( 'thread', { 'thread': thread_selected, 'start': str( first_post_previous_page ), 'count': str( post_count ) } )
	if page_last:
		page_next = enki.libutil.get_local_url( 'thread', { 'thread': thread_selected, 'start': str( first_post_next_page ), 'count': str( post_count ) } )

	# list of posts
	start = get_page( thread, post_requested, post_count ) - PAGES_BEFORE
	while start < 1:
		start += 1
	stop = get_page( thread, post_requested, post_count ) + PAGES_AFTER
	while stop > get_page( thread, thread.num_posts, post_count ):
		stop -= 1
	index = start
	while index <= stop :
		first_post = get_first_post_on_page( index, post_count )
		page = enki.libutil.get_local_url( 'thread', { 'thread': thread_selected, 'start': str( first_post ), 'count': str( post_count ) } )
		page_list.append([ page, index ])
		index += 1

	result = pagination( page_first, page_previous, page_current, page_list, page_next, page_last )
	return result


def	get_post_data ( post_selected ):
	# get a post
	forums_url = enki.libutil.get_local_url( 'forums' )
	post = EnkiModelPost.get_by_id( int( post_selected ))
	post_page =  enki.libutil.get_local_url( 'post', { 'post': str( post.key.id( ) ) } )
	thread = EnkiModelThread.get_by_id( post.thread )
	thread_url = enki.libutil.get_local_url( 'thread', { 'thread': str( thread.key.id( ) ) } )
	forum = EnkiModelForum.get_by_id( thread.forum )
	forum_url = enki.libutil.get_local_url( 'forum', { 'forum': str( forum.key.id( ) ) } )
	author_data = enki.libdisplayname.get_user_id_display_name_url( enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( post.author ) )
	post_data = postData( forums_url, forum, forum_url, thread, thread_url, post, post_page, author_data, markdown2.markdown, )
	return post_data


def get_author_posts( author_selected ):  # MOVED TO LIB
	# get posts by author to display on their profile. If the author hasn't set a display name, return nothing
	author_display_name = enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( int( author_selected ) )
	if author_display_name:
		forums_url = enki.libutil.get_local_url( 'forums' )
		author_data = enki.libdisplayname.get_user_id_display_name_url( author_display_name )
		list = fetch_EnkiPost_by_author( int( author_selected ))
		if list:
			for i, item in enumerate( list ):
				thread = EnkiModelThread.get_by_id( item.thread )
				forum = EnkiModelForum.get_by_id( thread.forum )
				item.thread_title = thread.title
				item.thread_url = enki.libutil.get_local_url( 'thread', { 'thread': str( item.thread ) } )
				item.forum_title = forum.title
				item.forum_group = forum.group
				item.forum_url = enki.libutil.get_local_url( 'forum', { 'forum': str( forum.key.id( ) ) } )
				item.post_page = enki.libutil.get_local_url( 'post', { 'post': str( item.key.id( ) ) } )
				list[ i ] = item
		author_posts_data = authorpostsData( forums_url, author_data, list, markdown2.markdown )
		return author_posts_data


#=== ADD DATA =================================================================


def add_preventmultipost_token():
	# prevent accidental multiple posting
	token = security.generate_random_string( entropy = 256 )
	pmtoken = EnkiModelTokenVerify( token = token, type = 'preventmultipost' )
	pmtoken.put()
	return token


def check_and_delete_preventmultipost_token( token ):
	# prevent accidental multiple posting
	result = False
	verify_token = EnkiModelTokenVerify.get_VerifyToken_by_token_type( token, 'preventmultipost' )
	if verify_token:
		verify_token.key.delete()
		result = True
	return result


def add_thread_and_post( user_id, forum, thread_title, post_body ):
	result = enki.libutil.ENKILIB_OK
	if user_id and forum and thread_title and post_body:
		if len( thread_title ) <= THREAD_TITLE_LENGTH_MAX and len( post_body ) <= POST_LENGTH_MAX:
			if enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( user_id ):
				thread = EnkiModelThread( author = user_id, forum = int( forum ), title = thread_title, num_posts = 1 )
				thread.put()
				post = EnkiModelPost( author = user_id, body = post_body, thread = thread.key.id())
				post.put()
				forum_selected = ndb.Key( EnkiModelForum, int( forum )).get()
				forum_selected.num_posts += 1
				forum_selected.num_threads += 1
				forum_selected.put()
			else:
				result = ERROR_POST_CREATION
		else:
			result = ERROR_POST_LENGTH
	else:
		result = ERROR_POST_CREATION
	return result


def add_post( user_id, thread, post_body ):
	result = enki.libutil.ENKILIB_OK
	if user_id and thread and post_body:
		if len( post_body ) <= POST_LENGTH_MAX:
			post = EnkiModelPost( author = user_id, thread = int( thread ), body = post_body )
			post.put()
			thread_selected = ndb.Key( EnkiModelThread, int( thread )).get()
			thread_selected.num_posts += 1
			thread_selected.put()
			forum_selected = ndb.Key( EnkiModelForum, thread_selected.forum ).get()
			forum_selected.num_posts += 1
			forum_selected.put()
		else:
			result = ERROR_POST_LENGTH
	else:
		result = ERROR_POST_CREATION
	return result


def edit_post( user_id, post_id, post_body ):
	thread = ''
	result = enki.libutil.ENKILIB_OK
	if user_id and post_id and post_body:
		if len( post_body ) <= POST_LENGTH_MAX:
			post = EnkiModelPost.get_by_id( int( post_id ))
			if post:
				post.body = post_body
				thread = str( post.thread )
			post.put()
		else:
			result = ERROR_POST_LENGTH
	else:
		result = ERROR_POST_EDITION
	return result, thread


def delete_post( user_id, post_id ):
	thread = ''
	result = enki.libutil.ENKILIB_OK
	if user_id and post_id:
		post = EnkiModelPost.get_by_id( int( post_id ))
		if post:
			post.body = POST_DELETED
			thread = str( post.thread )
		post.put()
	else:
		result = ERROR_POST_DELETION
	return result, thread


def delete_user_posts( user_id ):
	result = enki.libutil.ENKILIB_OK
	posts = fetch_EnkiPost_key_by_author( user_id )
	if posts:
		for post in posts:
			result = delete_post( user_id, post.id( ) )
			if result == ERROR_POST_DELETION:
				return result
	return result


#=== QUERIES ==================================================================


def exist_EnkiForums():
	count = EnkiModelForum.query().count( 1 )
	return count > 0


def fetch_EnkiForum_by_group( group ):
	list = EnkiModelForum.query( EnkiModelForum.group == group ).order( EnkiModelForum.order ).fetch()
	return list


def fetch_EnkiThread_by_forum( forum ):
	list = EnkiModelThread.query( EnkiModelThread.forum == forum ).order( -EnkiModelThread.time_created ).fetch()
	return list


def fetch_EnkiPost_by_thread( thread, limit, offset ):
	list = EnkiModelPost.query( EnkiModelPost.thread == thread ).order( EnkiModelPost.time_created ).fetch( limit = limit, offset = offset )
	return list


def fetch_EnkiPost_by_author( author ):
	list = EnkiModelPost.query( EnkiModelPost.author == author ).order( -EnkiModelPost.time_created ).fetch()
	return list


def fetch_EnkiPost_key_by_author( author ):
	list = EnkiModelPost.query( EnkiModelPost.author == author ).fetch( keys_only = True )
	return list
