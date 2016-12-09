import webapp2
import webapp2_extras.routes
import copy

import settings
import enki
import enki.libutil
import enki.textmessages as MSG

class HandlerMain( enki.HandlerBase ):

	def get(self):
		if not settings.SECRETS_EXIST:
			self.add_infomessage( 'warning', MSG.WARNING(), 'Setup incomplete, see <a class="alert-link"" href="https://github.com/juliettef/enkiWS#enabling-oauth-login-with-google-facebook-twitter">documentation</a>.')
		self.render_tmpl( 'home.html', False,
		                  active_menu = 'home' )

enki.ExtensionLibrary.set_extensions([ enki.ExtensionStore(),
                                       enki.ExtensionForums(),
                                       enki.ExtensionRestAPI(),
                                       enki.ExtensionFriends(),
                                       ])


routes = [ webapp2.Route( '/', HandlerMain, name = 'home' ) ]
routes += enki.routes_account \
		  + enki.ExtensionLibrary.get_routes()\
		  + enki.routes_info\
		  + enki.routes_legal\

routes_copy = copy.deepcopy( routes )
locale_routes = [ webapp2_extras.routes.PathPrefixRoute('/<locale:[a-z]{2}_[A-Z]{2}>',  [ webapp2_extras.routes.NamePrefixRoute('locale-', routes ) ] ) ]
locale_routes += routes_copy + settings.get_routes_oauth()

app = webapp2.WSGIApplication( routes = locale_routes, debug = enki.libutil.is_debug(), config = settings.config )
