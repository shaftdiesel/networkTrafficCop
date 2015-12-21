import pypureomapi
import ipaddress
import struct
from datetime import datetime

##Server settings
KEYNAME="sheatestkey"
BASE64_ENCODED_KEY="OIag01OLUi8OSOSwX1hWzw=="
dhcp_server_ip="192.168.22.1"
port = 7911 # Port of the omapi service

state = {
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

#Sample Leases

def add(o, leases):
    for ip in leases.keys():
        try:
            o.add_host(ip, leases[ip])
            print "added ", ip, "successfully"
        except pypureomapi.OmapiError, err:
            print "an error occured: %r" % (err,)

def ls(o, ip):
    try:
        infoList = o.lookup_all(ip)
        for x in infoList:
            (key, value) = x
            #if key == 'client-hostname' or key == 'state' or key == 'hardware-address' or key == 'starts' or key == 'ends':
                #print x

            if key == 'state':
                stateValue = struct.unpack('!I', value)
                print "State: ", key, stateValue
            if key == 'starts':
                (startValue,) = struct.unpack('!I', value)
                s = datetime.fromtimestamp(startValue)
                print "starts: ", startValue, s
            if key == 'ends':
                (endValue, ) = struct.unpack('!I', value)
                e = datetime.fromtimestamp(endValue)
                print "ends: ", endValue, e

    except pypureomapi.OmapiErrorNotFound:
        print "%s is currently not assigned" % (ip,)

def remove(o, leases):
    for ip in leases.keys():
        try:
            o.del_host(ip)
            print "removed ", ip, "successfully"
        except pypureomapi.OmapiErrorNotFound:
            print "%s is currently not assigned" % (ip,)

o = pypureomapi.Omapi(dhcp_server_ip,port, KEYNAME, BASE64_ENCODED_KEY)
#add(o, leases)
ip4net = ipaddress.ip_network(unicode("192.168.22.0/24"))
for addr in ip4net:
    #print "IP: ", addr
    ls(o,str(addr))
