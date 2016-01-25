from google.appengine.ext.ndb import model


class EnkiModelProductKey( model.Model ):

	product_code = model.StringProperty()  # mandatory
	product_name = model.TextProperty()  # mandatory

	purchaser_email = model.TextProperty()  # mandatory
	purchaser_user_id = model.IntegerProperty() # if the purchaser is registered

	purchase_date = model.DateTimeProperty()

	purchase_price = model.FloatProperty()

	registered_to_user = model.IntegerProperty()

	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )
