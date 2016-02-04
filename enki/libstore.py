import webapp2_extras.security

from google.appengine.ext import ndb

from enki.modelproductkey import EnkiModelProductKey


SEPARATOR_LICENSE_KEYS = '\n'


def generate_license_key():
	code = webapp2_extras.security.generate_random_string( length = 15, pool = webapp2_extras.security.UPPERCASE_ALPHANUMERIC )
	return code


def insert_dashes_5_10( string ):
	result_10 = string[:10] + '-' + string[10:]
	result = result_10[:5] + '-' + result_10[5:]
	return result


def generate_license_keys( quantity ):
	license_keys = ''
	if quantity:
		quantity = int( quantity )
		while quantity > 0:
			license_keys += insert_dashes_5_10( generate_license_key()) + SEPARATOR_LICENSE_KEYS
			quantity -= 1
	return license_keys


#=== QUERIES ==================================================================


def get_EnkiProductKey_by_purchaser_license_key( user_id, license_key ):
	entity = EnkiModelProductKey.query( ndb.AND( EnkiModelProductKey.purchaser_user_id == user_id,
	                                              EnkiModelProductKey.license_key == license_key )).get()
	if entity:
		return entity
	else:
		return None


def fetch_EnkiProductKey_by_purchaser( user_id ):
	list = EnkiModelProductKey.query( EnkiModelProductKey.purchaser_user_id == user_id ).fetch()
	return list


def fetch_EnkiProuctKey_by_registered_to( user_id ):
	list = EnkiModelProductKey.query( EnkiModelProductKey.activated_by_user == user_id ).fetch( )
	return list
