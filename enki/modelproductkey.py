from google.appengine.ext.ndb import model


class EnkiModelProductKey( model.Model ):

	product_code = model.StringProperty()  # mandatory
	purchaser_email = model.TextProperty()  # mandatory
	purchaser_user_id = model.IntegerProperty() # if the purchaser is registered
	product_name = model.TextProperty()  # mandatory
	purchase_date = model.DateTimeProperty( auto_now_add = True )   # mandatory

	purchase_price = model.IntegerProperty()

	registered_to_user = model.IntegerProperty()

	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )
