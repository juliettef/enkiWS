import os

version = raw_input( 'Upload ? version nr. or N ')
if version.isdigit():
	os.system( r'"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud" config set app/num_file_upload_processes 1' )	# Issue 1036 workaround https://code.google.com/p/google-cloud-sdk/issues/detail?id=1036
	os.system( r'"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud" config set project enkisoftware-webservices' )
	# os.system( r'"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud" app create --region=us-central')
	os.system( r'"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud" app deploy app.yaml dos.yaml index.yaml cron.yaml --version={v} --promote -q'.format( v = version ))
else:
	print 'Aborted'
