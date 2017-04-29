import webapp2

import enki
import enki.libutil
import enki.libdisplayname
import enki.textmessages as MSG

from enki.extensions import Extension
from enki.extensions import ExtensionPage
from enki.modelfriends import EnkiModelFriends
from enki.modelmessage import EnkiModelMessage


class HandlerFriends( enki.HandlerBase ):

	def get( self ):
		if self.ensure_is_logged_in() and self.ensure_has_display_name():
			self.render_tmpl( 'friends.html',
			                  active_menu = 'profile',
			                  data = EnkiModelFriends.get_friends_user_id_display_name_url( self.user_id ))

	def post( self ):
		if self.ensure_is_logged_in() and self.ensure_has_display_name():
			self.check_CSRF()
			user_id = self.user_id
			friend_id_invite = self.request.get( 'invite' )
			friend_id_remove = self.request.get( 'remove' )
			friend_name_search = self.request.get( 'search' ).strip()[:(enki.libdisplayname.DISPLAY_NAME_LENGTH_MAX + 4 )]  # 4 allows for some leading and trailing characters
			already_friends = ''
			has_friends = EnkiModelFriends.exist_by_user_id( user_id )
			error_message = ''
			result = ''

			if friend_id_invite: # send invitation to user to become friend
				outcome = EnkiModelFriends.send_friend_request( user_id, int( friend_id_invite ))
				if outcome == EnkiModelFriends.INFO_FRIENDS:
					self.add_infomessage( 'success', MSG.SUCCESS(), MSG.FRIEND_ADDED( enki.libdisplayname.get_display_name( int( friend_id_invite ))))
				elif outcome == enki.libutil.ENKILIB_OK:
					self.add_infomessage( 'success', MSG.SUCCESS(), MSG.FRIEND_INVITATION_SENT( enki.libdisplayname.get_display_name( int( friend_id_invite ))))
			elif friend_id_remove: # unfriend
				EnkiModelFriends.remove_friend( user_id, int( friend_id_remove ))
				has_friends = EnkiModelFriends.exist_by_user_id( user_id )
				self.add_infomessage( 'success', MSG.SUCCESS(), MSG.FRIEND_REMOVED( enki.libdisplayname.get_display_name( int( friend_id_remove ))))
			elif friend_name_search: # search for user to invite
				users_ids_to_ignore = [ user_id ]
				if has_friends:
					users_ids_to_ignore += EnkiModelFriends.get_friends_user_id( user_id )
				result = enki.libdisplayname.find_users_by_display_name( friend_name_search, users_ids_to_ignore )
				if result.error == enki.libdisplayname.ERROR_DISPLAY_NAME_INVALID:
					error_message = MSG.DISPLAY_NAME_INVALID()
				elif result.error == enki.libdisplayname.ERROR_DISPLAY_NAME_NOT_EXIST:
					error_message = MSG.DISPLAY_NAME_NOT_EXIST()
			else:
				error_message = MSG.DISPLAY_NAME_NEEDED()

			if has_friends:
				already_friends = EnkiModelFriends.get_friends_user_id_display_name_url( user_id )

			self.render_tmpl( 'friends.html',
			                  data = already_friends,
			                  error = error_message,
			                  result = result,
			                  friend_name = friend_name_search )


class HandlerMessages( enki.HandlerBase ):

	def get( self ):
		if self.ensure_is_logged_in() and self.ensure_has_display_name():
			self.render_tmpl( 'messages.html',
			                  active_menu = 'profile',
			                  data = EnkiModelMessage.get_messages( self.user_id ))

	def post( self ):
		if self.ensure_is_logged_in() and self.ensure_has_display_name():
			self.check_CSRF()
			user_id = self.user_id
			message_accept = self.request.get( 'accept' )
			message_decline = self.request.get( 'decline' )

			if message_accept:
				sender_id = EnkiModelMessage.get_by_id( int( message_accept )).sender
				if sender_id:
					EnkiModelFriends.add_friend( user_id, sender_id )
					self.add_infomessage( 'success', MSG.SUCCESS(), MSG.FRIEND_ADDED( enki.libdisplayname.get_display_name( sender_id )))
			elif message_decline:
				sender_id = EnkiModelMessage.get_by_id( int( message_decline )).sender
				if sender_id:
					EnkiModelMessage.remove_messages_crossed( user_id, sender_id )

			self.render_tmpl( 'messages.html',
			                  data = EnkiModelMessage.get_messages( self.user_id ) )


class ExtensionPageMessageAlert( ExtensionPage ):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'navbar', template_include = 'incmessagealert.html' )

	def get_data( self, handler ):
		data = [ 0 ]
		if handler.user_id:
			if EnkiModelMessage.exist_by_recipient( handler.user_id ):
				data = [ 1 ]  # user has message
		return data


class ExtensionFriends( Extension ):

	def get_routes( self ):
		return [ webapp2.Route( '/friends', HandlerFriends, name = 'friends' ),
		         webapp2.Route( '/messages', HandlerMessages, name = 'messages' ),
		         ]

	def get_page_extensions( self ):
		return [ ExtensionPageMessageAlert()]
