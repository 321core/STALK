# How To Install

## Ubuntu
1. wget https://raw.githubusercontent.com/321core/STALK-INSTALL/master/install-ubuntu.sh
2. sh install-ubuntu.sh

## OS-X
1. First, git should be installed on your mac.
2. wget https://raw.githubusercontent.com/321core/STALK-INSTALL/master/install-osx.sh
3. sh install-osx.sh

## Rasberry PI
1. wget https://raw.githubusercontent.com/321core/STALK-INSTALL/master/install-rasberry.sh
2. sh install-rasberry.sh

## Cygwin
1. First, the following items must be installed on Cygwin
       * python
       * git
       * wget
       * cygrunsrv

2. wget https://raw.githubusercontent.com/321core/STALK-INSTALL/master/install-cygwin.sh
3. sh install-cygwin.sh
4. run Cygwin terminal as Administrator and type this:
      ```
       cygrunsrv -I stalk -p /usr/bin/python2.7.exe -a /usr/share/stalk/service/talkd.py
       cygrunsrv -S stalk
      ```

5. now, stalk is installed as windows service. (you can quit Cygwin terminal now)
   You can check it by entering the url of 'http://localhost:8900' in the Chrome browser. 
   If pop up a page correctly, stalk is successfully installed.


# How To Use

Coming Soon...
