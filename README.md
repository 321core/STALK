# STALK

## Notice
now branch 'v0.1' has been created.
if you want to install stalk on your iot device, please download from v0.1 branch.
currently, major upgrade is undergoing on master branch. major features are:
  - load balancing between multiple channel servers
  - removing base64 conversion, direct transfer octet stream
  - independent channel namespace per user account
  - *remove dependency to 3rd party modules*, ie.'requests'
  - 
v0.1 users can check the channel list at
  http://nini.duckdns.org:8100/admin/api/entry/
  (ID:admin, PWD:stalk)

## Run STALK

  1. edit conf/settings.conf
    - INDEX_SERVER_BASE_URL = "*STALK MASTER SERVER*"
    - USER_NAME = "*YOUR ACCOUNT*"
    - PASSWORD = "*YOUR PASSWORD*" 

  2. run stalk as server
    - ./talk.py server VOLOSSH localhost 22
  
  3. access stalked device:
    - ./talk.py client VOLOSSH 2222

and making connection through SSH, if the IoT serving SSH... 
  4) ssh pi@localhost -p 2222
