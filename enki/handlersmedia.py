import webapp2
import json
import cloudstorage as gcs
from google.appengine.api import memcache

import settings
import enki
import enki.libutil
from enki import textmessages as MSG


class HandlerMedia( enki.HandlerBase ):

	def get( self ):
		# Galleries of images and videos
		media_html = ''
		if enki.libutil.is_debug():
			with open( 'test\media.json', 'r' ) as f:
				json_file = f.read()
				f.close()
			media_json = json.loads( json_file )
			media_html = self.create_media_page( media_json )
		else:
			cache_data = memcache.get( 'media_html' )
			if cache_data is not None:
				media_html = cache_data
			else:
				try:
					f = gcs.open( settings.bucket + 'media.json' )
					json_file = f.read()
					f.close()
					media_json = json.loads( json_file )
					media_html = self.create_media_page( media_json )
					memcache.add( 'media_html' , media_html, 300 )
				except:
					pass
		# Display enlarged image
		url_image_previous = ''
		url_image_next = ''
		url_image_displayed = ''
		src_image_displayed = ''
		alt_image_displayed = ''
		caption_image_displayed = ''
		# if src_image_displayed is found, display the image. Otherwise abort.
		while not src_image_displayed:
			gallery = abs( int( self.request.get( 'g' ))) if self.request.get( 'g' ).isdigit() else -1
			image = abs( int( self.request.get( 'i' ))) if self.request.get( 'i' ).isdigit() else -1
			if gallery == -1 or image == -1:
				break
			media_json = ''
			if enki.libutil.is_debug():
				with open( 'test\media.json', 'r') as f:
					json_file = f.read()
					f.close()
				media_json = json.loads( json_file )
			else:
				try:
					f = gcs.open( settings.bucket + 'media.json' )
					json_file = f.read()
					f.close()
					media_json = json.loads( json_file )
				except:
					break
			if media_json and 'galleries_of_images' in media_json[ 'media' ]:
				galleries_of_images = media_json[ 'media' ][ 'galleries_of_images' ]
				if gallery >= len( galleries_of_images ):
					break
				else:
					gallery_of_images = galleries_of_images[ gallery ][ 'images' ]
					images_count = len( gallery_of_images )
					if image >= images_count or 'img_src' not in gallery_of_images[ image ] or not gallery_of_images[ image ][ 'img_src' ]:
						break
					else:
						if image == 0:
							previous_image = images_count - 1
						else:
							previous_image = image - 1
						if image < images_count - 1:
							next_image = image + 1
						else:
							next_image = 0
						url_image_previous = enki.libutil.get_local_url( 'media', { 'g':str( gallery ), 'i':str( previous_image )})
						url_image_next = enki.libutil.get_local_url( 'media', { 'g' : str( gallery ), 'i' : str( next_image )})
						url_image_displayed = gallery_of_images[ image ][ 'a_href' ]
						src_image_displayed = gallery_of_images[ image ][ 'a_href' ]	# use the higher resolution image
						alt_image_displayed = gallery_of_images[ image ][ 'img_alt' ]
						caption_image_displayed = gallery_of_images[ image ][ 'caption' ]
						break
			else:
				break
		# user intended to display an enlarged image but it couldn't be retrieved
		if self.request.query_string and not src_image_displayed:
			self.add_infomessage( 'info', MSG.INFORMATION(), MSG.IMAGE_UNAVAILABLE())

		self.render_tmpl( 'media.html', False,
						  active_menu = 'media',
						  url_image_previous = url_image_previous,
						  url_image_next = url_image_next,
						  url_image_displayed = url_image_displayed,
						  src_image_displayed = src_image_displayed,
						  alt_image_displayed = alt_image_displayed,
						  caption_image_displayed = caption_image_displayed,
						  media_html = media_html )

	@classmethod
	def create_media_page( cls, media_json ):
		# Create html for galleries of images and videos from json data
		HTML_HEADER = '''\n\t\t\t<h2>{header}</h2>\n'''
		HTML_GALLERY_TITLE = '''\n\t\t\t<h3>{gallery_title}</h3>\n'''
		HTML_GALLERY_DESCRIPTION = '''\t\t\t<h4>{gallery_description}</h4>\n'''
		HTML_ROW_START = '''\t\t\t<div class="row">\n'''
		HTML_ROW_END = '''\t\t\t</div>\n'''
		HTML_COL_START = '''\t\t\t\t<div class="col-xs-{col_width}">\n'''
		HTML_COL_END = '''\t\t\t\t</div>\n'''
		HTML_COL_EMPTY = HTML_COL_START + HTML_COL_END
		HTML_IMAGE = HTML_COL_START + \
					 '''\t\t\t\t\t<p><a href="{url}">\n\t\t\t\t\t<img alt="{img_alt}" src="{img_src}" width=100% class="img-rounded"></a><br><small>{caption}</small></p>\n''' + \
					 HTML_COL_END
		HTML_VIDEO = HTML_COL_START + \
					 '''\t\t\t\t\t<div class="embed-responsive embed-responsive-16by9">\n\t\t\t\t\t\t<iframe src="{url}" frameborder="0" allowfullscreen></iframe>\n\t\t\t\t\t</div>\n''' + \
					 HTML_COL_END
		media_html = ''
		media = media_json[ 'media' ]
		# Galleries of images
		if 'galleries_of_images' in media:
			galleries_of_images = media[ 'galleries_of_images' ]
			media_html += HTML_HEADER.format( header = media[ 'HEADER_IMAGES' ]) if media[ 'HEADER_IMAGES' ] else ''
			iter_gallery = 0
			for gallery in galleries_of_images:
				# set gallery title and description (if exist)
				media_html += HTML_GALLERY_TITLE.format( gallery_title = gallery[ 'title' ]) if gallery[ 'title' ] else ''
				media_html += HTML_GALLERY_DESCRIPTION.format( gallery_description = gallery[ 'description' ]) if gallery[ 'description' ] else ''
				# retrieve and set gallery images
				images = gallery[ 'images' ]
				if images:
					num_columns = int( gallery[ 'num_columns_override' ]) if gallery[ 'num_columns_override' ] else int( media[ 'NUM_COLUMNS_IMAGES_DEFAULT' ])
					column_width = 12 // num_columns # ensure the number of columns requested fit in the bootsrap grid https://getbootstrap.com/css/#grid
					num_images = len( images )
					num_rows = num_images // num_columns + ( num_images % num_columns > 0 )	# round up
					iter_image = 0
					iter_row = 0
					while iter_row < num_rows:
						# start a new row
						media_html += HTML_ROW_START
						iter_column = 0
						while iter_column < num_columns:
							if iter_image < num_images:
								# cell contains an image
								image = images[ iter_image ]
								if 'img_src' in image and image[ 'img_src' ]:
									url = enki.libutil.get_local_url( 'media', { 'g' : str( iter_gallery ), 'i' : str( iter_image )})
									media_html += HTML_IMAGE.format( col_width = column_width, url=url, img_alt = image[ 'img_alt' ], img_src = image[ 'img_src' ], caption = image[ 'caption' ])
								else:
									# blank cell
									media_html += HTML_COL_EMPTY.format( col_width = column_width )
								iter_image += 1
							else:
								# blank cell
								media_html += HTML_COL_EMPTY.format( col_width = column_width )
							iter_column += 1
						# end row
						media_html += HTML_ROW_END
						iter_row += 1
				iter_gallery += 1
		# Galleries of videos
		if 'galleries_of_videos' in media:
			galleries_of_videos = media[ 'galleries_of_videos' ]
			media_html += HTML_HEADER.format( header = media[ 'HEADER_VIDEOS' ]) if media[ 'HEADER_VIDEOS' ] else ''
			for gallery in galleries_of_videos:
				# set gallery title and description (if exist)
				media_html += HTML_GALLERY_TITLE.format( gallery_title = gallery[ 'title' ]) if gallery[ 'title' ] else ''
				media_html += HTML_GALLERY_DESCRIPTION.format( gallery_description = gallery[ 'description' ]) if gallery[ 'description' ] else ''
				# retrieve and set gallery videos
				videos = gallery[ 'videos' ]
				if videos:
					num_columns = int( gallery[ 'num_columns_override' ]) if gallery[ 'num_columns_override' ] else int( media[ 'NUM_COLUMNS_VIDEOS_DEFAULT' ])
					column_width = 12 // num_columns # ensure the number of columns requested fit in the bootsrap grid https://getbootstrap.com/css/#grid
					num_videos = len( videos )
					num_rows = num_videos // num_columns + ( num_videos % num_columns > 0 )    # round up
					iter_video = 0
					iter_row = 0
					while iter_row < num_rows:
						# start a new row
						media_html += HTML_ROW_START
						iter_column = 0
						while iter_column < num_columns:
							if iter_video < num_videos:
								# cell contains an image
								video = videos[ iter_video ]
								if video[ 'iframe_src' ]:
									media_html += HTML_VIDEO.format( col_width = column_width, url = video[ 'iframe_src' ])
								else:
									# blank cell
									media_html += HTML_COL_EMPTY.format( col_width = column_width )
								iter_video += 1
							else:
								# blank cell
								media_html += HTML_COL_EMPTY.format( col_width = column_width )
							iter_column += 1
						# end row
						media_html += HTML_ROW_END
						iter_row += 1

		return media_html

	@classmethod
	def create_media_image_data( cls, media_json ):
		media = media_json[ 'media' ]
		galleries_images = {}
		if 'galleries_of_images' in media:
			iterator_gallery = 0
			for gallery in media[ 'galleries_of_images' ]:
				for image in gallery[ 'images' ]:
					galleries_images[ iterator_gallery ].append( image[ 'a_href' ] )
				iterator_gallery += 1

routes_media = [ webapp2.Route( '/media', HandlerMedia, name = 'media' )]
