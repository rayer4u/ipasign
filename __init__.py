#coding:utf-8
from django.conf import settings
from os.path import splitext,join,dirname
import os
import ConfigParser

PACKAGE_DIR="ipasign"
UPLOAD_DIR="upload"
PROFILES_DIR=join(settings.MEDIA_ROOT, "profiles")
CERTS={}
PUBLISH_URL="http://127.0.0.1:8000/ipapub/"

for root, dirs, files in os.walk(PROFILES_DIR):
    if root == PROFILES_DIR:
        for dir in dirs:
            CERTS[dir] = ''
    else:
        root = root[len(PROFILES_DIR)+1:]
        if root not in CERTS:
            continue
        if 'cert.cfg' not in files:
            continue
        
        cf = ConfigParser.SafeConfigParser()    
        cf.read(join(PROFILES_DIR, root, 'cert.cfg'))
        if 'certification' in cf.sections():
            CERTS[root] = dict(cf.items('certification'))

print('certifications')
print(CERTS)

