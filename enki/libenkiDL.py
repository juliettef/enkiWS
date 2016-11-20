import urllib
from google.appengine.api import urlfetch


class URLFetcher():

	def __init__( self ):
		self.error = 0
		self.download_url = ''

	def get_download_URL( self, enkiDL_URL, secret, item_to_download ):
		form_fields = { 'item' : item_to_download, 'secret' : secret }
		form_data = urllib.urlencode( form_fields )
		try:
			result = urlfetch.fetch( url = enkiDL_URL, payload = form_data, method = urlfetch.POST )
			if result.status_code == 200:
				token = result.content
				self.download_url = enkiDL_URL + '/download?token=' + str( token ) + '&item=' + str( item_to_download )
			else:
				self.error = 1
				return
		except urlfetch.DownloadError:
			self.error = 2
			return
