#!/usr/bin/python
from flask import Flask, request, render_template, flash, redirect, url_for
from datetime import datetime, date, time
import time
import os
import re
import sqlite3
import pypureomapi
import ipaddress
import struct


app = Flask(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'leaseDB.sqlite'),
    DEBUG=True,
    SECRET_KEY='horsefeathers',
    USERNAME='admin',
    PASSWORD='default',
))

###MAIN App ###
@app.route("/")
def showLeases():
    ldb = LeaseDB()
    addrs = ldb.readDB()
    return render_template("network.html", addrs = addrs)


@app.route("/revoke", methods=["POST"])
def revoke():
    ip, = request.form.getlist('ip')
    flash("revoked ip")
    #Revoke the current lease provided on the request from the webservice
    #d = dhcpdServer()
    #d.conn.del_host(ip)
    return redirect(url_for('showLeases'))

@app.route("/extend", methods=["POST"])
def extend():
    #lease = request.args.getlist('addr')[0].upper()
    print "extending", lease[0]
    #Extend the current lease provided on the request from the webservice
    #Options:

@app.route("/list", methods=["POST"])
def list():
    ip, = request.form.getlist('ip')
    print "listing", ip
    o = pypureomapi.Omapi("192.168.22.1",7911, 'sheatestkey', "OIag01OLUi8OSOSwX1hWzw==")
    try:
        mac = o.lookup_mac(ip)
        print "IP assigned ", ip, mac
        return render_template("list.html", ip = ip, mac = mac)
    except pypureomapi.OmapiErrorNotFound:
        print "%s is currently not assigned" % (ip,)

class dhcpdServer:
    """Sets up a connection to the dhcpd sever using Omapi and returns a list of leases"""
    def __init__(self):
        #Dhcp server
        self.KEYNAME="sheatestkey"
        self.BASE64_ENCODED_KEY="OIag01OLUi8OSOSwX1hWzw=="
        self.dhcp_server_ip="192.168.22.1" #/meh
        self.port = 7911
        self.conn = self.getConnection()

        self.leases = []
        self.getLeases()

    def getConnection(self):
        return pypureomapi.Omapi(self.dhcp_server_ip, self.port, self.KEYNAME, self.BASE64_ENCODED_KEY)

    def getLeases(self):
        d = dhcpdServer()
        #scan the entire /24 network
        ip4net = ipaddress.ip_network(unicode("192.168.22.0/24"))
        for addr in ip4net:
            ip = str(addr)
            try:
                info = dict(d.conn.lookup_all(ip))
                #easier to just let the api look this up, rather than converting that bitch back from network byte order
                mac = d.conn.lookup_mac(ip)
                info["hardware-address"] = mac
                lease = Lease(ip, info)
                self.leases.append(lease)
            except pypureomapi.OmapiErrorNotFound:
                print "%s is currently not assigned" % (ip,)
        return True


class LeaseDB:
    """sqlite database storing lease info."""
    def __init__(self):
        self.db = self.getDB()
        #if not app.config['DEBUG']:
        #self.initDB()

    def getDB(self):
        try:
            conn = sqlite3.connect(app.config['DATABASE'])
        except IOError:
            print "Error: can\'t find db file"
            exit(1)
        return conn

    def initDB(self):
        db = self.getDB()
        c = db.cursor()
        SCHEMA = "CREATE TABLE leases \
            (ip varchar(255) PRIMARY KEY, \
            hostname varchar(255), \
            start varchar(255), \
            end varchar(255), \
            mac varchar(255), \
            state varchar(255), \
            valid boolean);"
        try:
            with db:
                db.execute(SCHEMA)
                return True
        except sqlite3.IntegrityError:
            print "Couldn't initialize DB"
        return False
        db.close()

    def readDB(self):
        db = self.getDB()
        c = db.cursor()
        c.execute("SELECT ip, hostname, start, end, mac, state, valid FROM leases ")
        data = c.fetchall()
        db.close()
        return data

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
        startInt,  = struct.unpack('!I', info["starts"])
        self.start = datetime.fromtimestamp(startInt)
        endInt,  = struct.unpack('!I', info["ends"])
        self.end = datetime.fromtimestamp(endInt)
    	self.mac = info["hardware-address"]
        if "client-hostname" in info:
            self.hostname = info["client-hostname"]
        else:
            self.hostname = ""
        self.valid = self.isValid(self.start, self.end)

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
    app.run(host='0.0.0.0', debug=app.config['DEBUG'])
