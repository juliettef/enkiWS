import webapp2
import json
import cloudstorage as gcs
from google.appengine.api import memcache

import settings
import enki
import enki.libutil


GALLERIES_MAX = 100
IMAGES_PER_GALLERY_MAX = 200


class HandlerMedia( enki.HandlerBase ):

	def get( self ):
		gallery = abs( int( self.request.get( 'g' ))) if self.request.get( 'g' ) else 0
		gallery = gallery if gallery <= GALLERIES_MAX else 0
		image = abs( int( self.request.get( 'i' ))) if self.request.get( 'i' ) else 0
		image = image if image <= IMAGES_PER_GALLERY_MAX else 0

		media_html = ''
		if enki.libutil.is_debug():
			with open( 'test\media.json', 'r' ) as f:
				json_file = f.read()
				f.close()
			media_html = self.create_media_page( json.loads( json_file ))
		else:
			cache_data = memcache.get( 'media_html' )
			if cache_data is not None:
				media_html = cache_data
			else:
				try:
					f = gcs.open( settings.bucket + 'media.json')
					json_file = f.read()
					f.close()
					media_html = self.create_media_page( json.loads( json_file ))
					memcache.add( 'media_html' , media_html, 300 )
				except:
					pass

		self.render_tmpl( 'media.html', False,
						  active_menu = 'media',
						  g = gallery,
						  i = image,
						  media_html = media_html )

	@classmethod
	def create_media_page( cls, media_json ):
		# galleries
		NUM_COLUMNS_DEFAULT = 3
		HTML_GALLERY_TITLE = '''\t\t\t<h3>{gallery_title}</h3>\n'''
		HTML_GALLERY_DESCRIPTION = '''\t\t\t<h4>{gallery_description}</h4>\n'''
		HTML_IMAGES_ROW_START = '''\t\t\t<div class="row">\n'''
		HTML_IMAGES_ROW_END = '''\t\t\t</div>\n'''
		HTML_IMAGE = '''\t\t\t\t<div class="col-xs-{col_width}">\n''' + '''\t\t\t\t\t<p><a href="{url}">\n''' + \
		'''\t\t\t\t\t<img alt="{img_alt}" src="{img_src}" width=100% class="img-rounded"></a></p>\n''' + '''\t\t\t\t</div>\n'''
		HTML_IMAGE_NONE = '''\t\t\t\t<div class="col-xs-{col_width}">\n''' + '''\t\t\t\t</div>\n'''
		media_html = ''
		galleries = media_json[ 'galleries' ]
		if galleries:
			iter_gallery = 0
			for gallery in galleries:
				# set gallery title and description (if exist)
				media_html += HTML_GALLERY_TITLE.format( gallery_title = gallery[ 'title' ]) if gallery[ 'title' ] else ''
				media_html += HTML_GALLERY_DESCRIPTION.format( gallery_description = gallery[ 'description' ]) if gallery[ 'description' ] else ''
				# retrieve and set gallery images
				images = gallery[ 'images' ]
				if images:
					num_columns = int( gallery[ 'num_columns' ]) if gallery[ 'num_columns' ] else NUM_COLUMNS_DEFAULT
					column_width = 12 // num_columns # ensure the number of columns requested fit in the bootsrap grid https://getbootstrap.com/css/#grid
					num_images = len(images)
					num_rows = num_images // num_columns + ( num_images % num_columns > 0 )	# round up
					iter_image = 0
					iter_row = 0
					while iter_row < num_rows:
						# start a new row
						media_html += HTML_IMAGES_ROW_START
						iter_column = 0
						while iter_column < num_columns:
							if iter_image < num_images:
								# cell contains an image
								image = images[ iter_image ]
								url = enki.libutil.get_local_url( 'media', { 'g' : str( iter_gallery ), 'i' : str( iter_image )})
								media_html += HTML_IMAGE.format( col_width = column_width, url=url, img_alt = image[ 'img_alt' ], img_src = image[ 'img_src' ]) # gallery_num = iter_gallery, image_num = iter_image,
								iter_image += 1
							else:
								# blank cell
								media_html += HTML_IMAGE_NONE.format( col_width = column_width )
							iter_column += 1
						# end row
						media_html += HTML_IMAGES_ROW_END
						iter_row += 1
				else:
					media_html += '''<p class="text-info">No images available.</p>'''
				# increment gallery index
				iter_gallery += 1
		else:
			media_html = '''<p class="text-info">No galleries available.</p>'''
		return media_html


routes_media = [ webapp2.Route( '/media', HandlerMedia, name = 'media' )]
