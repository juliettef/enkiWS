from google.appengine.ext import ndb
from google.appengine.ext.ndb import model

import enki.libutil
import enki.libdisplayname

from enki.modelmessage import EnkiModelMessage


class EnkiModelFriends( model.Model ):

	friends = model.IntegerProperty( repeated = True )  # pairs of friends' user_ids

	INFO_FRIENDS = -61

	@classmethod
	def exist_by_user_id( cls, user_id ):
		count = cls.query( ndb.OR( cls.friends == user_id, cls.friends == user_id )).count( 1 )
		return count > 0

	@classmethod
	def count_by_user_id( cls, user_id ):
		return cls.query( ndb.OR( cls.friends == user_id, cls.friends == user_id )).count()

	@classmethod
	def fetch_by_user_id( cls, user_id ):
		return cls.query( cls.friends == user_id ).fetch()

	@classmethod
	def exist_by_user_ids( cls, user_a_id, user_b_id ):
		count = cls.query( ndb.AND( cls.friends == user_a_id, cls.friends == user_b_id )).count( 1 )
		return count > 0

	@classmethod
	def get_key_by_user_ids( cls, user_a_id, user_b_id ):
		return cls.query( ndb.AND( cls.friends == user_a_id, cls.friends == user_b_id )).get( keys_only = True )

	@classmethod
	def get_friends_user_id( cls, user_id ):
		friend_list = []
		list = cls.fetch_by_user_id( user_id )
		if list:
			for i, item in enumerate( list ):
				if item.friends[ 0 ] == user_id:
					friend_id = item.friends[ 1 ]
				else:
					friend_id = item.friends[ 0 ]
				friend_list.append( friend_id )
		return friend_list

	@classmethod
	def get_friends_user_id_display_name( cls, user_id ):
		friend_list = []
		list = cls.get_friends_user_id( user_id )
		if list:
			for friend_id in list:
				friend = enki.libdisplayname.get_user_id_display_name( enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( friend_id ))
				friend_list.append( friend )
		return friend_list

	@classmethod
	def get_friends_user_id_display_name_url(  cls, user_id ):
		friend_list = []
		list = cls.get_friends_user_id( user_id )
		if list:
			for friend_id in list:
				friend = enki.libdisplayname.get_user_id_display_name_url( enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( friend_id ))
				friend_list.append( friend )
		return friend_list

	@classmethod
	def send_friend_request( cls, sender_id, friend_id ):
		result = enki.libutil.ENKILIB_OK
		if friend_id != sender_id: # friend is not me
			if not cls.exist_by_user_ids( sender_id, friend_id ): # we're not currently friends
				already_invited = EnkiModelMessage.get_key_by_sender_recipient( friend_id, sender_id )
				if already_invited:
					# if an invite from the potential friend already exists, add the pair of friends immediately and delete the invite(s)
					cls.add_friend( sender_id, friend_id )
					result = cls.INFO_FRIENDS
				# send an invitation to friend (unless it's a duplicate)
				elif not EnkiModelMessage.exist_by_sender_recipient( sender_id, friend_id ):
					EnkiModelMessage.send_message( sender_id, friend_id, 'friend_request' )
		else:
			result = enki.libdisplayname.ERROR_DISPLAY_NAME_INVALID
		return result

	@classmethod
	def add_friend(  cls, user_id, friend_id ):
		if not cls.exist_by_user_ids( user_id, friend_id ):
			friends = cls( friends = [ user_id, friend_id ])
			friends.put()
		# clean up any remaining friend invitations (from either side)
		EnkiModelMessage.remove_messages_crossed( user_id, friend_id )

	@classmethod
	def remove_friend( cls, user_id, friend_id ):
		friends = cls.get_key_by_user_ids( user_id, friend_id )
		if friends:
			friends.delete()
		# clean up any remaining friend invitations (from either side)
		EnkiModelMessage.remove_messages_crossed( user_id, friend_id )
