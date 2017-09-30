#!/usr/bin/python
########################################################################
# lxTools
# Tools for working with Earth Networks lightning data and part of the
# EniPy library of tools.
#
# Copyright (c) 2017 Earth Networks, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Imports
# numpy is used for building arrays, and for general math
import numpy as np
# we really only need this to figure out where the location file is stored
import os
# struct allows decoding binary data, needed for raw LTG files and binary feeds
import struct
# time and calendar are generic libraries for workign with time
import time, calendar, datetime
# json is a build in library for decoding json files
import json
# threading is only used by the FeedReciever class, and allows it to
# operated asynchronously
import threading
import socket
# some of the files are compressed with gzip, this will decompress them
import gzip
# common tools
from miscTools import *



# In addition to the above, there is the lxcTools c library, which is
# imported as needed. This library is optional, but vastly improves the
# performance of related functions.  lxcTools may need to be compiled in
# order to operate.

DEBUGGING = True

__location__ = os.path.realpath(os.path.dirname(__file__))
locPath = os.path.join(__location__, 'entln.loc')
if not os.path.exists(locPath):
    import warnings

    warnings.warn('lxTools - location file is missing, some functions may not work properly', Warning)


###
# The Pulse and Flash classes are designed to decode the various string
# formats for data in use by Earth Networks (for historical reasons) and
# present the data in a consistent way with as little input as possible
class Pulse():
    """Pulse
    This is a general class for an ENTLN located 'pulse'.  One lightning
    'flash' is made up of many 'pulses'.

    A signficant amount of effort has been made such that regardless of
    which data source you are importing pulse data from, you can use
    the pulse object in the same way.  This is so that code written with
    this library is source agnostic.  Due to the multitude of EN data
    formats which all are subtly different, doing this has added a lot
    of complexity to what would otherwise be a simple data structure.
    Any complaints in the comments should therefor be forgiven.
    """

    ###
    # there are a lot of different ways to store the data, and they
    # don't call all the field the same name.  We handle that with
    # this alternate keys dictionary
    # each key has a forward and backward reference, making this a
    # pretty giant dictionary.
    _altKeys = { 	'timeStamp'    : 'time'      , 'time'       :'timeStamp',
                     'longitude'    : 'lon'       , 'lon'        :'longitude',
                     'latitude'     :'lat'        , 'lat'        :'latitude',
                     'amplitude'    :'peakCurrent', 'peakCurrent':'amplitude',
                     'numberSensors' :'numSensors' , 'numSensors' :'numberSensors',
                'height': 'icHeight', 'icHeight': 'height',
                'minLatitude': 'ulLatitude', 'ulLatitude': 'minLatitude',
                'minLongitude': 'ulLongitude', 'ulLongitude': 'minLongitude',
                'maxLatitude': 'lrLatitude', 'lrLatitude': 'maxLatitude',
                'maxLongitude': 'lrLongitude', 'lrLongitude': 'maxLongitude',
                'minor' :'eeMinor'	,
                     'major' :'eeMajor'    ,
                'bearing'      : 'eeBearing'   }

    # annoyingly, the csv files have their headers all in lower case,
    # while json is in camel case.  To get around this, this is a
    # so, we're going to convert lower case to camelcase
    _attributes = ["type",
                   "timeStamp",
                   "time",
                   "longitude",
                   "latitude",
                   "height",
                   "icHeight",
                   "amplitude",
                   "peakCurrent",
                   "numberSensors",
                   "numSensors",
                   "eeMajor",
                   "eeMinor",
                   "eeBearing"]
    _attributeConverter = {}
    for key in _attributes:
        _attributeConverter[key.lower() ] = key
    # clean up my mess
    del key

    def __init__(self, S, strType=None, header=None ):
        # store the initializing string, just in case
        self.messageString = S
        # some default values that don't always get filled in
        self.errorEllipse = None
        self.numSensors = 0

        ###
        # strType is a 3 tuple with information about where the string
        # came from so we know how to decode it.
        #   <format>, <type>, <source>
        # But, it's passing this is optional.  If it's not passed,
        # then we'll use the strType guesser
        if strType is None:
            self.strType = guess_strtype(S)
        else:
            self.strType = strType

        if self.strType[0] == 'binary':
            self._decode_binary_pulse(S)
        elif self.strType[0] == 'json':
            self._decode_json_pulse(S)
        elif self.strType[0] == 'csv':
            # for csv files, there's an optional header parameter that
            # would be convienient to have, and can potentially avoid
            # some problems
            self.header = header  # hopefully it's not none, but if it is, oh well
            self._decode_csv_pulse(S)
        elif self.strType[0] == 'mssql':
            self._decode_mssql_pulse(S)
        elif self.strType[0] == 'flat':
            self.header = header
            self._decode_flat_pulse(S)
        else:
            ###
            # I don't know what format this is
            #raise ValueError, 'unknown format: %s' % self.strType[0]
            raise ValueError('unknown format %s' % self.strType[0])

    def _decode_binary_pulse(self, S):
        # then we're working with a binary string

        # A flash message should be 32 bytes long, including the following:
        # !! all numbers are encoded big endian !!
        # 0 	length		unsigned int	56 (for flash)
        # 1		type		unsigned int	0 CG, 1 IC, 9 keep alive
        # 2-5	time (s)	unsigned int	epoc time of the strongest pulse (CG if available)
        # 6-9	time (ns)	unsigned int	ns of the second
        # 10-13	lat			signed int		lat *10,000,000, positive N, negative S
        # 14-17	lon			signed int		lon *10,000,000, positive E, negative W
        # 18-21 current		signed int		in Amperes
        # 22-23 height		unsigned int	in meters
        # 24	sensors		unsigned int
        # 25-26	err major	unsigned int	Error elipse major axis, meters
        # 27-28	err minot	unsigned int	Error elipse minor axis, meters
        # 29-30	err bearing	unsigned int	Error elipse bearing, degrees
        # 31	check sum	unsigned int	Check sum
        self.length, = struct.unpack('B', S[0])
        self.type, = struct.unpack('B', S[1])
        self.timeS, = struct.unpack('>I', S[2:6])
        self.timeNs, = struct.unpack('>I', S[6:10])
        self.latitude = struct.unpack('>i', S[10:14])[0] / 10000000.
        self.longitude = struct.unpack('>i', S[14:18])[0] / 10000000.
        self.peakCurrent, = struct.unpack('>i', S[18:22])
        self.icHeight, = struct.unpack('>H', S[22:24])
        self.numSensors, = struct.unpack('B', S[24])
        self.eeMajor, = struct.unpack('>H', S[25:27])
        self.eeMinor, = struct.unpack('>H', S[27:29])
        self.eeBearing, = struct.unpack('>H', S[29:31])
        self.checksum, = struct.unpack('B', S[31])

        # alternate forms
        for key in dir(self):
            value = getattr(self, key)
            if key in self._altKeys:
                altKey = self._altKeys[key]
                setattr(self, altKey, value)

        self.typeStr = type2str(self.type)

        if checksum(S[:-1]) != self.checksum:
            raise ValueError('Bad Checksum: %i %i' % (checksum(S[:-1]), self.checksum))

        ###
        # deal with the error ellipse' which have 2 formats
        self.errorEllipse = {'maj': self.eeMajor / 1000.,
                             'min': self.eeMinor / 1000.,
                             'b': self.eeBearing / 1000.}

        ###
        # handle time
        self.time = self.timeS + self.timeNs / 1.e9
        # timeStamp format: '2017-02-26T17:32:29.817443878'
        self.timeStamp = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(self.time))

        if DEBUGGING > 1:
            print('  %s pulse found at %0.2f %0.2f' % (self.typeStr, self.lat, self.lon))

    def _decode_json_pulse(self, S):
        # then we're working with a json string
        # pulse report
        # {"type":1,"timeStamp":"2017-02-13T00:00:26.7183463","longitude":-85.60853,"latitude":33.90489,"height":15299.0,"amplitude":473.0,"errorEllipse":{"maj":0.141,"min":0.14,"b":33.6},"numberSensors":6}
        # pulse feed
        # {"time":"2017-02-26T17:32:29.817443878Z","type":0,"latitude":-21.5043742,"longitude":-49.1724032,"peakCurrent":-21356.0,"icHeight":0.0,"numSensors":16,"eeMajor":278.0,"eeMinor":200.0,"eeBearing":21.8}


        # first we decode the json string
        dic = json.loads(S)

        # the we apply the parameters
        for key in dic.keys():
            value = dic[key]
            # catch some special cases
            if 'time' in key.lower():
                # some of the times have a Z at the end, some don't.  Remove the Z
                if value[-1] == 'Z':
                    value = value[:-1]
            # set the attribute
            setattr(self, key, value)
            # check for alternate naming, and set that attribute if needed
            if key in self._altKeys:
                altKey = self._altKeys[key]
                setattr(self, altKey, value)

        ###
        # human readable type
        self.typeStr = type2str(self.type)

        ###
        # the altKeys dictionary took care of most things, but there's
        # still the error ellipse stuff.:
        # pulse report
        # we have a dictionary in units of km
        # "errorEllipse":{"maj":0.141,"min":0.14,"b":33.6},}
        # pulse feed
        # we have individual values in units of meters
        # "eeMajor":278.0,"eeMinor":200.0,"eeBearing":21.8}
        if self.strType[2].lower() == 'report':
            # sometimes the errorEllipse dic is 'null'
            if self.errorEllipse:
                # then we have a dictionary under 'errorEllipse
                self.eeMajor = self.errorEllipse['maj']
                self.eeMinor = self.errorEllipse['min']
                self.eeBearing = self.errorEllipse['b']
            else:
                self.eeMajor = 0
                self.eeMinor = 0
                self.eeBearing = 0
        elif self.strType[2].lower() == 'feed':
            # feed data reports error ellipse info in meters, and
            # it's not always there.
            try:
                self.eeMajor /= 1000.
                self.eeMinor /= 1000.
                self.eeBearing /= 1000.
                self.errorEllipse = {'maj': self.eeMajor / 1000.,
                                     'min': self.eeMinor / 1000.,
                                     'b': self.eeBearing / 1000.}
            except:
                self.eeMajor = 0
                self.eeMinor = 0
                self.eeBearing = 0

        # handle special attirbutes (time)
        # the goal here is to have time in epoc format, since it's handy to use
        # so, timeStamps are in text, time's are in seconds
        self.timeStamp = self.time  # this entry should already exist
        self.time, self.timeS, self.timeNS = timeStamp2time(self.timeStamp)

    def _decode_mssql_pulse(self, dic):
        ###
        # pulses stored in the mssql databases have all different field
        # names, and some fields are stored in text in other fields.
        # The names are just hardcoded here

        # time information:
        self.timeStamp = dic['Lightning_Time_String']
        self.time, self.timeS, self.timeNS = timeStamp2time(self.timeStamp)

        # The easy stuff
        self.height = dic['Height']
        self.latitude = dic['Latitude']
        self.longitude = dic['Longitude']
        self.amplitude = dic['Amplitude']
        self.type = dic['Stroke_Type']

        # the hard stuff
        # "numSensors":16,"eeMajor":278.0,"eeMinor":200.0,"eeBearing":21.8
        # this stuff is stored in the stroke solution field, which is a
        # json string at least back to 2014
        strokeSolution = json.loads(dic['Stroke_Solution'])
        self.strokeSolution = strokeSolution
        # check the version
        version = strokeSolution['v']
        if version == None:
            # this is a WWLLN pulse
            self.type = 40  # override the type
            self.numSensors = len(strokeSolution['so'])
            self.eeMajor = 0
            self.eeMinor = 0
            self.eeBearing = 0
        else:
            # then we should have error information
            self.numSensors = len(strokeSolution['so'])
            self.eeMajor = strokeSolution['ee']['maj']
            self.eeMinor = strokeSolution['ee']['min']
            self.eeBearing = strokeSolution['ee']['b']
            self.errorEllipse = strokeSolution['ee']

        # deal with the alternate namings
        for key in dir(self):
            if key in self._altKeys:
                value = getattr(self, key)
                altKey = self._altKeys[key]
                setattr(self, altKey, value)

    def _decode_flat_pulse(self, S):
        # decoding flat files is a pain in the ass

        # the is the normal header file I expect
        if self.header == None:
            header = "FlashPortionID,FlashPortionGUID,FlashGUID,Lightning_Time,Lightning_Time_String,Latitude,Longitude,Height,Stroke_Type,Amplitude,Stroke_Solution,Offsets,Confidence,LastModifiedTime,LastModifiedBy"
            header = header.split(',')
        else:
            header = self.header

        headerStrings = ['Lightning_Time_String', 'Stroke_Solution', 'Offsets']
        headerNumbers = ['Latitude', 'Longitude', 'Height', 'Stroke_Type', 'Amplitude', 'Confidence']

        S = S.split(',')

        dic = {}

        j = 0
        for i in range(len(header)):
            if header[i] not in headerStrings + headerNumbers:
                j += 1
                continue
            if header[i] in headerStrings:
                if header[i] == 'Stroke_Solution':
                    # this is a json string
                    jsonStr = []
                    while S[j][-2:] != '}"':
                        jsonStr.append(S[j])
                        j += 1
                    jsonStr.append(S[j])
                    jsonStr = ','.join(jsonStr)[1:-1]

                    dic['Stroke_Solution'] = jsonStr
                else:
                    if S[j] == "":
                        # empty string
                        dic[header[i]] = None
                    elif S[j][0] == '"':
                        line = []
                        # we need to count forward
                        while S[j][-1].strip() != '"':
                            line.append(S[j])
                            j += 1
                        line.append(S[j])
                        line = ','.join(line)
                        dic[header[i]] = line[1:-1]
                    else:
                        dic[header[i]] = S[j]

            if header[i] in headerNumbers:
                dic[header[i]] = float(S[j])

            j += 1
        self._decode_mssql_pulse(dic)

    def _decode_csv_pulse(self, S):
        ###
        # the csv show up from the lightning reports.
        # they're also in the v2 feeds, which are not supported by this library

        # if no header is passed, this is the header I copied from a
        # pulse report csv file
        # type,timestamp,latitude,longitude,peakcurrent,icheight,numbersensors,majoraxis,minoraxis,bearing
        if self.header is None:
            self.header = ['type',
                           'timestamp',
                           'latitude',
                           'longitude',
                           'peakcurrent',
                           'icheight',
                           'numbersensors',
                           'major',
                           'minor',
                           'bearing']

        # split the input string by delimiter
        S = S.strip().split(',')

        # does the string match the header?
        if len(S) != len(self.header):
            raise ValueError('String does not match header')

        ###
        # now comes the fun part, we're going to loop over the entries
        # in the string, and apply the value to the corresponding
        # attribute using setattr and the header.
        for i in range(len(S)):
            key = self.header[i]
            # we're going to rashly assume that there are only 2 types
            # of values, strings and numbers
            try:
                value = float(S[i])
            except:
                value = S[i].strip()
            if value == '':
                value = 0

            ###
            # complication due to lower case:
            # we'll use the attributeConverter to set everything camel case
            if key in self._attributeConverter:
                key = self._attributeConverter[key]

            # catch some special cases
            if 'time' in key.lower():
                # some of the times have a Z at the end, some don't.  Remove the Z
                if value[-1] == 'Z':
                    value = value[:-1]
            # set the attribute
            setattr(self, key, value)
            # check for alternate naming, and set that attribute if needed
            if key in self._altKeys:
                altKey = self._altKeys[key]
                setattr(self, altKey, value)

        ###
        # human readable type
        self.typeStr = type2str(self.type)

        ###
        # deal with the error ellipse' which have 2 formats
        self.errorEllipse = {'maj': self.eeMajor,
                             'min': self.eeMinor,
                             'b': self.eeBearing}

        # handle special attirbutes (time)
        # the goal here is to have time in epoc format, since it's handy to use
        # so, timeStamps are in text, time's are in seconds
        self.timeStamp = self.time  # this entry should already exist
        self.time, self.timeS, self.timeNS = timeStamp2time(self.timeStamp)

    def printout(self):
        S = ""
        S += ('%10.9f,' % self.time).rjust(22)
        S += (' %2i,' % self.type).rjust(4)
        S += (' %5.4f,' % self.latitude).rjust(12)
        S += (' %5.4f,' % self.longitude).rjust(12)
        S += (' %9i,' % self.peakCurrent).rjust(11)
        S += (' %5i' % self.icHeight).rjust(6)
        ###
        # error ellipse info may not be available
        try:
            S += ','
            S += (' %3.1f,' % self.eeMajor).rjust(8)
            S += (' %3.1f,' % self.eeMinor).rjust(8)
            S += (' %3.1f ' % self.eeBearing).rjust(8)
        except:
            # if not, just don't append them
            pass
        return S


class Flash():
    ###
    # there are a lot of different ways to store the data, and they
    # don't call all the field the same name.  We handle that with
    # this alternate keys dictionary
    # each key has a forward and backward reference, making this a
    # pretty giant dictionary.
    _altKeys = { 	'timeStamp'    : 'time'      , 'time'       :'timeStamp',
                     'longitude'    : 'lon'       , 'lon'        :'longitude',
                     'latitude'     :'lat'        , 'lat'        :'latitude',
                     'amplitude'    :'peakCurrent', 'peakCurrent':'amplitude',
                     'numberSensors' :'numSensors' , 'numSensors' :'numberSensors',
                'height': 'icHeight', 'icHeight': 'height',
                'minLatitude': 'ulLatitude', 'ulLatitude': 'minLatitude',
                'minLongitude': 'ulLongitude', 'ulLongitude': 'minLongitude',
                'maxLatitude': 'lrLatitude', 'lrLatitude': 'maxLatitude',
                'maxLongitude': 'lrLongitude', 'lrLongitude': 'maxLongitude'}

    # annoyingly, the csv files have their headers all in lower case,
    # while json is in camel case.  To get around this, this is a
    # so, we're going to convert lower case to camelcase
    _attributes = ["type",
                   "timeStamp",
                   "time",
                   "longitude",
                   "latitude",
                   "height",
                   "icHeight",
                   "amplitude", "peakCurrent",
                   "numberSensors", "numSensors",
                   "eeMajor",
                   "eeMinor",
                   "eeBearing",
                   'icMultiplicity',
                   'cgMultiplicity',
                   'startTime',
                   'endTime',
                   'duration',
                   'ulLatitude', 'minLatitude',
                   'ulLongitude', 'minLongitude',
                   'lrLatitude', 'maxLatitude',
                   'lrLongitude', 'maxLongitude']
    _attributeConverter = {}
    for key in _attributes:
        _attributeConverter[key.lower()] = key

    def __init__(self, S, strType=None, header=None):

        # store the initializing string, just in case
        self.messageString = S

        ###
        # strType is a 3 tuple with information about where the string
        # came from so we know how to decode it.
        #   <format>, <type>, <source>
        # But, it's passing this is optional.  If it's not passed,
        # then we'll use the strType guesser
        if strType is None:
            self.strType = guess_strtype(S)
        else:
            self.strType = strType

        # ~ print 'str:', self.strType, repr(S)

        if self.strType[0] == 'binary':
            if self.strType[1] == 'combo':
                # then we have some extra work to do which I haven't
                # implemented yet
                self.pulses = []
                raise NotImplementedError('feature not implemented yet')
            self._decode_binary_flash(S)
        elif self.strType[0] == 'json':
            if self.strType[1] == 'combo':
                # then we have some extra work to do which I haven't
                # implemented yet
                # ~ raise NotImplementedError, 'feature not implemented yet'
                self.pulses = []
                pass
            self._decode_json_flash(S)
        elif self.strType[0] == 'csv':
            # for csv files, there's an optional header parameter that
            # would be convienient to have, and can potentially avoid
            # some problems
            self.header = header  # hopefully it's not none, but if it is, oh well
            self._decode_csv_flash(S)
        elif self.strType[0] == 'flat':
            # flat files are pain, they are csv files, with string containing ','
            # decoding flat files produces an mssql dic, and then decodes the dic
            self.header = header  # hopefully it's not none, but if it is, oh well
            self._decode_flat_flash(S)
        elif self.strType[0] == 'mssql':
            # the input for a mssql flash is a dictionary instead of a string
            self._decode_flat_flash(S)
        else:
            ###
            # I don't know what format this is
            raise ValueError('unknown format: %s' % self.strType[0])

    def _decode_flat_flash(self, S):
        # decoding flat files is a pain in the ass

        # the is the normal header file I expect
        if self.header == None:
            header = "FlashID,FlashGUID,Lightning_Time,Lightning_Time_String,Latitude,Longitude,Height,Stroke_Type,Amplitude,Stroke_Solution,Confidence,LastModifiedTime,LastModifiedBy"
            header = header.split(',')
        else:
            header = self.header

        # header strings are things that are supposed to be strings
        headerStrings = ['Lightning_Time_String', 'Stroke_Solution', 'Offsets']
        # header numbers are things that are supposed to be numbers
        headerNumbers = ['Latitude', 'Longitude', 'Height', 'Stroke_Type', 'Amplitude', 'Confidence']

        S = S.split(',')

        dic = {}

        j = 0
        for i in range(len(header)):
            if header[i] not in headerStrings + headerNumbers:
                j += 1
                continue
            if header[i] in headerStrings:
                if header[i] == 'Stroke_Solution':
                    # this is a json string
                    jsonStr = []
                    while S[j][-2:] != '}"':
                        jsonStr.append(S[j])
                        j += 1
                    jsonStr.append(S[j])
                    jsonStr = ','.join(jsonStr)[1:-1]

                    dic['Stroke_Solution'] = jsonStr
                else:
                    if S[j] == "":
                        # empty string
                        dic[header[i]] = None
                    elif S[j][0] == '"':
                        line = []
                        # we need to count forward
                        while S[j][-1].strip() != '"':
                            line.append(S[j])
                            j += 1
                        line.append(S[j])
                        line = ','.join(line)
                        dic[header[i]] = line[1:-1]
                    else:
                        dic[header[i]] = S[j]

            if header[i] in headerNumbers:
                dic[header[i]] = float(S[j])

            j += 1
        # ~ print dic
        self._decode_mssql_flash(dic)

    def _decode_mssql_flash(self, dic):
        ###
        # pulses stored in the mssql databases have all different field
        # names, and some fields are stored in text in other fields.
        # The names are just hardcoded here

        # time information:
        self.timeStamp = dic['Lightning_Time_String']
        self.time, self.timeS, self.timeNS = timeStamp2time(self.timeStamp)

        # The easy stuff
        self.height = dic['Height']
        self.latitude = dic['Latitude']
        self.longitude = dic['Longitude']
        self.amplitude = dic['Amplitude']
        self.type = dic['Stroke_Type']

        # the hard stuff
        # "numSensors":16,"eeMajor":278.0,"eeMinor":200.0,"eeBearing":21.8
        # this stuff is stored in the stroke solution field, which is a
        # json string at least back to 2014
        strokeSolution = json.loads(dic['Stroke_Solution'])
        # check the version
        version = strokeSolution['v']
        if version == None:
            # this is a WWLLN pulse
            self.type = 40  # override the type

        # things in all version types:
        self.numSensors = strokeSolution['ns']
        self.icMultiplicity = strokeSolution['im']
        self.cgMultiplicity = strokeSolution['cm']
        # I have have the bounding box messed up a bit, but have lat and lon correct
        self.ulLatitude = strokeSolution['aa']
        self.ulLongitude = strokeSolution['ao']
        self.lrLatitude = strokeSolution['ia']
        self.lrLongitude = strokeSolution['io']
        # the start and end times ( also in the stroke solution)
        self.startTimeStamp = strokeSolution['st']
        self.startTime, self.startTimeS, self.startTimeNS = timeStamp2time(self.startTimeStamp)
        self.endTimeStamp = strokeSolution['et']
        self.endTime, self.endTimeS, self.endTimeNS = timeStamp2time(self.endTimeStamp)

        # deal with the alternate namings
        for key in dir(self):
            if key in self._altKeys:
                value = getattr(self, key)
                altKey = self._altKeys[key]
                setattr(self, altKey, value)

    def _decode_binary_flash(self, S):
        ###
        # A flash message should be 56 bytes long, including the following:
        # !! all numbers are encoded big endian !!
        # 0 	length		unsigned int	56 (for flash)
        # 1		type		unsigned int	0 CG, 1 IC, 9 keep alive
        # 2-5	time (s)	unsigned int	epoc time of the strongest pulse (CG if available)
        # 6-9	time (ns)	unsigned int	ns of the second
        # 10-13	lat			signed int		lat *10,000,000, positive N, negative S
        # 14-17	lon			signed int		lon *10,000,000, positive E, negative W
        # 18-21 current		signed int		in Amperes
        # 22-23 height		unsigned int	in meters
        # 24	sensors		unsigned int
        # 25	IC mult		unsigned int	Number of IC pulses
        # 26	CG mult		unsigned int	Number of CG pulses
        # 27-30	start (s)	unsigned int	Start time (epoc)
        # 31-34 start (ns)	unsigned int	Start time fractional part
        # 35-38 Duration 	unsigned int	Duration of flash in ns
        # 39-42	UL lat		unsigned int	Upper Left corner latitude
        # 43-46	UL lon		unsigned int	Upper Left corner longitude
        # 47-50	UL lon		unsigned int	Lower Right corner latitude
        # 51-54	UL lon		unsigned int	Lower Right corner longitude
        # 55	Check sum	unsigned int	check sum

        self.length, = struct.unpack('B', S[0])
        self.type, = struct.unpack('B', S[1])
        self.timeS, = struct.unpack('>I', S[2:6])
        self.timeNs, = struct.unpack('>I', S[6:10])
        self.latitude = struct.unpack('>i', S[10:14])[0] / 10000000.
        self.longitude = struct.unpack('>i', S[14:18])[0] / 10000000.
        self.peakCurrent, = struct.unpack('>i', S[18:22])
        self.icHeight, = struct.unpack('>H', S[22:24])
        self.numSensors, = struct.unpack('B', S[24])
        self.icMultiplicity, = struct.unpack('B', S[25])
        self.cgMultiplicity, = struct.unpack('B', S[26])

        self.startTimeS, = struct.unpack('>I', S[27:31])
        self.startTimeNs, = struct.unpack('>I', S[31:35])
        self.duration, = struct.unpack('>I', S[35:39])

        self.ulLatitude = struct.unpack('>i', S[39:43])[0] / 10000000.
        self.ulLongitude = struct.unpack('>i', S[43:47])[0] / 10000000.
        self.lrLatitude = struct.unpack('>i', S[47:51])[0] / 10000000.
        self.lrLongitude = struct.unpack('>i', S[51:55])[0] / 10000000.

        self.checksum, = struct.unpack('B', S[55])

        self.pulses = []  # in case we have any to be appended later

        if self.type == 0:
            self.typeStr = 'CG'
        elif self.type == 1:
            self.typeStr = 'IC'
        elif self.type == 9:
            self.typeStr = 'keep alive'
        else:
            raise ValueError('Unknown type: %i' % self.type)

        if checksum(S[:-1]) != self.checksum:
            raise ValueError('Bad Checksum: %i %i' % (checksum(S[:-1]), self.checksum))

        ###
        # get a float time, for convenience
        self.time = self.timeS + self.timeNs / 1.e9

        if DEBUGGING > 1:
            print('%s flash found at %0.2f %0.2f' % (self.typeStr, self.lat, self.lon))
            # then we're working with a json string

    def _decode_json_flash(self, S):
        # flash report
        # {"type":0,"timeStamp":"2017-02-01T00:19:49.0936288","longitude":-68.10588,"latitude":-16.76447,"height":0.0,"amplitude":-47108.0,"numberSensors":16,"icMultiplicity":0,"cgMultiplicity":1,"startTime":"2017-02-01T00:19:49.0936288","endTime":"2017-02-01T00:19:49.0936288","durationSeconds":0.0,"minLatitude":-16.76447,"minLongitude":-68.10588,"maxLatitude":-16.76447,"maxLongitude":-68.10588,"portions":[{"type":0,"timeStamp":"2017-02-01T00:19:49.0936288","longitude":-68.10588,"latitude":-16.76447,"height":0.0,"amplitude":-47108.0,"errorEllipse":{"maj":0.492,"min":0.159,"b":104.2},"numberSensors":16}]}
        # combo report
        # {"type":0,"timeStamp":"2017-02-01T20:24:57.2901218","longitude":-68.0087,"latitude":-7.48562,"height":0.0,"amplitude":-59699.0,"numberSensors":7,"icMultiplicity":0,"cgMultiplicity":2,"startTime":"2017-02-01T20:24:57.2901218","endTime":"2017-02-01T20:24:57.3120733","durationSeconds":0.021951445,"minLatitude":-7.5689,"minLongitude":-68.00871,"maxLatitude":-7.48562,"maxLongitude":-68.00871,"portions":[{"type":0,"timeStamp":"2017-02-01T20:24:57.2901218","longitude":-68.0087,"latitude":-7.48562,"height":0.0,"amplitude":-59699.0,"errorEllipse":{"maj":0.707,"min":0.185,"b":38.4},"numberSensors":6},{"type":0,"timeStamp":"2017-02-01T20:24:57.3120733","longitude":-67.90836,"latitude":-7.5689,"height":0.0,"amplitude":-39619.0,"errorEllipse":{"maj":1.916,"min":0.542,"b":35.5},"numberSensors":7}]}
        # flash feed
        # {"time":"2017-02-26T17:30:52.579925000Z","type":0,"latitude":-37.7905,"longitude":-61.2728,"peakCurrent":-55520.0,"icHeight":0.0,"numSensors":6,"icMultiplicity":0,"cgMultiplicity":1,"startTime":"2017-02-26T17:30:52.579925000Z","duration":0,"ulLatitude":-37.7905,"ulLongitude":-61.2728,"lrLatitude":-37.7905,"lrLongitude":-61.2728}

        # first we decode the json string
        dic = json.loads(S)

        # the we apply the parameters
        for key in dic.keys():
            value = dic[key]
            # catch some special cases
            if 'time' in key.lower():
                # some of the times have a Z at the end, some don't.  Remove the Z
                if value[-1] == 'Z':
                    value = value[:-1]
            # set the attribute
            setattr(self, key, value)
            # check for alternate naming, and set that attribute if needed
            if key in self._altKeys:
                altKey = self._altKeys[key]
                setattr(self, altKey, value)

        self._convert_times()
        self._fill_bbox()

        ###
        # is this a combo feed?
        if 'portions' in dic:
            # yes it is.
            # What we're supposed to do now is append a bunch of pulses,
            # but that's not implemented yet
            pass

    def _decode_csv_flash(self, S):
        ###
        # the csv show up from the lightning reports.
        # they're also in the v2 feeds, which are not supported by this library

        # if no header is passed, this is the header I copied from a
        # pulse report csv file
        # type,timestamp,latitude,longitude,peakcurrent,icheight,numbersensors,icmultiplicity,cgmultiplicity,starttime,endtime,duration,ullatitude,ullongitude,lrlatitude,lrlongitude
        if self.header is None:
            self.header = ['type',
                           'timestamp',
                           'latitude',
                           'longitude',
                           'peakcurrent',
                           'icheight',
                           'numbersensors',
                           'icmultiplicity',
                           'cgmultiplicity',
                           'starttime',
                           'endtime',
                           'duration',
                           'ullatitude',
                           'ullongitude',
                           'lrlatitude',
                           'lrlongitude']

        # split the input string by delimiter
        S = S.strip().split(',')

        # does the string match the header?
        if len(S) != len(self.header):
            raise ValueError('String does not match header')

        ###
        # now comes the fun part, we're going to loop over the entries
        # in the string, and apply the value to the corresponding
        # attribute using setattr and the header.
        for i in range(len(S)):
            key = self.header[i]
            # we're going to rashly assume that there are only 2 types
            # of values, strings and numbers
            try:
                value = float(S[i])
            except:
                value = S[i].strip()
            # catch an empty value and fill with 0's
            if value == '':
                value = 0

            ###
            # complication due to lower case:
            # we'll use the attributeConverter to set everything camel case
            if key in self._attributeConverter:
                key = self._attributeConverter[key]

            # catch some special cases
            if 'time' in key.lower():
                # some of the times have a Z at the end, some don't.  Remove the Z
                if value[-1] == 'Z':
                    value = value[:-1]
            # set the attribute
            setattr(self, key, value)
            # check for alternate naming, and set that attribute if needed
            if key in self._altKeys:
                altKey = self._altKeys[key]
                setattr(self, altKey, value)

        ###
        # human readable type
        self.typeStr = type2str(self.type)

        # handle special attirbutes (time)
        # the goal here is to have time in epoc format, since it's handy to use
        # so, timeStamps are in text, time's are in seconds
        self.timeStamp = self.time  # this entry should already exist
        self.time, self.timeS, self.timeNS = timeStamp2time(self.timeStamp)

        self.startTimeStamp = self.startTime
        self.startTime, self.startTimeS, self.startTimeNS = timeStamp2time(self.startTimeStamp)

        self.endTimeStamp = self.endTime
        self.endTime, self.endTimeS, self.endTimeNS = timeStamp2time(self.endTimeStamp)

    def append_pulse(self, pulse):
        # Maybe we'll do more with this function later on
        self.pulses.append(pulse)

    def _fill_bbox(self):
        if 'ulLatitude' in dir(self):
            # everything is done already
            return
        self.ulLatitude = self.maxLatitude = self.lat
        self.ulLongitude = self.maxLongitude = self.lon
        self.lrLatitude = self.minLatitude = self.lat
        self.lrLongitude = self.minLongitude = self.lon

    def _convert_times(self):
        # handle special attirbutes (time)
        # the goal here is to have time in epoc format, since it's handy to use
        # so, timeStamps are in text, time's are in seconds
        self.timeStamp = self.time  # this entry should already exist
        self.time, self.timeS, self.timeNS = timeStamp2time(self.timeStamp)

        ###
        # the start and end times for the flash are also sometimes passed
        # to make things compatable, we'll need to do something if they're
        # not passed

        if 'startTime' not in dir(self):
            # we have no start time
            self.startTime = self.timeStamp

        self.startTimeStamp = self.startTime
        self.startTime, self.startTimeS, self.startTimeNS = timeStamp2time(self.startTimeStamp)

        # dealing with duration is easy
        if 'duration' not in dir(self):
            self.duration = 0

        # but then there's the end time
        if 'endTime' not in dir(self):
            self.endTime = self.startTime + self.duration
            self.endTimeNS, self.endTimeS = np.modf(self.endTime)
            self.endTimeNS = int(self.endTimeNS * 1e9)
            self.endTimeStamp = time2timeStamp(self.endTime)
        else:
            self.endTimeStamp = self.endTime
            self.endTime, self.endTimeS, self.endTimeNS = timeStamp2time(self.endTimeStamp)
            self.duration = self.endTime - self.startTime

    def printout(self):
        S = ''
        S += ('%10.9f,' % self.time).rjust(22)
        S += (' %2i,' % self.type).rjust(4)
        S += (' %5.4f,' % self.latitude).rjust(12)
        S += (' %5.4f,' % self.longitude).rjust(12)
        S += (' %9i,' % self.peakCurrent).rjust(11)
        S += (' %3i,' % self.cgMultiplicity).rjust(5)
        S += (' %3i' % self.icMultiplicity).ljust(5)
        return S


class Report():
    _altKeys = { 	'timeStamp'    : 'time'      , 'time'       :'timeStamp',
                     'longitude'    : 'lon'       , 'lon'        :'longitude',
                     'latitude'     :'lat'        , 'lat'        :'latitude',
                     'amplitude'    :'peakCurrent', 'peakCurrent':'amplitude',
                     'numberSensors' :'numSensors' , 'numSensors' :'numberSensors',
                'height': 'icHeight', 'icHeight': 'height',
                'minLatitude': 'ulLatitude', 'ulLatitude': 'minLatitude',
                'minLongitude': 'ulLongitude', 'ulLongitude': 'minLongitude',
                'maxLatitude': 'lrLatitude', 'lrLatitude': 'maxLatitude',
                'maxLongitude': 'lrLongitude', 'lrLongitude': 'maxLongitude',
                'minor' :'eeMinor'	,
                     'major' :'eeMajor'    ,
                'bearing'      : 'eeBearing'   }

    def __init__(self, filelike=None, mmap=False, strType=None, **kwargs ):
        """
        A report is a collection of flashes or pulses, usually distributed
        as a file or files in csv or json format.  Depending on the area
        and time range the report covers, the report files can be very
        large, so some attempt has been made to keep this class memory
        efficient as possible.

        mmap - puts the arrays into a memmap, so that memory use is
        substantially reduced, at the expense of some speed

        mode - the report supports reading or writing!
        """

        # filelike might be a list of files, or just a single file.  It
        # can be either a string (file path), or an open file object
        if filelike is None:
            self.inFiles = []
        elif not isinstance(filelike, list):
            # it's not a list.  To make things easier, we'll make it one
            self.inFiles = [filelike]
        else:
            self.inFiles = filelike

        ###
        # get the other parameters that were passed to the report on
        # object creation.  Most of these will be default values
        self.mmap = mmap  # mmap isn't supported yet
        self.strType = strType
        self.flashID = 0  # this is used for combo reports
        self._arr = None

        ###
        # should we read the file?
        for inFile in self.inFiles:
            self.read(inFile)

    def append(self, ob, update=True):
        # ob might be a list of obs
        if isinstance(ob, list):
            for subOb in ob:
                self.append(subOb, update=False)
            # update the helper arrays
            if update:
                self.update()
            return

        if isinstance(ob, Report):
            N = ob._arr.shape
            if self.strType is None and self._arr is None:
                # we don't have any data
                self.strType = ob.strType
                self._arr = ob._arr.copy()
            elif self.strType is not None and self._arr is not None:
                # we do have data
                s = self._arr.shape

                # double check that they're compatible
                if s[1] != N[1]:
                    # not sure how this can happen, but it just did
                    raise ValueError('%s is incompatible' % repr(ob))

                # the helper arrays are referencing the memory in the
                # array.  We'll update them in a second, so for now
                # we'll ignore the refcheck at our own peril
                self._arr.resize([s[0] + N[0], s[1]], refcheck=False)
                # hopefully I counted the length correctly
                self._arr[s[0]:] = ob._arr

        elif self.strType is None:
            # then we haven't created the array yet
            self.strType = ob.strType
            arr = self.decode(ob)
            N = arr.shape[0]
            self._arr = arr.reshape([1, N]).copy()

        elif ob.strType[1] == self.strType[1]:
            # it's a compatable type Pulse or Flash ( I hope )

            # first we need to expand the array, this is the fastest
            # way I've found to do it
            if self._arr is not None:
                s = self._arr.shape
                # the helper arrays are referencing the memory in the
                # array.  We'll update them in a second, so for now
                # we'll ignore the refcheck at our own peril
                self._arr.resize([s[0] + 1, s[1]], refcheck=False)
                # the we assign the new value
                self._arr[-1] = self.decode(ob)
            else:
                arr = self.decode(ob)
                N = arr.shape[0]
                self._arr = arr.reshape([1, N]).copy()

        else:
            raise ValueError('%s is incompatible' % repr(ob))

        # update the helper arrays
        if update:
            self.update()

    def truncate(self, m):
        # m is either a mask, or an int
        if isinstance(m, int):
            # it's a number, cut off the first m entries in the array
            self._arr = self._arr[m:]
        elif isinstance(m, (list, np.ndarray)):
            # it's a mask, probably
            try:
                self._arr = self._arr[m]
            except:
                raise ValueError('invalid mask')
        else:
            raise ValueError('Truncate takes an int or a mask')

        # update the helper arrays
        self.update()

    def read(self, inFile=None, N=0):
        print(inFile)

        ###
        # if the input file isn't given, we'll read the first one we
        # have on hand.
        if inFile is None and len(self.inFiles) > 0:
            inFile = self.inFiles[0]
        elif inFile is None:
            raise ValueError('No file given to read')

        ###
        # loop over the files
        if DEBUGGING:
            print('loading file, this may take a bit')
        # is it a string of a file
        if isinstance(inFile, basestring):
            # it's a string, try and open
            # first see if it's gzipped
            if inFile[-2:] == 'gz':
                f = gzip.GzipFile(inFile, 'r')
            else:
                f = open(inFile, 'r')

        elif isinstance(inFile, file) or isinstance(inFile, gzip.GzipFile):
            # then it's a file
            f = inFile
        else:
            # then I'm not sure what to do with this
            raise ValueError('%S is not a filelike' % filelike)

        sTime = time.time()
        ###
        # start reading the file
        S = f.readline().strip()

        # what kind of string as we working with?
        # this shouldn't change throughout the report
        # report type is a 3 tuple,
        # <format>, <type>, <source>
        if self.strType == None:
            self.strType = guess_strtype(S)

        # csv type catch:
        # the first line will be the header information
        if self.strType[0] == 'csv':
            self.headerStr = S.split(',')
            S = f.readline().strip()
        # flat file type catch
        if self.strType[0] == 'flat':
            # the first line in probably a header
            if 'FlashGUID' in S:
                # it's a header line
                self.headerStr = S.split(',')
                S = f.readline().strip()

        lst = []

        i = 0
        while S != "":
            # convert this line
            if self.strType[1].lower() == 'flash':
                # just flash information
                lst.append(Flash(S))
            elif self.strType[1].lower() == 'combo':
                # flash and pulse information
                lst.append(Flash(S))
                # pulses and flashes are supported yet
                self.flashID += 1
            elif self.strType[1].lower() == 'pulse':
                # pulse information
                lst.append(Pulse(S))
            else:
                raise ValueError('Unknown file type: %s' % self.strType)

            i += 1

            # should we end early?
            if N > 0 and i > N:
                break

            # we use lst as a buffer, but don't want it to get too long
            # because we can use up all our memory for really big reads
            if len(lst) >= 100000:
                self.append(lst)
                lst = []
                if DEBUGGING:
                    print(' - %i %s loaded' % (i, self.strType[1]))

            S = f.readline().strip()

        self.append(lst)

        if DEBUGGING:
            print
            ' - %i %s loaded in %0.1f seconds' % (len(self._arr), self.strType[1], time.time() - sTime)

    def write(self, outFile, strType=None):
        """writes the output to a file,
        you can specify the format with strType (except it's not supported yet)
        <format>, <type>, <source>"""

        if strType == None:
            strType = self.strType

        if strType[1].lower() == 'pulse':
            if strType[0].lower() == 'csv':
                print('writing pulse csv:', outFile)
                # we're writing a csv pulse report
                self._write_csv_pulse(outFile)
        elif strType[1].lower() == 'flash':
            if strType[0].lower() == 'csv':
                print('writing flash csv:', outFile)
                # we're writing a csv pulse report
                self._write_csv_flash(outFile)

    def save_state(self, outFile):
        """
        save_state saves the output of the arrays directly to a file,
        in a non-human readable form.  Reading these states is much
        faster than reading the ascii format data file
        """
        header = np.zeros(self._arr.shape[1])
        header[:2] = self._arr.shape
        shape = self._arr.shape[0] + 1, self._arr.shape[1]
        arr = np.memmap(outFile, mode='write', shape=shape, dtype='double')
        arr[0] = header
        arr[1:] = self._arr
        arr.flush()

    def load_state(self, inFile):

        arr = np.memmap(inFile, dtype='double', mode='r')

        # get the shape out of the header
        shape = arr[:2].astype(int)

        # copy this into memory
        self._arr = np.zeros(shape)
        self._arr[:] = arr[shape[1]:].reshape(shape)

        # set the type string
        if shape[1] == 15:
            # flash
            self.strType = 'csv', 'flash', 'report'
        elif shape[1] == 10:
            self.strType = 'csv', 'pulse', 'report'

        # update things
        self.update()

    def _write_csv_pulse(self, outFile):
        f = open(outFile, 'w')

        # first we write the header line
        f.write('type,timestamp,latitude,longitude,peakcurrent,icheight,numbersensors,majoraxis,minoraxis,bearing\n')

        # then we loop through the sources, and write each line
        for i in range(len(self.time)):
            S = ''
            S += ('%i, ' % self.type[i]).rjust(4)
            S += ('%s, ' % time2timeStamp(self.time[i])).rjust(30)
            S += ('%3.6f, ' % self.lat[i]).rjust(12)
            S += ('%3.6f, ' % self.lon[i]).rjust(12)
            S += ('%i, ' % self.amplitude[i]).rjust(8)
            S += ('%i, ' % self.height[i]).rjust(6)
            S += ('%i, ' % self.numSensors[i]).rjust(5)
            S += ('%1.2f, ' % self.eeMajor[i]).rjust(5)
            S += ('%1.2f, ' % self.eeMinor[i]).rjust(5)
            S += ('%1.2f  ' % self.eeBearing[i]).rjust(5)
            S += '\n'
            # ~ print S
            f.write(S)
        f.close()

    def _write_csv_flash(self, outFile):
        f = open(outFile, 'w')

        # first we write the header line
        f.write(
            'type,timestamp,latitude,longitude,peakcurrent,icheight,numbersensors,icmultiplicity,cgmultiplicity,starttime,endtime,duration,ullatitude,ullongitude,lrlatitude,lrlongitude\n')
        """
        type,timestamp,latitude,longitude,peakcurrent,
        icheight,numbersensors,icmultiplicity,cgmultiplicity,
        starttime,endtime,duration,ullatitude,ullongitude,lrlatitude,lrlongitude\n
        """
        for i in range(len(self.time)):
            S = ''
            S += ('%i, ' % self.type[i]).rjust(4)
            S += ('%s, ' % time2timeStamp(self.time[i])).rjust(30)
            S += ('%3.6f, ' % self.lat[i]).rjust(12)
            S += ('%3.6f, ' % self.lon[i]).rjust(12)
            S += ('%i, ' % self.amplitude[i]).rjust(8)
            S += ('%i, ' % self.height[i]).rjust(6)
            S += ('%i, ' % self.numSensors[i]).rjust(5)
            S += ('%i, ' % self.icMultiplicity[i]).rjust(5)
            S += ('%i, ' % self.cgMultiplicity[i]).rjust(5)
            S += ('%s, ' % time2timeStamp(self.startTime[i])).rjust(30)
            S += ('%s, ' % time2timeStamp(self.endTime[i])).rjust(30)
            S += ('%1.6f, ' % (self.endTime[i] - self.startTime[i])).rjust(10)
            S += ('%3.6f, ' % self.ulLatitude[i]).rjust(12)
            S += ('%3.6f, ' % self.ulLongitude[i]).rjust(12)
            S += ('%3.6f, ' % self.lrLatitude[i]).rjust(12)
            S += ('%3.6f  ' % self.lrLongitude[i]).rjust(12)
            S += '\n'
            # ~ print S
            f.write(S)
        f.close()

    def decode(self, ob):
        # ob is a flash or a pulse
        if isinstance(ob, Pulse):
            return self._decode_pulse(ob)
        elif isinstance(ob, Flash):
            return self._decode_flash(ob)
        else:
            raise ValueError('decode works on Pulse or Flash objects')

    def _decode_flash(self, flash):
        ###
        # we pull the following from the flash:
        # type,time,latitude,longitude,peakCurrent,icHeight,numberSensors,icMultiplicity,cgMultiplicity,startTime,ulLatitude,ulLongitude,lrLatitude,lrLongitude

        output = np.zeros(15)
        output[0] = flash.type
        output[1] = flash.time
        output[2] = flash.lat
        output[3] = flash.lon
        output[4] = flash.amplitude
        output[5] = flash.height
        output[6] = flash.numSensors
        output[7] = flash.icMultiplicity
        output[8] = flash.cgMultiplicity
        output[9] = flash.startTime
        output[10] = flash.endTime
        output[11] = flash.ulLatitude
        output[12] = flash.ulLongitude
        output[13] = flash.lrLatitude
        output[14] = flash.lrLongitude

        return output

    def _decode_pulse(self, pulse):
        ###
        # we pull the following from the pulse:
        # type,time,latitude,longitude,peakCurrent,icHeight,numberSensors,eeMajor,eeMinor,eeBearing
        output = np.zeros(10)
        output[0] = pulse.type
        output[1] = pulse.time
        output[2] = pulse.lat
        output[3] = pulse.lon
        output[4] = pulse.amplitude
        output[5] = pulse.height
        output[6] = pulse.numSensors
        output[7] = pulse.eeMajor
        output[8] = pulse.eeMinor
        output[9] = pulse.eeBearing

        return output

    def update(self):
        # this sets the helper strings
        if self.strType is None:
            # then no data could have been set yet, just return
            return None

        # clear my attributes
        for k in self._altKeys:
            if k in dir(self):
                delattr(self, k)

        self.type = self._arr[:, 0]
        self.time = self._arr[:, 1]
        self.lat = self._arr[:, 2]
        self.lon = self._arr[:, 3]
        self.amplitude = self._arr[:, 4]
        self.height = self._arr[:, 5]
        self.numSensors = self._arr[:, 6]

        # now things get strType specific
        if self.strType[1] == 'flash' or self.strType[1] == 'combo':
            self.icMultiplicity = self._arr[:, 7]
            self.cgMultiplicity = self._arr[:, 8]
            self.startTime = self._arr[:, 9]
            self.endTime = self._arr[:, 10]
            self.ulLatitude = self._arr[:, 11]
            self.ulLongitude = self._arr[:, 12]
            self.lrLatitude = self._arr[:, 13]
            self.lrLongitude = self._arr[:, 14]
        elif self.strType[1] == 'pulse':
            self.eeMajor = self._arr[:, 7]
            self.eeMinor = self._arr[:, 8]
            self.eeBearing = self._arr[:, 9]

        # get the alternate namings
        for key in dir(self):
            value = getattr(self, key)
            if key in self._altKeys:
                altKey = self._altKeys[key]
                setattr(self, altKey, value)


class LtgFile():
    def __init__(self, filelike):

        # open the file
        self.open(filelike)

        # where are the stations?
        try:
            self.locFile = LocFile(locPath)
        except:
            self.locFile = None

        # build the catalog
        self.split_ltg_by_message()

    def read(self, key):

        ###
        # loads the file specified by the catalog key
        self.f.seek(key)

        # get the location of the station
        if self.locFile is not None:
            size, magic, version, stationID, timeStart = self.catalog[key]
            lat, lon = self.locFile.stations[stationID]
        else:
            lat = None
            lon = None

        messageStr = self.f.read(self.catalog[key][0] + 2)
        return LtgMessage(messageStr, lat=lat, lon=lon)

    def open(self, filelike):
        # open the input file for reading
        if isinstance(filelike, basestring):
            # it's a string, try and open
            self.f = open(filelike, 'r')
        elif isinstance(filelike, file):
            # then it's a file
            self.f = filelike
        else:
            raise Error('%s does not seem to be a file' % repr(filelike))

    def close(self):
        self.f.close()

    def split_ltg_by_message(self):
        if DEBUGGING:
            print('building LTG Catalog, this may take a bit')

        # the file pointer should already exist
        f = self.f

        ###
        # the first 4 bytes in the file are (probably) the total number
        # of concatinated files
        # for now, we will just skip over this
        f.seek(4)
        ltgCatalog = {}
        while True:  # I should catch EOF here, being lazy
            l = f.tell()
            # read in the critial information, these values are always present
            try:
                ###
                # note, the size number here is little endian, unlike
                # the rest of the message!
                size, magic, messageType, messageVersionMajor, messageVersionMinor = struct.unpack('HBBBB', f.read(6))
            except:
                # must be EOF
                break
            version = [messageType, messageVersionMajor, messageVersionMinor]

            # in almost all cases, we can also decode the time and station information as well
            # so, we'll catch the cases where that's not true
            if (version == [1, 9, 0]) or (version[0] != 1):
                # we can't do further decoding

                ###
                # usually these files are the GPS data that the sensors send back,
                # there might maybe be 1 or 2 stations with very very old firmware versions
                # it's probably safe to just skip them all, if not, uncomment below
                # ~ ltgCatalog[l] = [size, magic, version, None, None]

                # skip to the next message
                f.seek(size - 4, 1)  # the -4 offsets for the portion we already read
                continue

            # in all other cases, we can do a little bit extra decoding of use
            stationID = f.read(10).strip()
            timeStart, = struct.unpack('>I', f.read(4))

            ltgCatalog[l] = [size, magic, version, stationID, timeStart]

            f.seek(size - 18, 1)  # the -18 offsets for the portion we already read

        self.catalog = ltgCatalog

        if DEBUGGING:
            print
            'found %i lightning messages' % len(self.catalog)


class LtgMessage():
    def __init__(self, messageStr, lat=None, lon=None):

        self.messageStr = messageStr
        # get version information
        size, magic, messageType, versionMajor, versionMinor = struct.unpack('HBBBB', messageStr[:6])
        self.size = size
        self.magic = magic
        self.version = [messageType, versionMajor, versionMinor]

        self.toga = None  # initialize this to something, since these
        # are not always present.

        self.lat = lat
        self.lon = lon

        ###
        # decode the message header
        if self.version == [1, 9, 1]:
            self._decode191()
        elif self.version == [1, 9, 4]:
            self._decode194()
        elif self.version == [1, 10, 1]:
            self._decode1101()
        elif self.version == [4, 0, 1]:
            # gps, this is the line from stan's code to get lat and lon
            # stationId, latms, lonms = struct.unpack('>4x10s15xii',h)
            pass

    def _decompress194(self, S):
        ###1.9.4 decompression, should be backwards compatible with 1.9.3 data

        directionState = 0  # 0 for down, 1 for up

        decompressed = []

        i = 0
        while i < len(S):
            byteType = byte2type(S[i])
            B, = struct.unpack('B', S[i])
            # case statement (with if's)
            if byteType == 0:
                ###
                # Type 0 1<7> (1 byte)
                # A leading one, followed by a seven bit integer indicates progression
                # to the next amplitude threshold.  Direction is unchanged, so if we
                # were rising before, we continue rising to the next larger threshold
                # value. The seven bit integer indicates how many ticks have elapsed
                # between threshold crossings.
                # tick = tickOfLastPoint + 7bitInteger
                # amplitude = nextThreshold
                # ~ print 'T0', hex(B),

                tim, = struct.unpack('B', S[i])
                # cut off that leading 1 and add to previous state
                tim = (tim & 0x7f) + decompressed[-1][0]

                if directionState == 0:
                    # going down
                    amp = boundary_prev(decompressed[-1][1])
                else:
                    # going up
                    amp = boundary_next(decompressed[-1][1])
                decompressed.append([tim, amp])

                i += 1
            elif byteType == 1:
                ###
                # Type 1 01<6><8> (2 bytes)
                # A leading '01', followed by a six bit integer and an eight bit integer
                # denotes a maximum (if rising) or a minimum (if falling).
                # The 8 bit integer is the number of ticks elapsed since the previous point.
                # The amplitude is between two thresholds. One is the next threshold, and
                # the other is the threshold beyond that (farther from 0). Call the smaller
                # of these a0 and the larger a1.
                # tick = tickOfLastPoint + 8bitInteger
                # amplitude = a0 + (6bitInteger/64) * (a1 - a0)
                if i + 2 > len(S):
                    print('exiting early', i, len(S))
                    break
                amp, tim = struct.unpack('BB', S[i:i + 2])
                # ~ print 'T1', hex(B), hex(tim),

                tim = tim + decompressed[-1][0]

                ###
                # going up or down?
                if directionState == 0:
                    # going down
                    a1 = boundary_prev(decompressed[-1][1])
                    a0 = boundary_prev(a1)
                # ~ print 'down', a0, a1
                else:
                    # going up
                    a0 = boundary_next(decompressed[-1][1])
                    a1 = boundary_next(a0)
                # ~ print 'up', a0, a1
                # chop off leading 01, and interpolate
                amp = a0 + ((amp & 0x3f) * (a1 - a0)) / 64

                decompressed.append([tim, int(amp)])
                directionState = (directionState + 1) % 2  # flip direction state
                i += 2
            elif byteType == 2:
                ###
                # Tyoe 2     001<5><16> (3 bytes)
                # A leading '001' followed by a five bit integer and a sixteen bit integer
                # denotes a maximum or minimum.
                # The 16 bit integer is the number of ticks elapsed since the previous point.
                # The 5 bit integer gives the amplitude of the peak.
                #
                # tick = tickOfLastPoint + 16bitInteger
                # amplitude = a0 + (5bitInteger/32) * (a1 - a0)
                if i + 3 > len(S):
                    print('exiting early', i, len(S))
                    break
                amp, tim = struct.unpack('>BH', S[i:i + 3])
                # ~ print 'T2', hex(amp), hex(tim),

                tim = tim + decompressed[-1][0]
                ###
                # going up or down?
                if directionState == 0:
                    # going down
                    a1 = boundary_prev(decompressed[-1][1])
                    a0 = boundary_prev(a1)
                # ~ print 'down', a0, a1
                else:
                    # going up
                    a0 = boundary_next(decompressed[-1][1])
                    a1 = boundary_next(a0)
                # ~ print 'up', a0, a1
                # chop off leading 001, and interpolate
                amp = a0 + ((amp & 0x1f) * (a1 - a0)) / 32

                decompressed.append([tim, int(amp)])
                directionState = (directionState + 1) % 2  # flip direction state
                i += 3
            # ~ print decompressed[-1]
            # ~ break
            elif byteType == 3:
                ###
                # Type 3  0001<12> (2 bytes)
                # A leading '0001', followed by a twelve bit integer indicates progression
                # to the next amplitude threshold.  Direction is unchanged, so if we
                # were rising before, we continue rising to the next larger threshold
                # value. The twelve bit integer indicates how many ticks have elapsed
                # between threshold crossings.
                #
                # tick = tickOfLastPoint + 12bitInteger
                # amplitude = nextThreshold
                if i + 2 > len(S):
                    print('exiting early', i, len(S))
                    break
                tim, = struct.unpack('>H', S[i:i + 2])
                # ~ print 'T3', hex(tim),

                tim = (tim & 0x0fff) + decompressed[-1][0]

                if directionState == 0:
                    # going down
                    amp = boundary_prev(decompressed[-1][1])
                else:
                    # going up
                    amp = boundary_next(decompressed[-1][1])
                decompressed.append([tim, amp])

                i += 2
            # ~ print decompressed[-1]
            # ~ break
            elif byteType == 4:
                ###
                # Type 4  00001<11> (2 bytes)
                # A leading '00001', followed by an eleven bit integer indicates progression
                # through 0 to an amplitude equal to the amplitude of the last point negated.
                #
                # tick = tickOfLastPoint + 11bitInteger
                # amplitude = -lastAmplitude
                if i + 2 > len(S):
                    print('exiting early', i, len(S))
                    break
                # ~ #going down

                tim, = struct.unpack('>H', S[i:i + 2])
                # ~ print 'T4', hex(tim),

                tim = (tim & 0x07ff) + decompressed[-1][0]
                # ~ if directionState == 0:
                # ~ amp = -boundary_prev( decompressed[-1][1] )
                # ~ else:
                # ~ #going up
                # ~ amp = -boundary_next( decompressed[-1][1] )
                amp = -decompressed[-1][1]

                decompressed.append([tim, amp])
                i += 2
            elif byteType == 5:
                ###
                # Type 5 000001<2><16> (3 bytes)
                # Five leading zeros indicate an arbitrary amplitude 1 to 5 ticks after
                # the preceding point.  The first 2 bits indicate 1 less than the number
                # of ticks from the previous point, and the next 16 bits are a signed
                # amplitude.
                if i + 3 > len(S):
                    print('exiting early', i, len(S))
                    break
                tim, amp = struct.unpack('>Bh', S[i:i + 3])
                # ~ print 'T5', hex(B), hex(amp),

                # mask out the time (6 bits)
                tim = decompressed[-1][0] + (tim & 0x03) + 1

                decompressed.append([tim, amp])

                i += 3
            elif byteType == 6:
                ###
                # Type 6 0000001<1> (1 byte)
                # A leading '0000001' followed by a one bit integer indicates whether we
                # are going up or down. '00000010' means "up", '00000011' means "down".
                # There are no tick and amplitude associated with a type 6 message, it
                # just tells how to interpret the following type 0-4 message.
                # direction = 1 bit integer
                # ~ print 'T6', hex(B),

                if B == 2:
                    directionState = 1
                elif B == 3:
                    directionState = 0
                else:
                    # somethings gone terribly wrong
                    print(panic)
                    break
                i += 1
            elif byteType == 7:
                ###
                # Type 7 0000000<25><16> (6 bytes)
                # Seven leading zeros indicate the traditional 6 byte tuple. This works
                # because the largest tick number that can be generated by our ADC is
                # (a bit more than) 24000000, which fits in 25 bits. This means that
                # our old uncompressed 1.9.3 message bodies are also valid 1.9.4 message
                # bodies, in which all points are encoded as type 7. This message type is
                # used for points that we can't compress into any of the other types,
                # because the jump in ticks or amplitude is too large to fit into the
                # small number of bytes available in those types. The first message and
                # last point of each second are always of this type.
                # ~ print hex(B),byteType, 6
                if i + 6 > len(S):
                    print('exiting early', i, len(S))
                    break
                tim, amp = struct.unpack('>Ih', S[i:i + 6])
                # ~ print 'T7', hex(tim), hex(amp),
                decompressed.append([tim, amp])

                i += 6
            else:
                # something went terribly wrong

                print('danger')
                return None

        return decompressed

    def _decode194(self, S=None):

        # get the string input,
        # we cut off the first 2 bytes (size) because that's part of the
        # ltgfile, and not the message.
        if S is None:
            S = self.messageStr[2:]
        else:
            S = S[2:]

        # the station ID is a string, so no need to use struct
        # but it does tend to be too long
        self.stationID = (S[4:14]).strip()

        # next are a bunch of numbers
        self.timeStart, = struct.unpack('>I', S[14:18])
        self.gpsOffset, = struct.unpack('b', S[18])  # in ns
        self.hfSclkOffset, = struct.unpack('B', S[19])  # sclk between pps an sample 0
        self.hfSclkPeriod, = struct.unpack('B', S[20])  # should always be 5
        self.sclkCount, = struct.unpack('>I', S[21:25])  # total sClk's in 1 second
        self.attenuation, = struct.unpack('B', S[25])
        self.hfThreshold, = struct.unpack('>H', S[26:28])
        self.lfSclkOffset, = struct.unpack('B', S[28])
        self.lfSclkPeriod, = struct.unpack('B', S[29])  # should always be about 192
        self.lfThreshold, = struct.unpack('>H', S[30:32])
        self.hfDcOffset, = struct.unpack('>h', S[32:34])
        self.lfDcOffset, = struct.unpack('>h', S[34:36])
        self.spSclkPeriod, = struct.unpack('>I', S[46:50])
        self.thresholdTab, = struct.unpack('B', S[50])  # 0--old(4bit) 3--new(3bit)
        self.spType, = struct.unpack('B', S[51])  # 0--NoSpectra, 1--Low 2--High, 3--System10
        self.hfLength, = struct.unpack('>H', S[52:54])
        self.lfLength, = struct.unpack('>H', S[54:56])
        self.spLength, = struct.unpack('>H', S[56:58])

        # next we need to read the packages
        self.hfStr = S[58:58 + self.hfLength]
        self.lfStr = S[58 + self.hfLength:58 + self.hfLength + self.lfLength]
        self.spStr = S[58 + self.hfLength + self.lfLength:58 + self.hfLength + self.lfLength + self.spLength]

        self.hf = None
        self.lf = None
        ###
        # next we need to decompress the hf and lf information
        if len(self.hfStr) > 0:
            hf = np.array(self._decompress194(self.hfStr), dtype='f')
            # convert the time to seconds
            hf[:, 0] = ((hf[:, 0] * self.hfSclkPeriod - self.hfSclkOffset)) / float(
                self.sclkCount) + self.gpsOffset * 40e-9
            self.hf = hf
        if len(self.lfStr) > 0:
            lf = np.array(self._decompress194(self.lfStr), dtype='f')
            # convert the time to seconds
            lf[:, 0] = ((lf[:, 0] * self.lfSclkPeriod - self.lfSclkOffset)) / float(
                self.sclkCount) + self.gpsOffset * 40e-9
            lf[:, 1] -= self.lfDcOffset
            self.lf = lf

    def _decode1101(self, S=None):
        # get the string input,
        # we cut off the first 2 bytes (size) because that's part of the
        # ltgfile, and not the message.
        if S is None:
            S = self.messageStr[2:]
        else:
            S = S[2:]

        # the station ID is a string, so no need to use struct
        # but it does tend to be too long
        self.stationID = (S[4:14]).strip()

        # next are a bunch of numbers
        self.timeStart, = struct.unpack('>I', S[14:18])
        self.gpsOffset, = struct.unpack('b', S[18])  # in ns
        self.totalSize, = struct.unpack('>H', S[19:21])
        self.sclkCount, = struct.unpack('>I', S[21:25])  # total sClk's in 1 second
        self.attenuation, = struct.unpack('B', S[25])  # in dB
        self.timeFirmware, = struct.unpack('>I', S[26:30])

        self.lf = None
        self.hf = None
        # what follows from this point are submessages, each with their
        # own formatting.

        # ~ print self.stationID
        # ~ print self.timeStart
        # ~ print self.gpsOffset
        # ~ print self.totalSize, self.size
        # ~ print self.sclkCount
        # ~ print self.attenuation
        # ~ print self.timeFirmware

        i0 = 30
        delayed = []
        while i0 + 3 <= self.size:
            # these sizes are in the message sent by the lightning sensor,
            # so the size is in network byte order, not little endian
            subSize, subMagic = struct.unpack('>HB', S[i0:i0 + 3])
            if subMagic == 49:
                # 0x31 - HF data
                # ~ print subSize, subMagic, 'HF'
                self.__decode1101HF(S[i0:i0 + subSize])
            elif subMagic == 50:
                # 0x32 - LF data
                # ~ print subSize, subMagic, 'LF'
                self.__decode1101LF(S[i0:i0 + subSize])
            elif subMagic == 51:
                # 0x33 - GPS data
                # ~ print subSize, subMagic, 'GPS'
                self.__decode1101GPS(S[i0:i0 + subSize])
            elif subMagic == 52:
                # 0x34 - Spectra
                # ~ print subSize, subMagic, 'Spectra'
                self.__decode1101Spec(S[i0:i0 + subSize])
            elif subMagic == 53:
                # 0x35 - Text Message
                # ~ print subSize, subMagic, 'Text'
                self.__decode1101Text(S[i0:i0 + subSize])
            elif subMagic == 54:
                # 0x36 - TOGA
                # this is based on LF data
                if self.lf is None:
                    delayed.append(S[i0:i0 + subSize])
                    i0 += subSize
                    continue
                # ~ print subSize, subMagic, 'TOGA'
                self.__decode1101Toga(S[i0:i0 + subSize])
            elif subMagic == 55:
                # 0x37 - ELF
                # this is based on LF data
                if self.lf is None:
                    delayed.append(S[i0:i0 + subSize])
                    i0 += subSize
                    continue
                # ~ print subSize, subMagic, 'ELF'
                self.__decode1101ELF(S[i0:i0 + subSize])
            else:
                # what went wrong here?
                print(subSize, subMagic, 'error')

            i0 += subSize

        # loop over delayed strings
        for S in delayed:
            # we delayed decoding because we needed an LF string to get
            # the timing information.  But, there's a chance we still
            # don't have an LF string.  In that case, I guess we won't
            # do decoding.
            if self.lf is None:
                continue
            i0 = 0
            subSize, subMagic = struct.unpack('>HB', S[i0:i0 + 3])
            if subMagic == 54:
                # 0x36 - TOGA
                # this is based on LF data
                # ~ print subSize, subMagic, 'TOGA'
                self.__decode1101Toga(S[i0:i0 + subSize])
            elif subMagic == 55:
                # 0x37 - ELF
                # this is based on LF data
                # ~ print subSize, subMagic, 'ELF'
                self.__decode1101ELF(S)

    def __decode1101HF(self, S):
        # ~ print 'reading', self.version, 'HF'
        size, magic = struct.unpack('>HB', S[:3])

        ###
        # idiot checking
        if magic != 49:
            # this isn't HF data!
            raise ValueError('This is not an HF String').with_traceback(magic)

        self.hfSclkOffset, = struct.unpack('B', S[3])  # sclk between pps an sample 0
        self.hfThreshold, = struct.unpack('>H', S[4:6])
        self.hfDcOffset, = struct.unpack('>h', S[6:8])
        ###
        # I'm not sure what's going on with the blackouts,
        # the example I'm looking at has all blackout related numbers as 0
        # so I'm also not sure I'm decoding them correctly
        self.hfBlkOffset, = struct.unpack('>I', '\x00' + S[8:11])  # 3 byte number!
        self.hfBlkOffset, = struct.unpack('>H', S[11:13])
        self.hfBlkOffset, = struct.unpack('>I', '\x00' + S[13:16])  # 3 byte number!
        # note, hfSclkPeriod is no longer stored, because it's always 5
        self.hfSclkPeriod = 5
        # ~ print self.hfSclkOffset
        # ~ print self.hfThreshold
        # ~ print self.hfDcOffset

        ###
        # the remainder of the string is 1.9.4 compressed waveshape
        self.hfStr = S[16:]
        if len(S) <= 16:
            # then there's no HF string
            self.hf = np.array([[0, 0]])  # placeholder
            return
        hf = np.array(self._decompress194(S[16:]), dtype='f')
        # convert time to seconds

        hf[:, 0] = ((hf[:, 0] * self.hfSclkPeriod - self.hfSclkOffset)) / float(self.sclkCount) + self.gpsOffset * 40e-9
        # DC offset
        hf[:, 1] -= self.hfDcOffset
        self.hf = hf

    def __decode1101LF(self, S):
        # ~ print 'reading', self.version, 'LF'
        size, magic = struct.unpack('>HB', S[:3])

        ###
        # idiot checking
        if magic != 50:
            # this isn't HF data!
            raise ValueError('This is not an LF String').with_traceback(magic)

        self.lfSclkOffset, = struct.unpack('B', S[3])  # sclk between pps an sample 0
        self.lfThreshold, = struct.unpack('>H', S[4:6])
        self.lfDcOffset, = struct.unpack('>h', S[6:8])
        ###
        # filter stuff
        self.lfFiltFreq, = struct.unpack('B', S[8])  # should be 50 or 60
        self.lfFiltAmp, = struct.unpack('>H', S[9:11])
        self.lfFiltOffset, = struct.unpack('>H', S[11:13])  # between the maximum of the filter and PPS
        # note, lfSclkPeriod is no longer stored, because it's always 192
        self.lfSclkPeriod = 192

        # ~ print magic, '{0:02x}'.format( ord(S[2]) )
        # ~ print self.lfSclkOffset, '{0:02x}'.format( ord(S[3]) )
        # ~ print self.lfThreshold
        # ~ print self.lfDcOffset
        # ~ print self.lfFiltFreq
        # ~ print self.lfFiltAmp
        # ~ print self.lfFiltOffset

        ###
        # the remainder of the string is 1.9.4 compressed waveshape
        self.lfStr = S[13:]
        if len(S) <= 13:
            # then there's no HF string
            self.lf = np.array([[0, 0]])  # placeholder
            return
        lf = np.array(self._decompress194(S[13:]), dtype='f')
        # convert time to seconds
        # note, hfSclkPeriod is no longer stored, because it's always 5
        lf[:, 0] = ((lf[:, 0] * self.lfSclkPeriod - self.lfSclkOffset)) / float(self.sclkCount) + self.gpsOffset * 40e-9
        # DC offset
        lf[:, 1] -= self.lfDcOffset
        self.lf = lf

    def __decode1101GPS(self, S):
        # ~ print 'reading', self.version, 'GPS'
        size, magic = struct.unpack('>HB', S[:3])

        ###
        # idiot checking
        if magic != 51:
            # this isn't HF data!
            raise ValueError('This is not an GPS String').with_traceback(magic)

        self.gpsTracked, = struct.unpack('B', S[3])  # num satellites tracked (hopefully not 0)
        self.gpsVisible, = struct.unpack('B', S[4])  # num satellites visible
        self.gpsLatitude, = struct.unpack('>i', '\x00' + S[5:8])  # 3byte number
        self.gpsLongitude, = struct.unpack('>i', '\x00' + S[8:11])  # 3byte number

        # correct the latitude and longitude
        self.lat = self.gpsLatitude * 90. / 2 ** 23
        self.lon = self.gpsLongitude * 90. / 2 ** 23

    def __decode1101Spec(self, S):
        # ~ print 'reading', self.version, 'Spec'
        size, magic = struct.unpack('>HB', S[:3])

        ###
        # idiot checking
        if magic != 52:
            # this isn't HF data!
            raise ValueError('This is not an Spec String').with_traceback(magic)

        self.spSclkPeriod = struct.unpack('>I', '\x00' + S[3:6])

        # the string
        self.spStr = S[6:]

        # decode the spectra
        self.sp = struct.unpack('>512H', S[6:])

    def __decode1101Text(self, S):
        # ~ print 'reading', self.version, 'Text'
        size, magic = struct.unpack('>HB', S[:3])

        ###
        # idiot checking
        if magic != 53:
            # this isn't HF data!
            raise ValueError('This is not an Text String').with_traceback(magic)

        # this one is pretty easy...
        self.text = S[3:]

    def __decode1101Toga(self, S):
        """
        IF multiple Toga's are present in a second, the this message
        will be repeated.
        The 8bit sample amplituede are constructed from the 16bit input as:
        m = max( abs(16bit waveform amplitudes) )
        8bit waveform = ((((16bit waveform)<<8) +1 )/m)>>1

        The 16bit amplitudes can be approximately reconstructed using
        *m>>7
        the approximation is exact if m<128

        The documentation *does not* specify the data sampling rate!
        This is what I've reconstructed with converstations with
        James Brundel and Stan Heckman:
        The data rate is 1 sample every 3072 sclks, which is 1 sample
        every 16 LF samples which seems plausible.  The data is aslo
        put through a narrow band filter, to match other WWLLN sensors.
        This filter adds a 81972 sclk sample delay to the waveform.
        All of these issues are corrected in this module.
        """
        # ~ print 'reading', self.version, 'Toga'
        size, magic = struct.unpack('>HB', S[:3])

        # have we already seen a Toga?
        if self.toga is None:
            # no, we haven't
            self.toga = []
            self.togaSclkOffset = []
            self.togaMaxAmplitude = []

        ###
        # idiot checking
        if magic != 54:
            # this isn't HF data!
            raise ValueError('This is not an TOGA String').with_traceback(magic)

        self.togaSclkOffset.append(struct.unpack('>i', S[3:7])[0])
        self.togaMaxAmplitude.append(struct.unpack('>h', S[7:9])[0])
        # ~ lf[:,0] = ((lf[:,0]*self.lfSclkPeriod - self.lfSclkOffset))/float(self.sclkCount) + self.gpsOffset*40e-9
        # then the toga itself
        d = np.zeros([64, 2])
        d[:, 1] = struct.unpack('>64b', S[9:])
        d[:, 1] *= abs(self.togaMaxAmplitude[-1]) >> 7
        # ~ d[:,0] = ((np.arange(64)*self.hfSclkPeriod*2**8)+self.togaSclkOffset[-1])/float(self.sclkCount) + self.gpsOffset*40e-9
        d[:, 0] = ((np.arange(64) * 3072) + self.togaSclkOffset[-1] - 81792) / float(
            self.sclkCount) + self.gpsOffset * 40e-9
        self.toga.append(d)

    def __decode1101ELF(self, S):
        """
        Documentation for the ELF data is lacking, and I'm not 100% sure
        that it will end up being useful.  The ELF data is generated by
        running the LF waveform (before decimation) through an LPF and
        summation.  There is 1 ELF sample every 2048 samples of LF data,
        yielding 305-306 samples every second.
        """
        # ~ print 'reading', self.version, 'ELF'
        size, magic = struct.unpack('>HB', S[:3])

        ###
        # idiot checking
        if magic != 55:
            # this isn't HF data!
            raise ValueError('This is not an ELF String').with_traceback(magic)

        self.elfClkOffset = struct.unpack('>H', S[3:5])

        ###
        # the rest of the message is samples,
        # the data is stored in 2 byte samples, but there can be a variable
        # number of them.  So, we'll get the number of samples from the
        # size of the file
        N = (size - 5) / 2
        self.elf = np.zeros([N, 2])
        # these are the amplitudes
        self.elf[:, 1] = struct.unpack('>%ih' % N, S[5:])
        # these are the times

        self.elf[:, 0] = ((np.arange(N) * 2048 + self.elfClkOffset) * self.lfSclkPeriod + self.lfSclkOffset) / float(
            self.sclkCount) + self.gpsOffset * 40e-9


class LocFile():
    def __init__(self, filelike):

        # build the catalog
        self.read(filelike)

    def read(self, filelike=None):
        # open the input file for reading
        if isinstance(filelike, basestring):
            # it's a string, try and open
            self.f = open(filelike, 'r')
        elif isinstance(filelike, file):
            # then it's a file
            self.f = filelike

        self.stationID = np.array([], dtype='|S6')
        self.stationLat = np.array([], dtype='float64')
        self.stationLon = np.array([], dtype='float64')
        self.stations = {}

        lines = self.f.readlines()
        for l in lines:
            l = l.strip().split()
            stationID = l[0]
            stationLat = float(l[1])
            stationLon = float(l[2])

            # expand the arrays and append
            N = self.stationID.shape[0]
            self.stationID.resize([N + 1])
            self.stationID[-1] = stationID
            self.stationLat.resize([N + 1])
            self.stationLat[-1] = stationLat
            self.stationLon.resize([N + 1])
            self.stationLon[-1] = stationLon

            # and the dictionary
            self.stations[stationID] = stationLat, stationLon

    def close(self):
        self.f.close()


class FeedReceiver(threading.Thread):
    def __init__(self, config=None, **kwargs):

        ###
        # initialize all the threading stuff
        threading.Thread.__init__(self)

        # best guess default settings
        self.partnerId = None  # we really do need one
        self.ip = ['184.72.125.75', '107.23.153.83']
        self.port = 2324
        self.feedType = 1
        self.feedFormat = 1
        self.decode = True  # should we bother decoding the strings at all?

        # initial parameters can also be set with a config file
        if config is not None:
            # then we have a config file:
            from ConfigParser import ConfigParser
            import ast
            cfg = ConfigParser()
            cfg.read(self.config)

            for section in cfg.sections():
                for key, value in cfg.items(section):
                    value = ast.literal_eval(value)
                    setattr(self, key, value)

        # were any kwargs passed?
        for key in kwargs:
            setattr(self, key, kwargs[key])

        # which IP should we use?
        self.whichIp = 0

        ###
        # initialize the messages
        self.received = []

        ###
        # set daemon flag so ctrl-c will kill the program
        self.daemon = True

        ###
        # open the socket
        self.open_socket()

    def close_socket(self):
        ###
        # used with reopening socket
        self.socket.close()

    def open_socket(self):
        ###
        # the reciever has a socket set up to pull the data feed
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip[self.whichIp], self.port))

        ###
        # generate the request string that tells EN what to send us
        requestStr = '{"p":"%s","v":3,"f":%i,"t":%i,"class":3,"meta":true}' % (
        self.partnerId, self.feedFormat, self.feedType)

        # ~ print requestStr
        self.socket.sendall(requestStr)

        ###
        # clean up the sending part of the socket
        self.socket.shutdown(socket.SHUT_WR)

    def loop_binary_old(self):
        ###
        # loop over messages
        message = ""
        while True:
            if len(message) < 2:
                message += self.socket.recv(1024)
            messageLen = struct.unpack('>H', message[:2])[0]
            if DEBUGGING > 2:
                print('new message', messageLen)

            ###
            # loop over recieves
            while len(message) < messageLen:
                message += self.socket.recv(1024)

            ###
            # Check checksum
            S = message[:messageLen]
            if struct.unpack('B', S[-1])[0] != checksum(S[:-1]):
                if DEBUGGING > 0:
                    print('bad checksum!! %i != %i' % (struct.unpack('B', S[-1])[0], checksum(S[:-1])))
                ###
                # restart the socket
                self.close_socket()
                self.whichIP = (self.whichIp + 1) % len(self.Ip)
                self.open_socket()
                message = ""
                continue
            elif DEBUGGING > 2:
                print
                'message good'

            ###
            # lets decode the message
            if messageLen == 32:
                # it's a pulse
                try:
                    S = message[:messageLen]
                    self.received.append(Pulse(message[:messageLen]))
                except:
                    # something went wrong with the string, even though
                    # the checksum worked out...
                    # skip on; there's a good chance we'll have to reopen the feed
                    if DEBUGGING > 0:
                        print
                        'Bad Pulse Message!'
                    message = message[messageLen:]
                    continue
            elif messageLen == 56:
                # it's a flash
                try:
                    self.received.append(Flash(message[:messageLen]))
                except:
                    # something went wrong with the string, even though
                    # the checksum worked out...
                    # skip on; there's a good chance we'll have to reopen the feed
                    if DEBUGGING > 0:
                        print('Bad Flash Message!')
                    message = message[messageLen:]
                    continue
            else:
                # it must be a flash with pulses
                try:
                    flash = Flash(message[2:58])
                except:
                    # something went wrong with the string, even though
                    # the checksum worked out...
                    # skip on; there's a good chance we'll have to reopen the feed
                    if DEBUGGING > 0:
                        print('Bad Flash+Pulse Message!')
                    message = message[messageLen:]
                    continue
                iPulse = 58
                while iPulse < messageLen - 1:
                    flash.append_pulse(Pulse(message[iPulse:iPulse + 32]))
                    iPulse += 32
                self.received.append(flash)
            # remove this message from the stuff we've read
            message = message[messageLen:]

    def loop_binary(self):
        message = ""
        while True:
            # first thing we do, always is get a packet of data
            # get_packet handles what to do if the socket needs to be
            # reset
            message = self.get_packet(message)

            # if the message is too short to get the length, we'll need
            # another one
            if len(message) < 2:
                continue

            # get the message length from the first 2 bytes of the message
            if self.feedType == 3:
                messageLen, = struct.unpack('>H', message[:2])
            else:
                messageLen, = struct.unpack('B', message[0])

            print(messageLen, len(message))
            # make sure the message is long enough
            if len(message) < messageLen:
                continue

            ###
            # split out the message
            S = message[:messageLen]

            # decode the message?
            if not self.decode:
                # we don't decode at all
                self.received.append(S)
            elif messageLen == 32:
                # it's a pulse
                self.received.append(Pulse(S))
            elif messageLen >= 56:
                # it must be a flash, or a combo
                self.received.append(Flash(S))
            else:
                # i'm not sure what it is
                pass

            # update the message
            message = message[messageLen:]

    def loop_json(self):
        message = ""
        while True:
            # first thing we do, always is get a packet of data
            # get_packet handles what to do if the socket needs to be
            # reset
            message = self.get_packet(message)

            # if the message is too short to get the length, we'll need
            # another one
            if len(message) < 4:
                continue

            # parse the message length so we know how much to get
            # ~ print message[:10], len( message ), len(message[:4])
            messageLen, = struct.unpack('>I', message[:4])

            # make sure the message is long enough
            if len(message) < messageLen:
                continue

            ###
            # split out the message
            S = message[4:messageLen]

            # now, what type of message is this.  We could look at the
            # config, but it's not trustworthy.  There are 2 options,
            # flash, pulse
            if not self.decode:
                # we don't decode at all
                self.received.append(S)
            elif 'icMultiplicity' in S:
                # this field only exists for flashes
                self.received.append(Flash(S))
            else:
                # it must be a pulse
                self.received.append(Pulse(S))
            message = message[messageLen:]

    def get_packet(self, message=""):
        try:
            S = ""
            tNow = time.time()
            while len(S) == 0:
                S = self.socket.recv(4)
                if time.time() - tNow > 20:
                    # it's been more than 20 seconds, and
                    # we haven't gotten a packet, not even a keepalive
                    # throw an error (that will restart the socket)
                    raise Exception
            return message + S
        except:
            # ~ print 'socket failed \n\n\n\n\n\n\n'
            # things have gone wrong, restart the feed
            self.close_socket()
            self.whichIp = (self.whichIp + 1) % len(self.ip)
            self.open_socket()
            return ""

    def run(self):
        if self.partnerId is None:
            print
            'no Partner ID!'
            return
        if self.feedFormat == 1:
            # it's a json feed.
            # csv feed uses v:2 in the request string, which is not
            # implemented
            self.loop_json()
        elif self.feedFormat == 2:
            # it's a binary feed
            self.loop_binary()
        else:
            raise ValueError("Unknown feedFormat:%i, not sure how to decode" % self.feedFormat)


########################################################################
# Functions

def xcorr(x, y, tau, trange, dtmin=0.0001):
    """computes the cross correlation of x and y at lag tau, where
    x and y are the waveshapes stored in a datafile, which means they
    are arrays of time, amplitude pairs.

    Since the waveshapes are not sampled at equal intervals, this does
    linear interpolation to improve the correlation estimation

    Note, this needs to be shoved over to cython asap
    """

    ###
    # This function has been built into the lxcTools library, but that
    # needs to be compiled to work, which may be difficult for some
    # people on some operating systems.
    # so, if the cython library fails, this will fall back on a (much
    # slower) pure python implementation
    try:
        import enipy.lxcTools as lct
        return lct.xcorr(x, y, tau, trange)
    except:
        import warnings
        warnings.warn('xcorr - Cython library not working, performance will suffer', Warning)

    return lct.xcorr(x, y, tau, trange, dtmin=dtmin)
    # these numbers will contain a running sum of the correlation
    N = 0  # the number of terms in the sum
    xc = 0

    # sample x, interpolate y
    j = 0
    for i in range(x.shape[0]):
        xt = x[i, 0]
        xv = x[i, 1]

        # find the first value of yt-tau larger than xt
        # note, we don't reset j, because xt is always increasing
        while y[j, 0] + tau < xt:
            j += 1
            # catch edgecase
            if j >= y.shape[0]:
                break
        # catch end edgecase again
        if j >= y.shape[0]:
            break
        # catch the beginning edgecase
        if j == 0:
            continue

        # y[j,0] is the first sample > xt, so that means y[j-1,0] is < xt
        # we will linearly interpolate to get the value at xt
        # calculate the slope of the line
        m = (y[j, 1] - y[j - 1, 1]) / (y[j, 0] - y[j - 1, 0])
        # calculate the expected value
        yv = m * (xt + tau - y[j - 1, 0]) + y[j, 1]

        xc += yv * xv
        N += 1

    # sample y, interpolate x

    return xc / N


def integrate(x):
    """
    return the integral of the waveshape
    """
    ###
    # not implemented yet
    return


######
# Functions needed to decode reports and feeds
def timeStamp2time(S):
    ###
    # converts a timeStamp into a time in seconds
    # this would be simpler if we didn't want the fractional part
    # in ns
    if S[-1] == 'Z':
        S = S[:-1]
    if '.' in S:	#amazingly, sometimes a fractional part isn't passed
        nano    = S.split('.')[1]
    else:
        nano = '0'

    while len(nano) < 9:
        nano += '0'
        nano   = int( nano )
        #there are a couple of different formats that I'd like to support
        try:
            sec    = calendar.timegm( time.strptime( S[:19], '%Y-%m-%dT%H:%M:%S' ) )
        except:
            sec    = calendar.timegm( time.strptime( S[:19], '%Y/%m/%dT%H:%M:%S' ) )
            t      =  sec + nano/1e9
    return t, sec, nano

def time2timeStamp( t ):
    S = time.strftime( '%Y-%m-%dT%H:%M:%S', time.gmtime( t ) )
    #  that gets us to the second, we still have to deal with the fractional part
    S += ('%0.9f'%np.modf( t )[0])[1:]
    return S

def checksum(S):
    """computes the checksum of ENTLN feed string
    """
    ###
    # computes the checksum as per EN documentation
    N = len(S)
    # this unpacks each byte
    l = struct.unpack('%iB' % N, S)

    return (256 - sum(l) % 256) % 256


def type2str(t):
    '''Converts flash and pulse 'types' into a human readable string
    '''
    if t == 0:
        return 'CG'
    elif t == 1:
        return 'IC'
    elif t == 9:
        return 'keep alive'
    elif t == 40:
        return 'WWLLN'
    else:
        raise ValueError('Unknown type: %i' % t)


def guess_strtype(S):
    """There are a lot of different formats for data floating around
    earthnetworks.  This tries to guess what type of string you happen
    to have, in case you don't already know

    there are 3 formats:
        json, csv, binary
    for 3 types of data
        flash, pulse, combo
    from 2 sources
        feed, report

    returns 3 strings in a tuple of :
        <format>, <type>, <source>
    """

    ###
    # MSSQL
    # for these, we pass dictionaries instead of strings
    if isinstance(S, dict):
        # then this is MSSQL
        # flash or pulse?
        if 'Flash_History_ID' in S.keys():
            # it's a flash
            return 'mssql', 'flash', 'report'
        elif 'LtgFlashPortions_History_ID' in S.keys():
            # it's a pulse
            return 'mssql', 'pulse', 'report'
        else:
            # i don't know what it is
            raise ValueError('%s is not a known type' % repr(S))

    ###
    # json
    # json files should always start and end with curly bracket
    # pulse report
    # {"type":1,"timeStamp":"2017-02-13T00:00:26.7183463","longitude":-85.60853,"latitude":33.90489,"height":15299.0,"amplitude":473.0,"errorEllipse":{"maj":0.141,"min":0.14,"b":33.6},"numberSensors":6}
    # flash report
    # {"type":0,"timeStamp":"2017-02-01T00:19:49.0936288","longitude":-68.10588,"latitude":-16.76447,"height":0.0,"amplitude":-47108.0,"numberSensors":16,"icMultiplicity":0,"cgMultiplicity":1,"startTime":"2017-02-01T00:19:49.0936288","endTime":"2017-02-01T00:19:49.0936288","durationSeconds":0.0,"minLatitude":-16.76447,"minLongitude":-68.10588,"maxLatitude":-16.76447,"maxLongitude":-68.10588,"portions":[{"type":0,"timeStamp":"2017-02-01T00:19:49.0936288","longitude":-68.10588,"latitude":-16.76447,"height":0.0,"amplitude":-47108.0,"errorEllipse":{"maj":0.492,"min":0.159,"b":104.2},"numberSensors":16}]}
    # combo report
    # {"type":0,"timeStamp":"2017-02-01T20:24:57.2901218","longitude":-68.0087,"latitude":-7.48562,"height":0.0,"amplitude":-59699.0,"numberSensors":7,"icMultiplicity":0,"cgMultiplicity":2,"startTime":"2017-02-01T20:24:57.2901218","endTime":"2017-02-01T20:24:57.3120733","durationSeconds":0.021951445,"minLatitude":-7.5689,"minLongitude":-68.00871,"maxLatitude":-7.48562,"maxLongitude":-68.00871,"portions":[{"type":0,"timeStamp":"2017-02-01T20:24:57.2901218","longitude":-68.0087,"latitude":-7.48562,"height":0.0,"amplitude":-59699.0,"errorEllipse":{"maj":0.707,"min":0.185,"b":38.4},"numberSensors":6},{"type":0,"timeStamp":"2017-02-01T20:24:57.3120733","longitude":-67.90836,"latitude":-7.5689,"height":0.0,"amplitude":-39619.0,"errorEllipse":{"maj":1.916,"min":0.542,"b":35.5},"numberSensors":7}]}
    # pulse feed
    # {"time":"2017-02-26T17:32:29.817443878Z","type":0,"latitude":-21.5043742,"longitude":-49.1724032,"peakCurrent":-21356.0,"icHeight":0.0,"numSensors":16,"eeMajor":278.0,"eeMinor":200.0,"eeBearing":21.8}
    # flash feed
    # {"time":"2017-02-26T17:30:52.579925000Z","type":0,"latitude":-37.7905,"longitude":-61.2728,"peakCurrent":-55520.0,"icHeight":0.0,"numSensors":6,"icMultiplicity":0,"cgMultiplicity":1,"startTime":"2017-02-26T17:30:52.579925000Z","duration":0,"ulLatitude":-37.7905,"ulLongitude":-61.2728,"lrLatitude":-37.7905,"lrLongitude":-61.2728}

    if S[0] == '{' and S[-1] == '}':
        # so, it's a json.  is it flash or pulse, and is it feed or report

        # flash or pulse?
        # only pulse data has error ellipse info (but sometimes it's missing)
        # only flashes have extent info (but sometimes it's missing)
        # only flashes have multiplicity information (and it's always included)
        # combo reports have both flash and pulse data in them, they include a second called 'portions'
        if 'portions' in S:
            # it's a combo report
            return 'json', 'combo', 'report'
        if 'icMultiplicity' in S:
            # it's a flash string
            if 'amplitude' in S:
                # it's a report
                return 'json', 'flash', 'report'
            else:
                # it's a feed
                return 'json', 'flash', 'feed'
        else:
            # it's a pulse
            if 'amplitude' in S:
                # it's a report
                return 'json', 'pulse', 'report'
            else:
                # it's a feed
                return 'json', 'pulse', 'feed'

    ###
    # CSV files are only available as reports
    # (actually, v2 feeds also have csv, but I don't support v2 data)
    # flash report
    # type,timestamp,latitude,longitude,peakcurrent,icheight,numbersensors,icmultiplicity,cgmultiplicity,starttime,endtime,duration,ullatitude,ullongitude,lrlatitude,lrlongitude
    # pulse report
    # type,timestamp,latitude,longitude,peakcurrent,icheight,numbersensors,majoraxis,minoraxis,bearing

    if S.count(',') == 15:
        # flash CSV
        return 'csv', 'flash', 'report'
    elif S.count(',') == 9:
        # pulse
        return 'csv', 'pulse', 'report'

    ###
    # flat files
    # 6268355705,
    # b6ca54c8-83f5-4cd8-9ab4-84d47bb637b5,
    # 298b7a2d-90dd-43b4-8589-8558c7cd7b4f,
    # 4/27/2017 12:00:00 AM,
    # 2017-04-27T00:00:00.017927240,
    # 32.8429853,-91.8318796,18236.6,1,3782,
    # "{"ee":{"maj":0.434,"min":0.402,"b":146.0},"v":"4.0.2.3","ns":19,"so":{"PLQDC":0.0,"COVNT":50.0,"QTMNP":65.0,"WLDWL":83.0,"HVNRS":187.0,"YNTSM":216.0,"THBNS":223.0,"TSCLB":393.0,"MILDR":504.0,"SHEFF":510.0,"SNNTP":522.0,"FRTGB":556.0,"BYTWN":559.0,"ZULCH":570.0,"WXHCH":620.0,"HSTJC":700.0,"ADWLL":702.0,"DNTNS":721.0,"WSTPS":734.0}}",
    # "PLQDC=0,COVNT=50,QTMNP=65,WLDWL=83,HVNRS=187,YNTSM=216,THBNS=223,TSCLB=393,MILDR=504,SHEFF=510,SNNTP=522,FRTGB=556,BYTWN=559,ZULCH=570,WXHCH=620,HSTJC=700,ADWLL=702,DNTNS=721,WSTPS=734,",
    # 100,4/26/2017 8:00:11 PM,LtgInsertFlashPortion_pr
    #
    # FlashPortionID,FlashPortionGUID,FlashGUID,Lightning_Time,Lightning_Time_String,Latitude,Longitude,Height,Stroke_Type,Amplitude,Stroke_Solution,Offsets,Confidence,LastModifiedTime,LastModifiedBy
    #
    # flat files are really hard to test.  They're csv files, but they
    # contain a json string in the middle which contains an undetermined
    # number of ,'s.
    # to get the flat files, I look for GUID's, which don't show up in
    # any other text format.
    # in pulse flat files, GUID's are the second and third fields
    # in flash flat files, GUID's are just the second filed
    s = S.split(',')
    if 'FlashPortionGUID' in S and 'FlashGUID' in S:
        return 'flat', 'pulse', 'report'
    elif 'FlashGUID' in S:
        return 'flat', 'flash', 'report'

    # alternative method, for if we don't pass the header
    def validate_guid(S):
        flatFile = False
        if len(S.strip()) == 36:
            # check the dashes
            dashes = [8, 13, 18, 23]
            flatFile = True
            for i in dashes:
                flatFile &= (S[i] == '-')
                # I haven't bothered checking to see if it's LtgFlash, or LtfFlashPortions
        return flatFile

    if validate_guid(s[2]) and validate_guid(s[1]):
        return 'flat', 'pulse', 'report'
    elif validate_guid(s[1]):
        return 'flat', 'flash', 'report'

    ###
    # binary,
    # we've saved this for last, because it's a little harder
    # binary only exists in a feed, and comes in all 3 types.
    # we'll determine the type by looking at the first 2 bytes,
    # which stores the size of the string.
    try:
        messageLen, = struct.unpack('B', S[0])
    except:
        # if this failed, it means that it's not binary either,
        # so, it must be something else
        raise ValueError('poorly formatted binary string?: ' + repr(S))
    if messageLen == 32:
        return 'binary', 'pulse', 'feed'
    elif messageLen == 56:
        return 'binary', 'flash', 'feed'
    else:
        # the combo feeds use 2 bytes for the length
        # this is 2 bytes, followed by a flash, followed by a sequence of pulses, followed by a checksum
        messageLen, = struct.unpack('>H', S[:2])
        if (messageLen - 56 - 3) % 32 == 0:
            return 'binary', 'combo', 'feed'

    # default result is an error
    raise ValueError('could not guess string type: ' + repr(S))


########################################################################
# Functions needed for raw data decoding
# there's probably no reason to call these directly

def boundary_next(level):
    # were we passed a valid level?
    level = boundary_floor(level)
    level += 2 ** (max(level.bit_length() - 3, 0))
    # the digitizer is 14 bits, and the least 2 sig bits are meaningless
    while level % 4 != 0:
        level += 2 ** (max(level.bit_length() - 3, 0))
    return level


def boundary_prev(level):
    # to go down, we'll use the floor function already defined.
    # if we're already on the floor, we'll need to subtract 1 first
    i = 0
    output = level
    while output == level:
        output = boundary_floor(level - i)
        i += 1
    return output


def boundary_floor(level):
    # what is the closest boundary lower than or equal to this level
    # this is more complicated by a lot because the least 2 significant
    # bits are meaningless in the digitizer (14 bit AD)
    level = level >> 2
    N = level.bit_length()
    if N <= 3:
        return level << 2
    else:
        return (level >> N - 3) << N - 1


def byte2type(B):
    ### reads in a byte, and converts to a type, for 1.9.4 compressed data

    # is this a string or a number?  We can only shift numbers
    if isinstance(B, basestring):
        B, = struct.unpack('B', B)
    # ~ print B
    for i in range(8):
        if B >> 7 - i == 1:
            return i
    # if we haven't already
    return i