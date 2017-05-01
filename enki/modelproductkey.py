import webapp2_extras.security
import logging

from google.appengine.ext import ndb
from google.appengine.ext.ndb import model


class EnkiModelProductKey( model.Model ):

	#=== MODEL ====================================================================

	licence_key = model.StringProperty()  # mandatory
	product_name = model.StringProperty()  # mandatory

	purchaser_email = model.StringProperty()  # mandatory
	purchaser_user_id = model.IntegerProperty() # if the purchaser is logged in

	shop_name = model.StringProperty( choices = [ 'FastSpring', 'Emulator', 'Generator' ])
	purchase_price = model.StringProperty()
	quantity = model.IntegerProperty()
	order_id = model.StringProperty()
	order_type = model.StringProperty( choices = [ 'purchase', 'test', 'free-press', 'free-gift', 'free-promo' ])
	info = model.TextProperty()

	activated_by_user = model.IntegerProperty( default = -1 )

	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )

	#=== CONSTANTS ================================================================

	LICENCE_KEY_LENGTH = 15
	LICENCE_KEY_DASHES_LENGTH = LICENCE_KEY_LENGTH + 2  # licence including two inserted dashes
	SEPARATOR_LICENCE_KEYS = '\n'

	#=== QUERIES ==================================================================

	@classmethod
	def exist_by_licence_key( cls, licence_key ):
		count = cls.query(cls.licence_key == licence_key.replace( '-', '' )).count(1)
		return count > 0

	@classmethod
	def get_by_licence_key( cls, licence_key ):
		return cls.query( cls.licence_key == licence_key.replace( '-', '' )).get()

	@classmethod
	def exist_product_by_activator( cls, user_id, product_name ):
		count = cls.query( ndb.AND( cls.activated_by_user == user_id, cls.product_name == product_name )).count( 1 )
		return count > 0

	@classmethod
	def fetch_by_purchaser( cls, user_id ):
		return cls.query( cls.purchaser_user_id == user_id ).order( cls.product_name ).fetch()

	@classmethod
	def exist_by_activator( cls, user_id ):
		count = cls.query( cls.activated_by_user == user_id ).count( 1 )
		return count > 0

	@classmethod
	def count_by_activator( cls, user_id ):
		return cls.query( cls.activated_by_user == user_id ).count()

	@classmethod
	def fetch_by_activator( cls, user_id ):
		return cls.query( cls.activated_by_user == user_id ).order( cls.product_name ).fetch()

	@classmethod
	def fetch_by_activator_products_list( cls, user_id, products_list ):
		return cls.query( ndb.AND( cls.activated_by_user == user_id, cls.product_name.IN( products_list ))).fetch()

	@classmethod
	def exist_by_purchaser_or_activator( cls, user_id ):
		count = cls.query( ndb.OR( cls.purchaser_user_id == user_id, cls.activated_by_user == user_id )).count( 1 )
		return count > 0

	@classmethod
	def exist_by_purchaser_not_activated( cls, user_id ):
		count = cls.query( ndb.AND( cls.purchaser_user_id == user_id, cls.activated_by_user == -1 )).count( 1 )
		return count > 0

	@classmethod
	def count_by_purchaser_not_activated( cls, user_id ):
		return cls.query( ndb.AND( cls.purchaser_user_id == user_id, cls.activated_by_user == -1)).count()

	@classmethod
	def count_by_shop_name_order_type_activated( cls, shop_name, order_type ):
		return cls.query( ndb.AND( cls.shop_name == shop_name, cls.order_type == order_type, cls.activated_by_user >= 0 )).count()

	@classmethod
	def count_by_shop_name_order_type_not_activated( cls, shop_name, order_type ):
		return cls.query( ndb.AND( cls.shop_name == shop_name, cls.order_type == order_type, cls.activated_by_user == -1 )).count()

	#=== UTILITIES ================================================================

	@classmethod
	def generate_licence_key( cls ):
		attempt = 0
		while attempt < 1000:
			code = webapp2_extras.security.generate_random_string( length = cls.LICENCE_KEY_LENGTH, pool = webapp2_extras.security.UPPERCASE_ALPHANUMERIC )
			if not cls.exist_by_licence_key( code ):
				return code
			attempt += 1
		logging.error( 'Could not generate unique Licence Key. LICENCE_KEY_LENGTH = ' + str( cls.LICENCE_KEY_LENGTH ))
		return 'LICENGENERERROR'	# in case unique licence code cannot be generated (unlikely)

	@classmethod
	def insert_dashes_5_10( cls, string ):
		result_10 = string[:10] + '-' + string[10:]
		result = result_10[:5] + '-' + result_10[5:]
		return result

	@classmethod
	def generate_licence_keys( cls, quantity ):
		licence_keys = ''
		if quantity:
			quantity = int( quantity )
			while quantity > 0:
				licence_keys += cls.insert_dashes_5_10( cls.generate_licence_key()) + cls.SEPARATOR_LICENCE_KEYS
				quantity -= 1
		return licence_keys

	@classmethod
	def count_licence_keys( cls, shop_name, product_key, activated = True ):
		if activated:
			return cls.count_by_shop_name_order_type_activated( shop_name, product_key )
		else:
			return cls.count_by_shop_name_order_type_not_activated( shop_name, product_key )
