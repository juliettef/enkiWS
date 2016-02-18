from google.appengine.ext import ndb

import enki.libdisplayname
import enki.libmessage
import enki.libutil
from enki.modelfriends import EnkiModelFriends
from enki.modelmessage import EnkiModelMessage


def get_friends( user_id ):
	list = fetch_EnkiFriends_by_user( user_id )
	friend_list = []
	if list:
		for i, item in enumerate( list ):
			if item.friends[ 0 ] == user_id:
				friend_id = item.friends[ 1 ]
			else:
				friend_id = item.friends[ 0 ]
			friend = enki.libdisplayname.get_user_id_display_name_url( enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( friend_id ) )
			friend_list.append( friend )
	return friend_list


def send_friend_request( sender_id, friend_id ):
	if friend_id != sender_id: # friend is not me
		if not exist_EnkiFriends_by_friends( sender_id, friend_id ): # we're not currently friends
			already_invited = enki.libmessage.get_key_EnkiMessage_by_sender_recipient( friend_id, sender_id )
			if already_invited:
				# if an invite from the potential friend already exists, add the couple of friends immediately and delete the invite(s)
				add_friend( sender_id, friend_id )
			# send an invitation to friend (unless it's a duplicate)
			elif not enki.libmessage.exist_EnkiMessage_by_sender_recipient( sender_id, friend_id ):
				message = EnkiModelMessage( sender = sender_id, recipient = friend_id, type = 'friend_request' )
				message.put()
			result = enki.libutil.ENKILIB_OK
	else:
		result = enki.libdisplayname.ERROR_DISPLAY_NAME_INVALID
	return result


def add_friend( user_id, friend_id ):
	if not exist_EnkiFriends_by_friends( user_id, friend_id ):
		friends = EnkiModelFriends( friends = [ user_id, friend_id ])
		friends.put()
	# clean up any remaining friend invitations (from either side)
	enki.libmessage.remove_messages_crossed( user_id, friend_id )


def remove_friend( user_id, friend_id ):    # MOVE TO FRIEND
	friends = get_key_EnkiFriends_by_friends( user_id, friend_id )
	if friends:
		friends.delete()
	# clean up any remaining friend invitations (from either side)
	enki.libmessage.remove_messages_crossed( user_id, friend_id )


#=== QUERIES ==================================================================


def fetch_EnkiFriends_by_user( user ):
	list = EnkiModelFriends.query( EnkiModelFriends.friends == user ).fetch()
	return list


def exist_EnkiFriends_by_friends( user_a_id, user_b_id ):
	count = EnkiModelFriends.query( ndb.AND( EnkiModelFriends.friends == user_a_id,
	                                         EnkiModelFriends.friends == user_b_id )).count( 1 )
	return count > 0


def get_key_EnkiFriends_by_friends( user_a_id, user_b_id ):
	entity = EnkiModelFriends.query( ndb.AND( EnkiModelFriends.friends == user_a_id,
	                                          EnkiModelFriends.friends == user_b_id )).get( keys_only = True )
	return entity
