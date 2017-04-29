import enki.libdisplayname
import enki.libmessage
import enki.libutil
from enki.modelfriends import EnkiModelFriends
from enki.modelmessage import EnkiModelMessage


INFO_FRIENDS = -61


def get_friends_user_id( user_id ):
	friend_list = []
	list = EnkiModelFriends.fetch_by_user_id( user_id )
	if list:
		for i, item in enumerate( list ):
			if item.friends[ 0 ] == user_id:
				friend_id = item.friends[ 1 ]
			else:
				friend_id = item.friends[ 0 ]
			friend_list.append( friend_id )
	return friend_list


def get_friends_user_id_display_name( user_id ):
	friend_list = []
	list = get_friends_user_id( user_id )
	if list:
		for friend_id in list:
			friend = enki.libdisplayname.get_user_id_display_name( enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( friend_id ))
			friend_list.append( friend )
	return friend_list


def get_friends_user_id_display_name_url( user_id ):
	friend_list = []
	list = get_friends_user_id( user_id )
	if list:
		for friend_id in list:
			friend = enki.libdisplayname.get_user_id_display_name_url( enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( friend_id ))
			friend_list.append( friend )
	return friend_list


def send_friend_request( sender_id, friend_id ):
	result = enki.libutil.ENKILIB_OK
	if friend_id != sender_id: # friend is not me
		if not EnkiModelFriends.exist_by_user_ids( sender_id, friend_id ): # we're not currently friends
			already_invited = EnkiModelMessage.get_key_by_sender_recipient( friend_id, sender_id )
			if already_invited:
				# if an invite from the potential friend already exists, add the pair of friends immediately and delete the invite(s)
				add_friend( sender_id, friend_id )
				result = INFO_FRIENDS
			# send an invitation to friend (unless it's a duplicate)
			elif not EnkiModelMessage.exist_by_sender_recipient( sender_id, friend_id ):
				message = EnkiModelMessage( sender = sender_id, recipient = friend_id, type = 'friend_request' )
				message.put()
	else:
		result = enki.libdisplayname.ERROR_DISPLAY_NAME_INVALID
	return result


def add_friend( user_id, friend_id ):
	if not EnkiModelFriends.exist_by_user_ids( user_id, friend_id ):
		friends = EnkiModelFriends( friends = [ user_id, friend_id ])
		friends.put()
	# clean up any remaining friend invitations (from either side)
	enki.libmessage.remove_messages_crossed( user_id, friend_id )


def remove_friend( user_id, friend_id ):
	friends = EnkiModelFriends.get_key_by_user_ids( user_id, friend_id )
	if friends:
		friends.delete()
	# clean up any remaining friend invitations (from either side)
	enki.libmessage.remove_messages_crossed( user_id, friend_id )
