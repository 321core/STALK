# STALK

## Notice
now branch 'v0.1' has been created.
if you want to install stalk on your iot device, please download from v0.1 branch.
currently, major upgrade is undergoing on master branch. major features are:
  - load balancing between multiple channel servers
  - removing base64 conversion, direct transfer octet stream
  - independent channel namespace per user account

v0.1 users can check the channel list at
  http://nini.duckdns.org:8100/admin/api/entry/
  (ID:admin, PWD:stalk)

## Run STALK >

the connection to STALK Server

  1) python app.py bind VOLOSSH 2222

and making connection through SSH, if the IoT serving SSH... 

  2) ssh pi@localhost -p 2222

