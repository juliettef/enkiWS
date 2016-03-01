import webapp2

import enki
import enki.libfriends
import enki.libdisplayname
import enki.textmessages as MSG

from enki.extensions import Extension


class HandlerFriends( enki.HandlerBase ):

	def get( self ):
		if self.ensure_is_logged_in() and self.ensure_has_display_name():
			self.render_tmpl( 'friends.html',
			                  active_menu = 'profile',
			                  data = enki.libfriends.get_friends_user_id_display_name_url( self.user_id ))

	def post( self ):
		if self.ensure_is_logged_in() and self.ensure_has_display_name():
			self.check_CSRF()
			user_id = self.user_id
			friend_id_invite = self.request.get( 'invite' )
			friend_id_remove = self.request.get( 'remove' )
			friend_name_search = self.request.get( 'search' ).strip()[:(enki.libdisplayname.DISPLAY_NAME_LENGTH_MAX + 4 )]  # 4 allows for some leading and trailing characters
			already_friends = ''
			has_friends = enki.libfriends.exist_EnkiFriends
			error_message = ''
			result = ''

			if friend_id_invite: # send invitation to user to become friend
				enki.libfriends.send_friend_request( user_id, int( friend_id_invite ))
				self.add_infomessage( 'success', MSG.SUCCESS(), MSG.FRIEND_INVITATION_SENT( enki.libdisplayname.get_display_name( int( friend_id_invite ))))
			elif friend_id_remove: # unfriend
				enki.libfriends.remove_friend( user_id, int( friend_id_remove ))
				has_friends = enki.libfriends.exist_EnkiFriends
				self.add_infomessage( 'success', MSG.SUCCESS(), MSG.FRIEND_REMOVED( enki.libdisplayname.get_display_name( int( friend_id_remove ))))
			elif friend_name_search: # search for user to invite
				users_ids_to_ignore = [ user_id ]
				if has_friends:
					users_ids_to_ignore += enki.libfriends.get_friends_user_id( user_id )
				result = enki.libdisplayname.find_users_by_display_name( friend_name_search, users_ids_to_ignore )
				if result.error == enki.libdisplayname.ERROR_DISPLAY_NAME_INVALID:
					error_message = MSG.DISPLAY_NAME_INVALID()
				elif result.error == enki.libdisplayname.ERROR_DISPLAY_NAME_NOT_EXIST:
					error_message = MSG.DISPLAY_NAME_NOT_EXIST()
			else:
				error_message = MSG.DISPLAY_NAME_NEEDED()

			if has_friends:
				already_friends = enki.libfriends.get_friends_user_id_display_name_url( user_id )

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
			                  data = enki.libmessage.get_messages( self.user_id ) )

	def post( self ):
		if self.ensure_is_logged_in() and self.ensure_has_display_name():
			user_id = self.user_id
			instruction = self.request.arguments()[ 0 ]
			message_id = int( self.request.get( instruction ))
			sender_id = enki.libmessage.get_EnkiMessage_by_id( message_id ).sender
			if instruction == 'accept':
				enki.libfriends.add_friend( user_id, sender_id )
			elif instruction == 'decline':
				enki.libmessage.remove_messages_crossed( user_id, sender_id )
			elif instruction == 'delete':
				enki.libmessage.remove_message( message_id )
			self.render_tmpl( 'messages.html',
			                  data = enki.libmessage.get_messages( self.user_id ) )


class ExtensionFriends( Extension ):

	def get_routes( self ):
		return [ webapp2.Route( '/friends', HandlerFriends, name = 'friends' ),
		         webapp2.Route( '/messages', HandlerMessages, name = 'messages' ),
		         ]
