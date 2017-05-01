import webapp2
import cgi
import re

from google.appengine.ext import ndb

import settings
import enki.libutil
from enki.authcryptcontext import pwd_context
from enki.modeltokenemailrollback import EnkiModelTokenEmailRollback
from enki.modeltokenverify import EnkiModelTokenVerify


ERROR_EMAIL_MISSING = -11
ERROR_EMAIL_FORMAT_INVALID = -12
ERROR_PASSWORD_BLANK = -21
ERROR_PASSWORD_TOO_SHORT = -22
ERROR_PASSWORD_NOT_SET = -23


def validate_email( email ):
	result = enki.libutil.ENKILIB_OK
	email_escaped = cgi.escape(email, quote = True)
	if email and email == email_escaped:
		if (('.' not in email) or (not re.search('[^@]+@[^@]+', email))):
			result = ERROR_EMAIL_FORMAT_INVALID
	elif email == '':
		result = ERROR_EMAIL_MISSING
	else:
		result = ERROR_EMAIL_FORMAT_INVALID
	return email_escaped, result


def validate_password( password ):
	result = enki.libutil.ENKILIB_OK
	if password == '':
		result = ERROR_PASSWORD_BLANK
	elif len( password ) < webapp2.get_app().config.get( 'enki' ).get( 'user' ).get( 'PASSWORD_LENGTH_MIN' ):
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
	entities = EnkiModelTokenVerify.fetch_keys_by_email_type( email, type )
	if entities:
		ndb.delete_multi( entities )


def add_roles( user, roles ):
	for role in roles:
		if role not in user.roles:
			user.roles.append( role )
	user.put()


def remove_roles( user, roles ):
	for role in roles:
		if role in user.roles:
			user.roles.remove( role )
	user.put()


def has_permissions( user, permissions ):
# check a user has all the permissions required
	if user and permissions:
		for permission in permissions:
			if not has_permission( user, permission ):
				return False
		return True	# all permissions have tested true by this point
	return False


def has_permission( user, permission ):
# check a user has a permission
	if user and permission:
		if user.roles:
			for role in user.roles:
				if permission in settings.ROLES_PERMISSIONS[ role ]:
					return True
	return False


#=== QUERIES ==================================================================




def get_EmailRollbackToken_by_user_id_email( user_id, email ):
	entity = EnkiModelTokenEmailRollback.query( ndb.AND( EnkiModelTokenEmailRollback.user_id == user_id,
	                                                     EnkiModelTokenEmailRollback.email == email )).get()
	return entity


def get_RollbackToken_by_token( token ):
	entity = EnkiModelTokenEmailRollback.query( EnkiModelTokenEmailRollback.token == token ).get()
	return entity


def fetch_keys_RollbackToken( user_id ):
	keys = EnkiModelTokenEmailRollback.query( EnkiModelTokenEmailRollback.user_id == user_id ).fetch( keys_only = True )
	return keys


def fetch_keys_RollbackToken_by_time( user_id, time_created ):
	keys = EnkiModelTokenEmailRollback.query( ndb.AND( EnkiModelTokenEmailRollback.time_created >= time_created ,
	                                                   EnkiModelTokenEmailRollback.user_id == user_id )).fetch( keys_only = True )
	return keys
