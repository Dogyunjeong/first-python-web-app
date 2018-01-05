import threading, math, dateutil.parser
from numpy import genfromtxt
from datetime import datetime, timezone, timedelta

class DataModel():
#    each row has 4 columns(timestamp, id, type, status)
    dataHead = list()
    data = list()
    dayList = list()
    selector = {}
    pre_popular = {}
    recentData = {}
    date_format = '%Y-%m-%d'

    def __init__(self, readRef):
        self.processing(readRef)

        
    def setInterval(self, func, seconds):
        def funcWrapper():
            self.setInterval(func, seconds)
        t = threading.Timer(seconds, funcWrapper)
        t.start()
        return t
        
    def readCsv(self):
        temp = genfromtxt('report.csv', delimiter=',', dtype=str)
        self.dataHead = temp[0:0]
        self.data = temp[1:]
        
    def processingFn(self):
        self.readCsv()
        self.preReporting()
#        Each hour

    def processing(self, seconds):
        self.processingFn()
        return self.setInterval(self.processingFn, seconds)

    def calcOccurence(self, targetDayStr, deviceId):
        if targetDayStr not in self.pre_popular:
            self.pre_popular[targetDayStr] = {}
            self.dayList.append(targetDayStr)
        
        if deviceId in self.pre_popular[targetDayStr]:
            self.pre_popular[targetDayStr][deviceId] += 1
        else:
            self.pre_popular[targetDayStr][deviceId] = 1
            
    def addSelector(self, deviceType, conn):
        if deviceType not in self.selector['type']:
            self.selector['type'].append(deviceType)
        if conn not in self.selector['connection']:
            self.selector['connection'].append(conn) 

    def dayDiff(self, datetime1, datetime2):
        diff = datetime1 - datetime2
        return diff.days

    def trimTimeStr(self, payload, dayDiff=0):
        targetTime = dateutil.parser.parse(payload) - timedelta(days=dayDiff)
        targetDayStr = targetTime.strftime(self.date_format)
        return targetDayStr
    
    def strDayDiff(self, dayStr1, dayStr2):
        day1 = dateutil.parser.parse(dayStr1)
        day2 = dateutil.parser.parse(self.trimTimeStr(dayStr2))
        return self.dayDiff(day1, day2)
 
    def eachStatusReport(self, payload):
        lastIdx = payload['lastIdx']
        timePoint = payload['time']
        reqType = payload['type']
        reqConn = payload['connection']
        recentData = {}
        
        for i in range(lastIdx, 0, -1):
            row = self.data[i]
            if self.strDayDiff(timePoint, row[0]) <= 30:
                dayStr = self.trimTimeStr(row[0])

                if row[2] == reqType and row[3] == reqConn:
                    if dayStr not in recentData:
                        recentData[dayStr] = {}
                        recentData[dayStr][row[2]] = 1
                    elif row[2] not in recentData[dayStr]:
                        recentData[dayStr][row[2]] = 1
                    else:
                        recentData[dayStr][row[2]] += 1
        return recentData


    def statusReporting(self):
        # Assume, last day is previous than now
        # last 30 days is from the date of last data
        lastIdx = len(self.data) - 1
        time = self.trimTimeStr(self.data[lastIdx][0])
        recentData = {}
        for devType in self.selector['type']:
            recentData[devType] = {}
            for conn in self.selector['connection']:
                payload = {
                    'time': time,
                    'lastIdx': lastIdx,
                    'type': devType,
                    'connection': conn
                }
                recentData[devType][conn] = self.eachStatusReport(payload)
        self.recentData = recentData   

    def preReporting(self):
        self.selector = {
            'type': list(),
            'connection': list()
        }
        self.pre_popular = {}

        for row in self.data:
            targetDayStr = self.trimTimeStr(row[0])   
            self.calcOccurence(targetDayStr, row[1])
            self.addSelector(row[2], row[3])
    
        self.statusReporting()
    
    def pickTopTen(self, targetDic):
        popular = {
            'num': list(),
            'device': list(),
        }
        for key, value in targetDic.items():
            tempOne = { 'device': False, 'num': False}
            tempTwo = {}
            if len(popular['num']) < 10:
                popular['num'].append(value)
                popular['device'].append(key)
            else:
                for idx, num in enumerate(popular['num']):
#                    ignore same popularity
                    if value > num and tempOne['device'] == False:
                        tempOne['device'] = popular['device'][idx]
                        tempOne['num'] = popular['num'][idx]
                        popular['device'][idx] = key
                        popular['num'][idx] = value
                    if tempOne['num'] > num:
                        tempTwo['device'] = popular['device'][idx]
                        tempTwo['num'] = popular['num'][idx]
                        popular['device'][idx] = tempOne['device']
                        popular['num'][idx] = tempOne['num']
                        tempOne = tempTwo
        return popular

    def calcPercentage(self, curr, prev):
        changePercentage = 'none'
        if isinstance(curr, int) and isinstance(prev, int):        
            changePercentage = math.floor(((curr - prev) / prev) * 100) - 100
        return changePercentage

    def findAnWeekAgo(self, time, deviceId):
        prev = 'none'
        if time in self.pre_popular and deviceId in self.pre_popular[time]:
            prev = self.pre_popular[time][deviceId]
        return prev

    def calcChangePercentage(self, payload):
        targetDayStr = self.trimTimeStr(payload['time'])
        print('targetDayStr:', targetDayStr)
        anWeekAgo = self.trimTimeStr(payload['time'], 7)
        deviceId = payload['device']
        
        curr = self.pre_popular[targetDayStr][deviceId]
        prev = self.findAnWeekAgo(anWeekAgo, deviceId)

        return self.calcPercentage(curr, prev)
    
    def getDayInfo(self):
        return self.dayList
    
    def getPopularDevices(self, pickedTime):
        requestTopTen = self.pickTopTen(self.pre_popular[pickedTime])
        requestTopTen['change'] = list()
        for device in requestTopTen['device']:
            requestTopTen['change'].append(self.calcChangePercentage({ 'time': pickedTime, 'device': device }))
        return requestTopTen
    

    def getSelectInfo(self):
        return self.selector

    
    def getRecentInfo(self, payload):
        # Assume, last day is previous than now
        # last 30 days is from the date of last data
        reqType = payload['type']
        reqConn = payload['connection']
        return self.recentData[reqType][reqConn]

