import webapp2
import cgi
import re

import settings
import enki.libutil
from enki.authcryptcontext import pwd_context


ERROR_EMAIL_MISSING = -11
ERROR_EMAIL_FORMAT_INVALID = -12
ERROR_PASSWORD_BLANK = -21
ERROR_PASSWORD_TOO_SHORT = -22
ERROR_PASSWORD_NOT_SET = -23

def validate_email( email ):
	result = enki.libutil.ENKILIB_OK
	email_escaped = cgi.escape( email, quote = True )
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
