import webapp2_extras.security
from google.appengine.ext import ndb


import settings
import enki.libuser
import enki.libutil
from enki.modelproductkey import EnkiModelProductKey


def generate_product_code():
	code = webapp2_extras.security.generate_random_string( length = 15, pool = webapp2_extras.security.UPPERCASE_ALPHANUMERIC )
	return code


#=== QUERIES ==================================================================

