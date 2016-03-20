import webapp2

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
          + settings.get_routes_oauth() \
          + enki.ExtensionLibrary.get_routes()


app = webapp2.WSGIApplication( routes = routes, debug = enki.libutil.is_debug(), config = settings.config )
