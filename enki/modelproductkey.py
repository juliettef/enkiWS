from google.appengine.ext.ndb import model


class EnkiModelProductKey( model.Model ):

	license_key = model.StringProperty()  # mandatory
	product_name = model.StringProperty()  # mandatory

	purchaser_email = model.StringProperty()  # mandatory
	purchaser_user_id = model.IntegerProperty() # if the purchaser is registered

	shop_name = model.StringProperty() #choices = [ 'FastSpring' ])
	purchase_price = model.StringProperty()
	quantity = model.IntegerProperty()
	order_id = model.StringProperty()
	order_type = model.StringProperty( choices = [ 'emulated', 'test', 'normal' ])

	registered_to_user = model.IntegerProperty()

	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )
