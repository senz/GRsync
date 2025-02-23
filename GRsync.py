#!/usr/bin/python -u
# -*- coding: utf-8 -*-

from urllib.request import Request, URLError, urlopen
import sys
import json
import argparse
from argparse import RawTextHelpFormatter
import socket
import re
import os

# remember the ending "/"
# eg: PHOTO_DEST_DIR = "/home/user/photos/"
PHOTO_DEST_DIR = ""

# GR_HOST is FIXED. DO NOT CHANGE!!
GR_HOST = "http://192.168.0.1/"
PHOTO_LIST_URI = "v1/photos"
GR_PROPS = "v1/props"
STARTDIR = ""
STARTFILE = ""
SUPPORT_DEVICE = ['RICOH GR II', 'RICOH GR III', 'RICOH GR IIIx']
DEVICE = "RICOH GR II"

def getDeviceModel():
    req = Request(GR_HOST + GR_PROPS)
    try:
        resp = urlopen(req)
        data = resp.read()
        props = json.loads(data)
        if props['errCode'] != 200:
            print("Error code: %d, Error message: %s" %
                  (props['errCode'], props['errMsg']))
            sys.exit(1)
        else:
            return props['model']
    except URLError as e:
        print("Unable to fetch device props from device")
        sys.exit(1)

def getBatteryLevel():
    req = Request(GR_HOST + GR_PROPS)
    try:
        resp = urlopen(req)
        data = resp.read()
        props = json.loads(data)
        if props['errCode'] != 200:
            print("Error code: %d, Error message: %s" %
                  (props['errCode'], props['errMsg']))
            sys.exit(1)
        else:
            return props['battery']
    except URLError as e:
        print("Unable to fetch device props from %s" % DEVICE)
        sys.exit(1)

def getPhotoList():
    req = Request(GR_HOST + PHOTO_LIST_URI)
    try:
        resp = urlopen(req)
        data = resp.read()
        photoDict = json.loads(data)
        if photoDict['errCode'] != 200:
            print("Error code: %d, Error message: %s" % (photoDict['errCode'], photoDict['errMsg']))
            sys.exit(1)
        else:
            photoList = []
            for dic in photoDict['dirs']:
                # check if this directory already exist in local PHOTO_DEST_DIR
                # if not, create one
                if not os.path.isdir(PHOTO_DEST_DIR+dic['name']):
                    os.makedirs(PHOTO_DEST_DIR+dic['name'])
                
                # generate the full photo list
                for file in dic['files']:
                    photoList.append("%s/%s" % (dic['name'], file ))
            return photoList
    except URLError as e:
        print("Unable to fetch photo list from %s" % DEVICE)
        sys.exit(1)
    
def getLocalFiles():
    fileList = []
    for (dir, _, files) in os.walk(PHOTO_DEST_DIR):
        for f in files:
            fileList.append(os.path.join(dir, f).replace(PHOTO_DEST_DIR, ""))
            
    return fileList

def fetchPhoto(photouri):
    try:
        if DEVICE == 'GR2':
            f = urlopen(GR_HOST+photouri)
        else: 
            f = urlopen(GR_HOST+PHOTO_LIST_URI+'/'+photouri)
        with open(PHOTO_DEST_DIR+photouri, "wb") as localfile:
            localfile.write(f.read())
        return True
    except URLError as e:
        return False

def shutdownGR():
    req = Request("http://192.168.0.1/v1/device/finish")
    req.add_header('Content-Type', 'application/json')
    response = urlopen(req, b"{}")

def downloadPhotos(isAll):
    print("Fetching photo list from %s ..." % DEVICE)
    photoLists = getPhotoList()
    localFiles = getLocalFiles()
    count = 0
    if isAll == True:
        totalPhoto = len(photoLists)
    else:
        starturi = "%s/%s" % (STARTDIR, STARTFILE)
        if starturi not in photoLists:
            print("Unable to find %s in Ricoh %s" % (starturi, DEVICE))
            sys.exit(1)
        else:
            while True:
                if photoLists[0] != starturi:
                    photoLists.pop(0)
                else:
                    totalPhoto = len(photoLists)
                    break
                    
    print("Start to download photos ...")    
    while True:
        if not photoLists:
            print("\nAll photos are downloaded.")
            shutdownGR()
            break
        else:
            photouri = photoLists.pop(0)
            count += 1
            if photouri in localFiles:
                print("(%d/%d) Skip %s, already have it on local drive!!" % (count, totalPhoto, photouri))
            else:
                print("(%d/%d) Downloading %s now ... " % (count, totalPhoto, photouri), end=' ')
                if fetchPhoto(photouri) == True:
                    print("done!!")
                else:
                    print("*** FAILED ***")
    
if __name__ == "__main__":
    # set connection timeout to 2 seconds
    socket.setdefaulttimeout(2)
    
    # setting up argument parser
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter, description='''
GRsync is a handy Python script, which allows you to sync photos from Ricoh GR
II or III via Wifi. It has been tested on Mac OS X and Ubuntu. It should be able to
run on any platform that has a Python environment.

It automatically checks if photos already exists in your local drive. Duplicated
photos will be skipped and only sync needed photos for you.

Simple usage - Download ALL photos from Ricoh GR II or III:

    ./GRsync -a

Advanced usage - Download photos after specific directory and file:

    ./GRsync -d 100RICOH -f R0000005.JPG
    
    All photos after 100RICOH/R0000005.JPG will be downloaded, including all
    following directories (eg. 101RICOH, 102RICOH)

''')
    parser.add_argument("-a", "--all", action="store_true", help="Download all photos")
    parser.add_argument("-d", "--dir", help="Assign directory (eg. -d 100RICOH). MUST use with -f")
    parser.add_argument("-f", "--file", help="Start to download photos from specific file \n(eg. -f R0000005.JPG). MUST use with -d")

    model = getDeviceModel()
    if model not in SUPPORT_DEVICE:
        print("Your source device '%s' is unknown or not supported!" % model)
        sys.exit(1)
    else:
        DEVICE = model

    if getBatteryLevel() < 15:
        print("Your battery level is less than 15%, please charge it before sync operation!")
        sys.exit(1)

    if parser.parse_args().all == True and parser.parse_args().dir is None and parser.parse_args().file is None:
        downloadPhotos(isAll=True)
    elif not (parser.parse_args().dir is None) and not (parser.parse_args().file is None) and parser.parse_args().all == False:
        match = re.match(r"^[1-9]\d\dRICOH$", parser.parse_args().dir)
        if match:
            STARTDIR = parser.parse_args().dir
        else:
            print("Incorrect directory name. It should be something like 100RICOH")
            sys.exit(1)
        match = re.match(r"^R0\d{6}\.JPG$", parser.parse_args().file)
        if match:
            STARTFILE = parser.parse_args().file
        else:
            print("Incorrect file name. It should be something like R0999999.JPG. (all in CAPITAL)")
            sys.exit(1)
        downloadPhotos(isAll=False)
    else:
        parser.print_help()
