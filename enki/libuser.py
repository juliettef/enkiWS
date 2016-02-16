import re

from google.appengine.ext import ndb

import enki.libutil
from enki.authcryptcontext import pwd_context
from enki.modeluser import EnkiModelUser
from enki.modeltokenauth import EnkiModelTokenAuth
from enki.modeltokenemailrollback import EnkiModelTokenEmailRollback
from enki.modeltokenverify import EnkiModelTokenVerify

PASSWORD_LENGTH_MIN = 3 # passwords must be at least n chars long

ERROR_EMAIL_MISSING = -11
ERROR_EMAIL_FORMAT_INVALID = -12
ERROR_PASSWORD_BLANK = -21
ERROR_PASSWORD_TOO_SHORT = -22
ERROR_PASSWORD_NOT_SET = -23


def validate_email( email ):
	result = enki.libutil.ENKILIB_OK
	if email:
		if not re.search( '[^@]+@[^@]+', email ):
			result = ERROR_EMAIL_FORMAT_INVALID
	else:
		result = ERROR_EMAIL_MISSING
	return result


def validate_password( password ):
	result = enki.libutil.ENKILIB_OK
	if password == '':
		result = ERROR_PASSWORD_BLANK
	elif len( password ) < PASSWORD_LENGTH_MIN:
		result = ERROR_PASSWORD_TOO_SHORT
	return result


def set_password( user, password ):
	result = validate_password( password )
	if result == enki.libutil.ENKILIB_OK:
		passwordHash = pwd_context.encrypt( password )
		user.password = passwordHash
		user.put()
	return result


def delete_verifytoken_by_email( email, type ):
	# delete all verify tokens for a given email and type (cleanup)
	entities = fetch_keys_VerifyToken_by_email_type( email, type )
	if entities:
		ndb.delete_multi( entities )


def revoke_user_authentications( user_id ):
	tokens = fetch_keys_AuthToken( user_id )
	if tokens:
		# delete the token from the db
		ndb.delete_multi( tokens )


#=== QUERIES ==================================================================


def get_EnkiUser( email ):
	entity = EnkiModelUser.query( EnkiModelUser.email == email ).get()
	if entity:
		return entity
	else:
		return None


def get_key_EnkiUser( email ):
	key = EnkiModelUser.query( EnkiModelUser.email == email ).get( keys_only = True )
	if key:
		return key
	else:
		return None


def exist_EnkiUser( email ):
	count = EnkiModelUser.query( EnkiModelUser.email == email ).count( 1 )
	if count:
		return True
	else:
		return False


def get_AuthToken( user_id, token ):
	entity = EnkiModelTokenAuth.query( ndb.AND( EnkiModelTokenAuth.user_id == user_id,
	                                            EnkiModelTokenAuth.token == token )).get()
	if entity:
		return entity
	else:
		return None


def exist_AuthToken( user_id, token ):
	count = EnkiModelTokenAuth.query( ndb.AND( EnkiModelTokenAuth.user_id == user_id,
	                                           EnkiModelTokenAuth.token == token )).count( 1 )
	if count:
		return True
	else:
		return False


def fetch_keys_AuthToken( user_id ):
	keys = EnkiModelTokenAuth.query( EnkiModelTokenAuth.user_id == user_id ).fetch( keys_only = True )
	if keys:
		return keys
	else:
		return None


def get_VerifyToken_by_user_id_email_type( user_id, email, type ):
	entity = EnkiModelTokenVerify.query( ndb.AND( EnkiModelTokenVerify.user_id == user_id,
	                                              EnkiModelTokenVerify.email == email,
	                                              EnkiModelTokenVerify.type == type )).get()
	if entity:
		return entity
	else:
		return None


def get_VerifyToken( token ):
	entity = EnkiModelTokenVerify.query( EnkiModelTokenVerify.token == token ).get()
	if entity:
		return entity
	else:
		return None


def get_VerifyToken_by_token_type( token, type ):
	entity = EnkiModelTokenVerify.query( ndb.AND( EnkiModelTokenVerify.token == token,
	                                              EnkiModelTokenVerify.type == type )).get()
	if entity:
		return entity
	else:
		return None


def get_VerifyToken_by_authid_type( authId, type ):
	entity = EnkiModelTokenVerify.query( ndb.AND( EnkiModelTokenVerify.auth_ids_provider == authId,
	                                              EnkiModelTokenVerify.type == type )).get()
	if entity:
		return entity
	else:
		return None


def fetch_keys_VerifyToken_by_user_id( user_id ):
	keys = EnkiModelTokenVerify.query( EnkiModelTokenVerify.user_id == user_id ).fetch( keys_only = True )
	if keys:
		return keys
	else:
		return None


def fetch_keys_VerifyToken_by_user_id_type( user_id, type ):
	keys = EnkiModelTokenVerify.query( ndb.AND( EnkiModelTokenVerify.user_id == user_id,
	                                            EnkiModelTokenVerify.type == type )).fetch( keys_only = True )
	if keys:
		return keys
	else:
		return None


def fetch_keys_VerifyToken_by_user_id_except_type( user_id, type ):
	keys = EnkiModelTokenVerify.query( ndb.AND( EnkiModelTokenVerify.user_id == user_id,
	                                            EnkiModelTokenVerify.type != type )).fetch( keys_only = True )
	if keys:
		return keys
	else:
		return None


def fetch_keys_VerifyToken_by_email_type( email, type ):
	keys = EnkiModelTokenVerify.query( ndb.AND( EnkiModelTokenVerify.email == email,
	                                            EnkiModelTokenVerify.type == type )).fetch( keys_only = True )
	if keys:
		return keys
	else:
		return None


def exist_VerifyToken( token, type ):
	count = EnkiModelTokenVerify.query( ndb.AND( EnkiModelTokenVerify.token == token,
	                                             EnkiModelTokenVerify.type == type )).count( 1 )
	if count:
		return True
	else:
		return False


def exist_VerifyToken_by_user_id_token( user_id, token ):
	count = EnkiModelTokenVerify.query( ndb.AND( EnkiModelTokenVerify.user_id == user_id,
	                                             EnkiModelTokenVerify.token == token )).count( 1 )
	if count:
		return True
	else:
		return False


def get_EmailRollbackToken_by_user_id_email( user_id, email ):
	entity = EnkiModelTokenEmailRollback.query( ndb.AND( EnkiModelTokenEmailRollback.user_id == user_id,
	                                                     EnkiModelTokenEmailRollback.email == email )).get()
	if entity:
		return entity
	else:
		return None


def get_RollbackToken_by_token( token ):
	entity = EnkiModelTokenEmailRollback.query( EnkiModelTokenEmailRollback.token == token ).get()
	if entity:
		return entity
	else:
		return None


def fetch_keys_RollbackToken( user_id ):
	keys = EnkiModelTokenEmailRollback.query( EnkiModelTokenEmailRollback.user_id == user_id ).fetch( keys_only = True )
	if keys:
		return keys
	else:
		return None


def fetch_keys_RollbackToken_by_time( user_id, time_created ):
	keys = EnkiModelTokenEmailRollback.query( ndb.AND( EnkiModelTokenEmailRollback.time_created >= time_created ,
	                                                   EnkiModelTokenEmailRollback.user_id == user_id )).fetch( keys_only = True )
	if keys:
		return keys
	else:
		return None
