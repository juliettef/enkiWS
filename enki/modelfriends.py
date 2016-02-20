from google.appengine.ext.ndb import model


class EnkiModelFriends( model.Model ):

	friends = model.IntegerProperty( repeated = True )  # pairs of friends' user_ids
