#!/usr/bin/python
from flask import Flask, request, render_template
from datetime import datetime, date, time
import time
import os
import re
import sqlite3
import pypureomapi
import ipaddress
import struct

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
        self.getLeases()

    def getDB(self):
        try:
            conn = sqlite3.connect('leaseDB.sqlite')
        except IOError:
            print "Error: can\'t find db file"
            exit(1)
        return conn

    def getLeases(self):
        o = pypureomapi.Omapi(dhcp_server_ip, port, KEYNAME, BASE64_ENCODED_KEY)
        ip4net = ipaddress.ip_network(unicode("192.168.22.0/24"))
        for addr in ip4net:
            ip = str(addr)
            try:
                info = dict(o.lookup_all(ip))
                mac = o.lookup_mac(ip) #easier to just let the api look this up than converting that bitch back
                info["hardware-address"] = mac
                lease = Lease(ip, info)
                self.writeDB(lease)
            except pypureomapi.OmapiErrorNotFound:
                print "%s is currently not assigned" % (ip,)
        return True


    def writeDB(self, lease):
        db = self.getDB()
        c = db.cursor()
        record = [lease.ip, lease.hostname, lease.start, lease.end, lease.mac, lease.state, lease.valid]
        print "inserting ", record
        try:
            with db:
                db.execute("INSERT INTO leases VALUES (?,?,?,?,?,?,?)", record)
        except sqlite3.IntegrityError:
            print "couldn't add ", record
        db.close()
        return True

    def readDB(self):
        db = self.getDB()
        c = db.cursor()
        c.execute("SELECT ip, hostname, start, end, mac, state, valid FROM leases")
        data = c.fetchall()
        db.close()
        return data

class Lease:
    """A lease from dhcpd, consistening of an IP, timeframe, etc."""
    #def __init__(self, state, ip, s, e, mac, hostname):
    def __init__(self, ip, info):
        states = {
            1 : "free",
            2 : "active",
            3 : "expired",
            4 : "released",
            5 : "abandoned",
            6 : "reset",
            7 : "backup",
            8 : "reserved",
            9 : "bootp",
        }
        self.ip = ip
        if "state" in info:
            stateInt, = struct.unpack('!I', info["state"])
        self.state = states[stateInt]
        print self.state
        startInt,  = struct.unpack('!I', info["starts"])
        self.start = datetime.fromtimestamp(startInt)
        print "START: ", self.start
        endInt,  = struct.unpack('!I', info["ends"])
        self.end = datetime.fromtimestamp(endInt)
        print "END: ", self.end
    	self.mac = info["hardware-address"]
        if "client-hostname" in info:
            self.hostname = info["client-hostname"]
        else:
            self.hostname = ""
        self.valid = self.isValid(self.start, self.end)
        #('state', '\x00\x00\x00\x01'),
        #('ip-address', '\xc0\xa8\x16#'),
        #('client-hostname'),
        #('hardware-address', '$\xe3\x14\x99\xa0N'),
        #('ends', 'Vu\xbd#'),
        #('starts', 'Vu\xa1\x03'),

    def isValid(self, start, end):
        now = datetime.fromtimestamp(time.time())
        if(now > start and now < end):
            return True
        else:
            return False

    def intToDate(self, i):
        d = datetime.fromtimestamp(i)
        #return d

    def toString(self):
        return(self.ip, self.start, self.end, self.mac, self.hostname, self.isValid)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
