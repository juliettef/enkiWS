import webapp2

import enki
import enki.textmessages as MSG


class HandlerFriends( enki.HandlerBase ):

	def get( self ):
		if self.ensure_is_logged_in():
			self.render_tmpl( 'friends.html',
			                  active_menu = 'profile',
			                  data = enki.libfriends.get_friends( self.user_id ) )

	def post( self ):
		if self.ensure_is_logged_in():
			user_id = self.user_id
			instruction = self.request.arguments()[ 0 ]
			friend_name = self.request.get( instruction )
			if instruction == 'invite': # find a user to become a friend
				preselection = enki.libdisplayname.find_users_by_display_name( friend_name, user_id )
				if not preselection.error:
					# display the preselection of friends
					error_message = ''
					self.render_tmpl( 'friends.html',
					                  data = enki.libfriends.get_friends( user_id ),
					                  error = error_message,
					                  result = preselection )
				elif preselection.error == enki.libdisplayname.ERROR_DISPLAY_NAME_INVALID:
					error_message = MSG.DISPLAY_NAME_NOT_EXIST()
					self.render_tmpl( 'friends.html',
					                  data = enki.libfriends.get_friends( user_id ),
					                  error = error_message,
					                  result = '' )
			elif instruction == 'confirm': # send invitation to user to become friend
				friend_id = int( self.request.get( instruction ))
				enki.libfriends.send_friend_request( user_id, friend_id )
			elif instruction == 'remove': # unfriend
				friend_id = int( self.request.get( instruction ))
				enki.libfriends.remove_friend( user_id, friend_id )


class HandlerMessages( enki.HandlerBase ):

	def get( self ):
		if self.ensure_is_logged_in():
			self.render_tmpl( 'messages.html',
			                  data = enki.libmessage.get_messages( self.user_id ) )

	def post( self ):
		if self.ensure_is_logged_in():
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


routes_friends = [ webapp2.Route( '/friends', HandlerFriends, name = 'friends' ),
                   webapp2.Route( '/messages', HandlerMessages, name = 'messages' ),
                   ]
