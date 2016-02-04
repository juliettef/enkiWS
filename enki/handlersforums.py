import webapp2

from webapp2_extras.i18n import gettext as _

import enki
import enki.textmessages as MSG

from enki.extensions import Extension
from enki.extensions import ExtensionPage
from enki.modelcounter import EnkiModelCounter
from enki.modelforum import EnkiModelForum
from enki.modelthread import EnkiModelThread


class HandlerForums( enki.HandlerBase ):

	def get( self ):
		thread_view_count = EnkiModelCounter.get_count()
		if not enki.libforum.exist_EnkiForums():
			# if no forum topic exists , populate the forums with default topics
			enki.libforum.set_forum()
		self.render_tmpl( 'forums.html', False,
		                  active_menu = 'forums',
		                  thread_view_count = thread_view_count,
		                  data_company = enki.libforum.get_forums_data( 'Company' ),
		                  data_game = enki.libforum.get_forums_data( 'Game' ) )


class HandlerForum( enki.HandlerBase ):

	def get( self, forum ):
		data = ''
		not_found = ''
		if forum.isdigit() and EnkiModelForum.get_by_id( int( forum ) ):
			EnkiModelCounter.increment()
			data = enki.libforum.get_forum_data( forum )
		else:
			not_found = MSG.FORUM_NOT_EXIST( )
		self.render_tmpl( 'forum.html', False,
		                  active_menu = 'forums',
		                  data = data,
		                  not_found = not_found,
		                  maxpostlength = enki.libforum.POST_LENGTH_MAX,
		                  maxthreadtitlelength = enki.libforum.THREAD_TITLE_LENGTH_MAX )

	def post( self, forum ):
		if self.ensure_is_logged_in() and enki.libdisplayname.ensure_has_display_name( self ):
			if forum.isdigit() and EnkiModelForum.get_by_id( int( forum ) ):
				user_id = self.user_id
				thread_title = self.request.get( 'thread_title' )
				post_body = self.request.get( 'post_body' )
				submit_type = self.request.get( 'submittype' )
				error_message_threadtitle = ''
				error_message_postbody = ''
				preview_threadtitle = ''
				preview_post = ''
				pmtoken = self.request.get( 'preventmultitoken' )
				show_input = True
				if submit_type == 'input':
					thread_title = ''
					post_body = ''
					pmtoken = enki.libforum.add_preventmultipost_token( )
				else:
					self.check_CSRF()
					if submit_type != 'cancel':
						if not thread_title:
							error_message_threadtitle = MSG.THREAD_TITLE_NEEDED( )
						else:
							exceed = len( thread_title ) - enki.libforum.THREAD_TITLE_LENGTH_MAX
							if exceed > 0:
								error_message_threadtitle = MSG.THREAD_TITLE_TOO_LONG( exceed )
						if not post_body:
							error_message_postbody = MSG.POST_BODY_NEEDED()
						else:
							exceed = len( post_body ) - enki.libforum.POST_LENGTH_MAX
							if exceed > 0:
								error_message_postbody = MSG.POST_BODY_TOO_LONG( exceed )

					if not error_message_threadtitle and not error_message_postbody:
						if submit_type == 'submit':
							if enki.libforum.check_and_delete_preventmultipost_token( pmtoken ):
								result = enki.libforum.add_thread_and_post( user_id, forum, thread_title, post_body )
								if result == enki.libutil.ENKILIB_OK:
									self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.THREAD_PUBLISHED())
									thread_title = ''
									post_body = ''
									self.redirect( enki.libutil.get_local_url( 'forum', { 'forum': forum }))
									return
								else:
									error_threadtitle = MSG.FAIL_THREAD_SUBMISSION()
							else:
								thread_title = ''
								post_body = ''
						elif submit_type == 'preview':
							preview_threadtitle = thread_title
							preview_post = post_body
						elif submit_type == 'cancel':
							thread_title = ''
							post_body = ''

				self.render_tmpl( 'forum.html', CSRFneeded = show_input,
				                  active_menu = 'forums',
				                  data = enki.libforum.get_forum_data( forum ),
				                  show_input = show_input,
				                  preventmultitoken = pmtoken,
				                  error_threadtitle = error_message_threadtitle,
				                  error_postbody = error_message_postbody,
				                  maxpostlength = enki.libforum.POST_LENGTH_MAX,
				                  maxthreadtitlelength = enki.libforum.THREAD_TITLE_LENGTH_MAX,
				                  threadtitle = thread_title,
				                  postbody = post_body,
				                  previewthreadtitle = preview_threadtitle,
				                  previewpost = preview_post )


class HandlerThread( enki.HandlerBase ):

	def get( self, thread ):
		data = ''
		pagination = ''
		not_found = ''
		post_requested = str( self.request.get( 'start' ))
		post_count = str( self.request.get( 'count' ))
		validation_result = enki.libforum.validate_thread_pagination( thread, post_requested, post_count )
		if validation_result == enki.libutil.ENKILIB_OK:
			if not post_requested:
				post_requested = enki.libforum.POST_DEFAULT
			if not post_count:
				post_count = enki.libforum.POSTS_PER_PAGE
			data = enki.libforum.get_thread_data( thread, post_requested, post_count )
			pagination = enki.libforum.get_thread_pagination_data( thread, post_requested, post_count )
		else:
			not_found = MSG.POST_THREAD_NOT_EXIST( )
		self.render_tmpl( 'thread.html', False,
		                  active_menu = 'forums',
		                  data = data,
		                  pagination = pagination,
		                  user_id = self.user_id,
		                  not_found = not_found,
		                  maxpostlength = enki.libforum.POST_LENGTH_MAX )

	def post( self, thread ):
		if self.ensure_is_logged_in() and enki.libdisplayname.ensure_has_display_name( self ):
			if thread.isdigit() and EnkiModelThread.get_by_id( int( thread ) ):
				user = self.user_id
				post_body = self.request.get( 'post_body' )
				submit_type = self.request.get( 'submittype' )

				post_count = str( self.request.get( 'count' ))
				post_requested = str( self.request.get( 'start' ))
				if not post_count:
					post_count = enki.libforum.POSTS_PER_PAGE
				if not post_requested:
					post_requested = enki.libforum.get_first_post_on_page( enki.libforum.get_page( EnkiModelThread.get_by_id( int( thread )), enki.libforum.POST_LAST, int( post_count )), int( post_count ))

				error_message = ''
				preview = ''
				pmtoken = self.request.get( 'preventmultitoken' )
				show_input = True
				if submit_type == 'input':
					post_body = ''
					pmtoken = enki.libforum.add_preventmultipost_token( )
				else:
					self.check_CSRF()
					if submit_type != 'cancel':
						if not post_body:
							error_message = MSG.POST_BODY_NEEDED()
						else:
							exceed = len( post_body ) - enki.libforum.POST_LENGTH_MAX
							if exceed > 0:
								error_message = MSG.POST_BODY_TOO_LONG( exceed )
					if not error_message:
						if submit_type == 'submit':
							if enki.libforum.check_and_delete_preventmultipost_token( pmtoken ):
								result = enki.libforum.add_post( user, thread, post_body )
								if result == enki.libutil.ENKILIB_OK:
									self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.POST_PUBLISHED())
									post_body = ''
									post_requested = enki.libforum.get_first_post_on_page( enki.libforum.get_page( EnkiModelThread.get_by_id( int( thread )), enki.libforum.POST_LAST, int( post_count )), int( post_count ))
									self.redirect( enki.libutil.get_local_url( 'thread', { 'thread': thread, 'start': str( post_requested ), 'count': str( post_count )}))
									return
								else:
									error_message = MSG.FAIL_POST_SUBMISSION()
							else:
								post_body = ''
						elif submit_type == 'preview':
							preview = post_body
						elif submit_type == 'cancel':
							post_body = ''

				data = enki.libforum.get_thread_data( thread, post_requested, post_count )
				pagination = enki.libforum.get_thread_pagination_data( thread, post_requested, post_count )
				self.render_tmpl( 'thread.html', CSRFneeded = show_input,
				                  active_menu = 'forums',
				                  data = data,
				                  pagination = pagination,
				                  user_id = self.user_id,
				                  show_input = show_input,
				                  preventmultitoken = pmtoken,
				                  error = error_message,
				                  maxpostlength = enki.libforum.POST_LENGTH_MAX,
				                  postbody = post_body,
				                  preview = preview )


class HandlerPost( enki.HandlerBase ):

	def get( self, post ):
		data = ''
		not_found = ''
		is_author = False
		post_body = ''
		self.session[ 'sessionrefpath' ] = self.request.referrer
		if post.isdigit() and enki.libforum.EnkiModelPost.get_by_id( int( post ) ):
			data = enki.libforum.get_post_data( post )
			if data:
				is_author = True if self.user_id == data.author_data.user_id else False
				post_body = '' if data.post.body == enki.libforum.POST_DELETED else data.post.body
		else:
			not_found = MSG.POST_NOT_EXIST( )
		change = self.request.get( 'change' )
		CSRFneeded = True
		if change != 'edit' and change != 'delete':
			CSRFneeded = False
		self.render_tmpl( 'post.html', CSRFneeded,
		                  active_menu = 'forums',
		                  data = data,
		                  not_found = not_found,
		                  change = change,
		                  isauthor = is_author,
		                  postbody = post_body,
		                  maxpostlength = enki.libforum.POST_LENGTH_MAX )


	def post( self, post ):
		if self.ensure_is_logged_in() and enki.libdisplayname.ensure_has_display_name( self ):
			if post.isdigit() and enki.libforum.EnkiModelPost.get_by_id( int( post ) ):

				data = enki.libforum.get_post_data( post )
				is_author = True if self.user_id == data.author_data.user_id else False
				user = self.user_id
				post_body = self.request.get( 'post_body' )
				submit_type = self.request.get( 'submittype' )
				change = self.request.get( 'change' )
				error_message = ''
				preview = ''

				if submit_type == 'delete':
					self.check_CSRF()
					result = enki.libforum.delete_post( user, post )
					if result[ 0 ] == enki.libutil.ENKILIB_OK:
						self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.POST_DELETED())
						self.redirect( enki.libutil.get_local_url( 'thread', { 'thread' : result[ 1 ] } ) ) # redirect to parent thread
						return
					else:
						error_message = MSG.FAIL_POST_DELETION()

				elif submit_type == 'cancel':
					self.redirect( enki.libutil.get_local_url( data.post_page ) )
					return
				else:
					if not post_body:
						error_message = MSG.POST_BODY_NEEDED()
					else:
						exceed = len( post_body ) - enki.libforum.POST_LENGTH_MAX
						if exceed > 0:
							error_message = MSG.POST_BODY_TOO_LONG( exceed )

				if not error_message:
					if submit_type == 'submit':
						self.check_CSRF()
						result = enki.libforum.edit_post( user, post, post_body )
						if result[ 0 ] == enki.libutil.ENKILIB_OK:
							self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.POST_MODIFIED())
							self.redirect( enki.libutil.get_local_url( 'thread', { 'thread' : result[ 1 ] } ) ) # redirect to parent thread
							return
						else:
							error_message = MSG.FAIL_POST_MODIFICATION()
					elif submit_type == 'preview':
						preview = post_body

				self.render_tmpl( 'post.html',
				                  active_menu = 'forums',
				                  data = data,
				                  change = change,
				                  isauthor = is_author,
				                  error = error_message,
				                  postbody = post_body,
				                  maxpostlength = enki.libforum.POST_LENGTH_MAX,
				                  preview = preview )


class ExtensionPageUserPosts( ExtensionPage ):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'profilepublic', template_include = 'incuserposts.html' )

	def get_data( self, handler ):
		useridnumber = handler.request.route_kwargs.get( 'useridnumber' )
		data = {}
		data[ 'posts' ] = ''
		data[ 'is_author' ] = False
		if handler.ensure_is_logged_in():
			if useridnumber.isdigit() and enki.libuser.EnkiModelUser.get_by_id( int( useridnumber ) ):
				posts = enki.libforum.get_author_posts( useridnumber )
				if posts:
					data[ 'posts' ] = posts
					data[ 'is_author' ] = True if handler.user_id == posts.author_data.user_id else False
		return data


class ExtensionForums( Extension ):

	def get_routes( self ):
		return  [ webapp2.Route( '/forums', HandlerForums, name = 'forums' ),
                  webapp2.Route( '/f/<forum>', HandlerForum, name = 'forum' ),
		          webapp2.Route( '/t/<thread>', HandlerThread, name = 'thread' ),
		          webapp2.Route( '/p/<post>', HandlerPost, name = 'post' ),
                  ]

	def get_navbar_items( self ):
		return [( enki.libutil.get_local_url( 'forums' ), 'forums', _( "Forums" ))]

	def get_page_extensions( self ):
		return [ ExtensionPageUserPosts()]
