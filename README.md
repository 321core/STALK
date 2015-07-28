# STALK (KETI server version. 125.x.x.52)

## Notice
now branch 'v0.1' has been created.
if you want to install stalk on your iot device, please download from v0.1 branch.
currently, major upgrade is undergoing on master branch. major features are:
  - load balancing between multiple channel servers
  - removing base64 conversion, direct transfer octet stream (**MUCH FASTER!!**)
  - independent channel namespace per user account
  - ~~remove dependency to 3rd party modules, ie.'requests'~~
  - using KEEP_ALIVE, much faster again.

v0.1 users can check the channel list at
  http://nini.duckdns.org:8100/admin/api/entry/
  (ID:admin, PWD:stalk)

## Run STALK Client

### Config setting on device (for example, RaspberryPi2)
  1. edit conf/settings.conf
    - INDEX_SERVER_BASE_URL = "*STALK MASTER SERVER*"
    - USER_NAME = "*YOUR ACCOUNT*"
    - PASSWORD = "*YOUR PASSWORD*" 

### Run software 
  1. run Stalk and connect to the Stalk service on the device (like a RaspberryPi2)
    - ./talk.py server VOLOSSH localhost 22
  1. to connect to stalked device from my device (like a laptop) :
    - ./talk.py client VOLOSSH 2222
  1. making connection through SSH, if the IoT serving SSH... on my device (the same device above laptop)
    - ssh pi@localhost -p 2222
