#!/usr/bin/python
from flask import Flask, request, render_template
from datetime import datetime, date, time
import os
import re
import sqlite3
import pypureomapi


##Server settings
KEYNAME="sheatestkey"
BASE64_ENCODED_KEY="OIag01OLUi8OSOSwX1hWzw=="
dhcp_server_ip="192.168.22.1"
port = 7911 # Port of the omapi service

app = Flask(__name__)

###MAIN App ###
@app.route("/")
def showLeases():
    ldb = LeaseDB()
    print ldb
    addrs = ldb.readDB()
    for tup in addrs:
        x, y = tup
    return render_template("network.html", addrs = addrs)


@app.route("/revoke", methods=["POST"])
def revoke():
    #lease = request.args.getlist('addr')[0].upper()
    print "revoking", lease[0]
    #Revoke the current lease provided on the request from the webservice
    #Options:

@app.route("/extend", methods=["POST"])
def extend():
    #lease = request.args.getlist('addr')[0].upper()
    print "extending", lease[0]
    #Extend the current lease provided on the request from the webservice
    #Options:

@app.route("/list", methods=["POST"])
def list():
    lease = request.form.getlist('ip')[0]
    print "listing", lease
    o = pypureomapi.Omapi("192.168.22.1",7911, 'sheatestkey', "OIag01OLUi8OSOSwX1hWzw==")
    try:
        mac = o.lookup_mac(lease)
        print "IP assigned ", lease, mac
        return render_template("list.html", lease = lease, mac = mac)
    except pypureomapi.OmapiErrorNotFound:
        print "%s is currently not assigned" % (lease,)



class LeaseDB:
    """Collects the dhcp info and inserts it into an sqlite database for use by the application."""
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
        with open('dhcpd.leases', 'rw') as f: #TODO: this will have to point to the "real file" on disk
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
        data = c.fetchall()
        db.close()
        return data



class Lease:
    """A lease from dhcpd, consistening of an IP, timeframe, etc."""
    def __init__(self, ip, s, e, mac, hostname):
        self.ip = ip
        self.start = self.stringToDate(s)
        self.end =  self.stringToDate(e)
    	self.mac = mac
        self.hostname = hostname
        self.valid = self.isValid(self.start, self.end)
        #('state', '\x00\x00\x00\x01'),
        #('ip-address', '\xc0\xa8\x16#'),
        #('client-hostname'),
        #('hardware-address', '$\xe3\x14\x99\xa0N'),
        #('ends', 'Vu\xbd#'),
        #('starts', 'Vu\xa1\x03'),

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
