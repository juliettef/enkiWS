from google.appengine.ext import ndb
from google.appengine.ext.ndb import model


class EnkiModelFriends( model.Model ):

	friends = model.IntegerProperty( repeated = True )  # pairs of friends' user_ids

	@classmethod
	def exist_by_user_id( cls, user_id ):
		count = cls.query( ndb.OR( cls.friends == user_id, cls.friends == user_id )).count( 1 )
		return count > 0

	@classmethod
	def count_by_user_id( cls, user_id ):
		return cls.query( ndb.OR( cls.friends == user_id, cls.friends == user_id )).count()
