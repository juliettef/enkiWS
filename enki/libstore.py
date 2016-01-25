import webapp2_extras.security
from google.appengine.ext import ndb


import settings
import enki.libuser
import enki.libutil
from enki.modelproductkey import EnkiModelProductKey


def generate_product_code():
	code = webapp2_extras.security.generate_random_string( length = 15, pool = webapp2_extras.security.UPPERCASE_ALPHANUMERIC )
	return code

def insert_dash_5_10( string ):
	result_10 = string[:10] + '-' + string[10:]
	result = result_10[:5] + '-' + result_10[5:]
	return result


#=== QUERIES ==================================================================

