#!/bin/bash
set -x
sudo rm -rf /opt/index-server
sudo cp -r ../index-server /opt
sudo cp stalk-master.conf /etc/init
sudo service stalk-master restart
