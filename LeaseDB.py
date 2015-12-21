#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

import os
import sqlite3
import re
from datetime import datetime, date, time

class LeaseDB:
    """Imports the file dhcpd.leases from the operating system, and inserts it into an sqlite database for use by the application."""
    def __init__(self): #self, leases, db)
        self.leases = []
        self.db = self.getDB()
        self.parseFile()

    def getDB(self):
        try:
            conn = sqlite3.connect('leaseDB.sqlite')
        except IOError:
            print "Error: can\'t find db file"
            exit(1)
        return conn

    def parseFile(self):
        ip = start = end = mac = host = ''
        with open('dhcpd.leases', 'rw') as f:
            read_data = f.read()
            data = read_data.split('}') #break on } rather than newline, so we can slurp in the whole lease chunk
            for chunk in data:
                #Build out the lease object; one-per-chunk
                if re.search('^\s$', chunk):
                    break
                mIp = re.search('lease\s(\d+.\d+.\d+.\d+)\s', chunk)
                ip =  mIp.group(1)
                mStart = re.search('starts\s+\d+(.*?)\s+(.*?);', chunk)
                start = mStart.group(1) + mStart.group(2)
                mEnd = re.search('ends\s+\d+(.*?)\s+(.*?);', chunk)
                end = mEnd.group(1) + mEnd.group(2)
                mMac = re.search('hardware ethernet (([0-f][0-f]:){5}[0-f][0-f]);', chunk)
                mac = mMac.group(1)
                mHost = re.search('client-hostname\s+\W(\S+)";', chunk)
                if mHost: #cuz this one seems to be optional.
                    host = mHost.group(1)
                lease = Lease(ip, start, end, mac, host)
                if lease.valid is True:
                    self.writeDB(lease)
        return True

    def writeDB(self, lease):
        db = self.getDB()
        c = db.cursor()
        record = [lease.ip, lease.start, lease.end, lease.mac, lease.hostname, lease.valid]
        print "inserting ", record
        try:
            with db:
                db.execute("INSERT INTO leases VALUES (?,?,?,?,?,?)", record)
        except sqlite3.IntegrityError:
            print "couldn't add ", record
        db.close()
        return True

    def readDB(self):
        db = self.getDB()
        c = db.cursor()
        c.execute("SELECT ip,hostname FROM leases")
        a = c.fetchall()
        db.close()
        return a



class Lease:
    def __init__(self, ip, s, e, mac, hostname):
        self.ip = ip
        self.start = self.stringToDate(s)
        self.end =  self.stringToDate(e)
    	self.mac = mac
        self.hostname = hostname
        self.valid = self.isValid(self.start, self.end)

    def isValid(self, start, end):
        now = datetime.utcnow()
        if(now > start and now < end):
            return True
        else:
            return False

    def stringToDate(self, s):
        d = datetime.strptime(s, "%Y/%m/%d %H:%M:%S")
        return d

    def toString(self):
        return(self.ip, self.start, self.end, self.mac, self.hostname, self.isValid)
