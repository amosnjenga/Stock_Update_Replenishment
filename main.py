import requests,os
from datetime import datetime
from pytz import timezone
from math import trunc
import json

def authentication():
    url = "https://gis.protoenergy.com/portal/sharing/rest/generateToken"
    """ payload = { 'client_id': client_id, 'client_secret': client_secret, 'grant_type': 'client_credentials'}"""

    payload = {'f': 'json',
               'username': os.environ.get('PortalUser'),
               'password': os.environ.get('PortalPassword'),
               'client': 'referer',
               'referer': 'https://gis.protoenergy.com/portal',
               'expiration': '21600'
               }
    data = requests.post(url, payload).json()
    token = str(data['token'])
    return token

class TerminalStocks:
    def __init__(self):
        self.url1 = "https://geoevent.protoenergy.com/arcgis/rest/services/Hosted/openingBalance_calcFS_Replenishment/FeatureServer"
        self.url2 = "https://geoevent.protoenergy.com/arcgis/rest/services/Hosted/Terminals_Replenishment_V1/FeatureServer"
        self.queryUrl = "/0/query"
        self.update = "/0/updateFeatures"
        self.token = authentication()
        self.payload = {"f":"json","token":self.token}

    def request(self,url,payload):
        response = requests.request("POST",url,data=payload).json()
        return response

    def updateFs(self,tid,stockLevel):
        url = self.url2 + self.update
        features = [{"attributes": {"fid": tid, "stocks": stockLevel}}]
        payload = self.payload
        payload["features"] = str(features)
        response = self.request(url,payload)
        return response

    def getDate(self):
        time_zone = timezone('Africa/Nairobi')
        ke_time = datetime.now(time_zone).strftime("%Y-%m-%d")
        return ke_time

    def epochDate(self,ftime):
        time_epoch = trunc(ftime/1000)
        time_date = datetime.fromtimestamp(time_epoch).strftime('%Y-%m-%d')
        return str(time_date)

    def timeDiff(self,ftime):
        time_zone = timezone('Africa/Nairobi')
        time_now = trunc(datetime.now(time_zone).timestamp())
        time_diff = time_now - trunc(ftime/1000)
        return time_diff

    def query(self):
        query = "1=1"
        return query

    def queryFS(self):
        url = self.url1 + self.queryUrl
        payload = self.payload
        payload["where"] = self.query()
        payload["outFields"] = "*"

        response = self.request(url,payload)
        return response

    def queryResult(self):
        ob = []
        data = self.queryFS()
        data = data['features']
        for i in data:
            attributes = i["attributes"]
            ob.append(attributes)

        #print(ob)
        return ob

    def getStocks(self):
        data = self.queryResult()
        terminal_stocks = []
        for i in data:
            obj = {}
            #print(i['dateadded'],self.epochDate(i['dateadded']))
            if self.getDate() == self.epochDate(i['dateadded']):
                obj['container'] = i['container'].strip()
                obj['dateadded'] = i['dateadded']
                obj['stocks'] = i['stocks']
                terminal_stocks.append(obj)
        #print(terminal_stocks)
        return terminal_stocks

    def getContainers(self):
        with open('./Containers/containers.json') as json_file:
            containers = json.load(json_file)
        containers = containers["containers"]

        #for i in containers:
            #print(i)
        return containers

    def stocksUpdate(self):
        data = self.getStocks()

        recent_stock = []
        for i in data:
            #time_diff = self.timeDiff(i['dateadded'])
            obj={}
            #print(i['container'],time_diff)
            if self.timeDiff(i['dateadded']) < 2000:
                obj['container'] = i['container']
                obj['stocks'] = i['stocks']
                obj['timediff'] = self.timeDiff(i['dateadded'])
                recent_stock.append(obj)

        print(recent_stock)
        return recent_stock

    def updateTerminalStocks(self):
        data = self.stocksUpdate()
        containers = self.getContainers()

        dataUpdate = []
        for i in containers:
            for k in data:
                obj = {}
                if i['terminalname'] == k['container']:
                    obj['terminalname'] = k['container']
                    obj['terminalid'] = i['terminalid']
                    obj['fid'] = i['fid']
                    obj['stocklevel'] = k['stocks']
                    dataUpdate.append(obj)
        #print(dataUpdate)
        #return dataUpdate

        for i in dataUpdate:
            response = self.updateFs(i['fid'],i['stocklevel'])
            print(response)








#TerminalStocks().getStocks()
TerminalStocks().updateTerminalStocks()