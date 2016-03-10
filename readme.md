# enkiWS


## enki Web Services for Games on Python Google App Engine

A permissively licensed Python web service for games developers. enkiWS is a library for setting up a website and ancillary services for games on Google App Engine. GAE was chosen as the platform since it provides a low cost scalable solution.

Online demo *- may be out of sync with the source code -* https://enkisoftware-webservices.appspot.com


## Status

This is a work in progress and not yet ready for production use.  
__[ NEW in v0.5 ] REST API Friends and data store__


## Functionality

### Current

* User Accounts - email, display name
* Login through OAuth & OpenID providers - Valve's Steam, Facebook, Google, Twitter
* Forums
* Localisation - English & French implemented
* Online store
    * Payment provider [FastSpring](http://www.fastspring.com/)  
    * Licence key generation and activation
    * Store emulator
* Friends
    * Search by display name and invite
    * Message alert for friend invite
* REST API
    * Authentication (account and game key)
    * Friends list
    * Data Store   

### Intended for release 1.0.0 
    
* Admin tools
* Installation and usage documentation
* REST API improvements:
    * datastore limits
    * online datastore explorer
    * authentication timeout control
    * datastore object modifcation time and lifetime controls

### Intended for  release 1.x.x

* User roles
* Issues reporting and tracking
* Static blogging tool integration
* Integration [presskit() for GAE](http://www.enkisoftware.com/devlogpost-20140123-1-Presskit_for_Google_App_Engine.html), 
[distribute()](https://dodistribute.com/), 
[Promoter](https://www.promoterapp.com/)


## Instructions

### Running the enkiWS website locally

You can run enkiWS on your machine using the Google App Engine Launcher:  

1. Download & extract [enkiWS](https://github.com/juliettef/enkiWS/archive/master.zip)  
1. Download & install [Google App Engine with python 2.7](https://cloud.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python)  
1. Run GoogleAppEngineLauncher:  
    1. Choose File > Add Existing Application.  
    1. Set the Application Path to the directory enkiWS was extracted to (where the app.yaml file resides)  
    1. Select Add - enkiWS is added to the list of project.
1. In the GAE Launcher select enkiWS, press Run, then press Browse - the enkiWS site opens in your browser.  

### Debugging enkiWS locally using PyCharm CE

A *.idea* directory is included in the project. It is preconfigured to enable the use of the free Pycharm Community Edition as an IDE for debugging python GAE code, with one modification to make manually. 
Note: if you'd prefer to configure PyCharm CE yourself see the [detailed tutorial](http://www.enkisoftware.com/devlogpost-20141231-1-Python_Google_App_Engine_debugging_with_PyCharm_CE.html). Otherwise follow the simplified instructions below:

1. Ensure you have python 2.7 and Google app Engine installed. To check it works, try running the enkiWS website locally.  
1. Download and install [Pycharm CE](https://www.jetbrains.com/pycharm/download/)  
1. Start Pycharm and open the project - set the project location to the directory enkiWS was extracted to (the parent folder of the .idea directory).  
1. A *Load error: undefined path variables*, *GAE_PATH is undefined* warning is displayed. To fix it see the [PyCharm tutorial Method A step 5 onwards](http://www.enkisoftware.com/devlogpost-20141231-1-Python_Google_App_Engine_debugging_with_PyCharm_CE.html#pathvariable).
1. Note: if you get a message stating *No Python interpreter configured for the project*, go to File > Settings > Project:enkiWS > Project Interpreter and set the project interpreter to point to the location of *python.exe* on your computer (..\Python27\python.exe).
1. Restart PyCharm
1. You can now run / debug the project from PyCharm using one of the configurations provided (e.g. *GAE_config*).  

### Enabling OAuth login with Google, Facebook, Twitter

To set up Open Authentication, you need to configure secrets.py:  

1. Follow the instructions in [example_secrets.txt](https://github.com/juliettef/enkiWS/blob/master/example_secrets.txt)  
1. Go to the login page: you will see the login buttons for the providers you've set up. Clicking on those buttons creates and account &/or logs you into enkiWS using OAuth.  

Notes:  

 - Valve's Steam is always available since it doesn't require a client Id nor secret.  
 - When you navigate the enkiWS site you will no longer see the warning message stating that the setup is incomplete.  

### REST API

#### Overview

The rest api provides a mechanism for developers to create games, apps and websites which interact with users data.

 - Protocol: HTTPS
 - Request method: POST  
 - Request and response format: JSON  
 - Request and result parameters format: String unless specified otherwise  

The REST API security mechanism is to use HTTPS for as the protocol combined with user authentication (detailed later). Currently we do not implement a client secret or other application verification mechanism since any global key available on a client machine can be stolen - thus the REST API is deliberatly limited in the scope of the changes it can make.

#### User Authentication via a Connect Code

EnkiWS encourages the use of OAUTH so users may not have a password, and having users type their password into an unknown application is potentially risky. So we've developed an approach which allows users to authenticate an app by getting a temporary short code which they use to login, and the app exchanges this for a long lasting authentication token. Users can remove authentication priviledges using their profile page.

1. User goes to their profile page and requests a 'Connect Code'
1. EnkiWS displays the code e.g. 'Q354D'
1. User types their full displayname and connect code into the app login screen
1. App uses the /api/v1/connect API to login
1. App receives an auth_token and user_id, which it can use for further API requests. This can be stored on disk and re-used if required
 
#### The datastore

The datastore provides a named JSON object store for users with private, friends, and public read access control. The Google App Engine backend limits the per-object size to around 1 megabyte, however we intend to add per user limits with product based increases (for example you could configure enkiWS to give all registered users a small amount of storage, but users with a given product several megabytes).

#### Example REST API uses

Once an app has authenticated the user, it can use the auth_token and user_id to perform further API queries, and use the datastore to store user data.

- Check if a user has purchased a game
    1. Use /api/v1/ownsproducts and request for your game
- Store and find out if friends are online
    1.  Get the list of friends with /api/v1/friends
    1. Use the datastore /api/v1/datastore/set to store a JSON structure containing the details you need for friend status (online, ingame, IP address and ports for chat or game connect etc.). Make sure to have "read_access" : "friends"
    1. Use /api/v1/datastore/getlist with "read_access" : "friends" to get a list of the status for each user_id
- Invite a friend to play a game
    1. We discover the friend status as above, ensuring that the datastore entry has an IP address and port for messages to be passed. The game can then connect via this address and send an invite
- Get a list of open servers
    1. Again using the datastore we store the details required (server name, IP address, port, game details) to connect to the game with "read_access" : "public"
    1. Clients can pull this list using /api/v1/datastore/getlist with "read_access" : "public", and ping the servers for online status

#### API Functionality table

| URL | Functionality | Request Parameters | Request example | Response Parameters | Response example (success) |  
| --- | --- | --- | --- | --- | --- |  
| /api/v1/connect | User connect | user_displayname, code | {"user_displayname":"Silvia#2702","code":"Q354D"} | user_id, auth_token, success, error | {"user_id":"5066549580791808","auth_token":"kDfFg1F6KkQu9E1yNaPhcvo46YVNQF8dz9AruNdw3S","success":true,"error":""} |  
| /api/v1/logout | User logout | user_id, auth_token | {"user_id":"5066549580791808","auth_token":"kDfFg1F6KkQu9E1yNaPhcvo46YVNQF8dz9AruNdw3S"} | success, error | {"success":true,"error":""} |  
| /api/v1/authvalidate | Validate user | user_id, auth_token | {"user_id":"5066549580791808","auth_token":"kDfFg1F6KkQu9E1yNaPhcvo46YVNQF8dz9AruNdw3S"} | user_displayname, success, error | {"user_displayname":"Silvia#2702","success":true,"error":""} |  
| /api/v1/ownsproducts | List products activated by user | user_id, auth_token | {"user_id":"5066549580791808","auth_token":"kDfFg1F6KkQu9E1yNaPhcvo46YVNQF8dz9AruNdw3S"} | products_owned (list of strings), success, error | {"products_owned":["product_a","product_b","product_c"],"success":true,"error":""} |  
| /api/v1/ownsproducts | List confirming products activated by user | user_id, auth_token, products (list of strings) | {"user_id":"5066549580791808","auth_token":"kDfFg1F6KkQu9E1yNaPhcvo46YVNQF8dz9AruNdw3S","products":["product_b","product_c","product_d"]} | products_owned (list of strings), success, error | {"products_owned":["product_b","product_c"],"success":true,"error":""} |  
| /api/v1/friends | List user's friends | user_id, auth_token | {"user_id":"5066549580791808","auth_token":"kDfFg1F6KkQu9E1yNaPhcvo46YVNQF8dz9AruNdw3S"} | friends user_id and displayname (list of dictionaries of strings) , success, error | {"friends":[{"user_id":"4677872220372992","displayname":"Toto#2929"},{"user_id":"6454683010859008","displayname":"Ann#1234"}],"success":true,"error":""} |  
| /api/v1/datastore/set | Create / update user's data filtered by app id and data type | user_id, auth_token, app_id, data_key data_payload (JSON), read_access | {"user_id":"5066549580791808","auth_token":"kDfFg1F6KkQu9E1yNaPhcvo46YVNQF8dz9AruNdw3S","app_id":"product_a","data_key":"settings","data_payload": json.loads("{"colour":"green", "shape":"tetraedron", "size":"0.5"}"),"read_access":"friends"} | success, error | {"success":true,"error":""} |  
| /api/v1/datastore/get | Get user's data filtered by app id and data type | user_id, auth_token, app_id, data_key | {"user_id":"5066549580791808","auth_token":"kDfFg1F6KkQu9E1yNaPhcvo46YVNQF8dz9AruNdw3S","app_id":"product_a","data_key":"settings"} | data_payload (JSON), success, error | {"data_payload":[{"colour":"green","shape":"tetraedron","size":"0.5"}],"success":true,"error":""} |  
| /api/v1/datastore/getlist | Get user's friend's data filtered by app id, data type and friends' read_access setting to 'friends' | user_id, auth_token, app_id, data_key, read_access (="friends") | {"user_id":"5066549580791808","auth_token":"kDfFg1F6KkQu9E1yNaPhcvo46YVNQF8dz9AruNdw3S","app_id":"product_a","data_key":"settings","read_access":"friends"} | data_payloads (list of dictionaries (user_id, data_payload (JSON))), success, error | {"data_payloads":[{"user_id":"4677872220372992","data_payload":{"colour":"blue","shape":"cube","size":"0.8"}},{"user_id":"6454683010859008","data_payload":{"colour":"red","shape":"sphere","size":"0.4"}}],"success":true,"error":""} |  
| /api/v1/datastore/getlist | Get data filtered by app id, data type and user's read_access setting to 'public'| user_id, auth_token, app_id, data_key, read_access (="public") | {"user_id":"5066549580791808","auth_token":"kDfFg1F6KkQu9E1yNaPhcvo46YVNQF8dz9AruNdw3S","app_id":"product_a","data_key":"settings","read_access":"public"} | data_payloads (list of dictionaries (user_id, data_payload (JSON))), success, error | {"data_payloads":[{"user_id":"4537134732017664","data_payload":{"colour":"yellow","shape":"cube","size":"0.3"}},{"user_id":"6218562888794112","data_payload":{"colour":"teal","shape":"tetraedon","size":"1.9"}},{"user_id":"6368543146770432","data_payload":{"colour":"black","shape":"sphere","size":"0.2"}}],"success":true,"error":""} |  
| /api/v1/datastore/del | Delete user's data filtered by app id and data type | user_id, auth_token, app_id, data_key | {"user_id":"5066549580791808","auth_token":"kDfFg1F6KkQu9E1yNaPhcvo46YVNQF8dz9AruNdw3S","app_id":"product_a","data_key":"settings"} | success, error | {"success":true,"error":""} |  

#### API Errors

| Error messages | Description | Response example (failure) |  
| --- | --- | --- |  
| Invalid request | Invalid or missing request parameters | {"success":false,"error":"Invalid request"} |  
| Unauthorised | user could not be authenticated. Connect request: user_displayname/code invalid. Other requests: user_id/auth_token invalid | {"success":false,"error":"Unauthorised"} |  
| Not Found | No data found | {"success":false,"error":"Not found"} |  


## Frequently Asked Questions

### Why use Google App Engine?

Small games developers like ourselves typically have very irregular backend requirements - website and service traffic are typically relatively low, but spike when there's a new release or if some content goes viral. Google App Engine (GAE) provides a low cost scalable solution for this scenario. For more information see our article on [Implementing a static website in Google App Engine](http://www.enkisoftware.com/devlogpost-20130823-1-Implementing_a_static_website_in_Google_App_Engine.html) or [Wolfire's article on GAE for indie developers](http://blog.wolfire.com/2009/03/google-app-engine-for-indie-developers/) as well as [Wolfire's article on hosting the Humble Indie Bundle](http://blog.wolfire.com/2010/06/Hosting-the-Humble-Indie-Bundle-on-App-Engine).

Note that if you don't want to use Google App Engine, you can use [the open source AppScale](http://www.appscale.com/) environment to run this code on other platforms.

### Why Python?

Python is sufficiently popular and easy to use that it made a convenient choice of language from those available on Google App Engine. We considered Google's Go language, but although it has many benefits we thought it would be less widely known in the game development community.

### EU Cookie law?
According to the [EU legislation on cookies](http://ec.europa.eu/ipg/basics/legal/cookies/index_en.htm#section_2), the cookies used in enkiWS are exempt from consent.


## Credits

Developed by [Juliette Foucaut](http://www.enkisoftware.com/about.html#juliette) - [@juliettef](https://github.com/juliettef)  
Architecture and OAuth implementation - [Doug Binks](http://www.enkisoftware.com/about.html#doug) - [@dougbinks](https://github.com/dougbinks)  
Testing - [Andy Binks](http://www.enkisoftware.com/about.html#andy)  
Testing - Sven Bentlage - [@sbe-dev](https://github.com/sbe-dev)  
Localisation - Charlotte Foucaut - [@charlf](https://github.com/charlf)


## Licence

zlib - see [licence.txt](https://github.com/juliettef/enkiWS/blob/master/licence.txt)
