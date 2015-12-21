#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

#Lease.py
from datetime import date, time
import time
import datetime
class Lease:
    def __init__(self, ip, s, e, mac, hostname):
        self.ip = ip
        self.start = self.stringToDate(s)
        self.end = self.stringToDate(e)
    	self.mac = mac
        self.hostname = hostname

    def isValid(self, start, end):
        now = datetime.datetime.now()
        if(now > start and now < end):
            return True
        else:
            return False

    def stringToDate(self, s):
        d = datetime.strptime(s, "%Y/%m/%d %H:%M:%S")
        print "d is a " + d.type()
        return d
