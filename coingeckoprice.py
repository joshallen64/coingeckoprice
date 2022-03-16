import json
import pandas as pd
import time
from pycoingecko import CoinGeckoAPI
import requests

cg = CoinGeckoAPI()

class CoinPrice:
    
    def __init__(self):
        self.tsym = "cad"
        self.IDList = cg.get_coins_list()
        time.sleep(1.0)
        self.priceList = {}
        self.timeResolution = 'D' #use D?? for Day H for hourly, min for minutely
        self.session =requests.Session()
        self.useSearch = True

    def getCoinID (self, sym: str) -> str:
        #Gets the coingecko coinID
        sym = sym.lower()
        coinIDs = []
        for coin in self.IDList :
            if coin["symbol"] == sym:
                #return coin["id"]
                if "binance-peg" not in coin["id"]:
                    coinIDs.append(coin)

        #no symbol found    
        #return ("none")

        if (len(coinIDs) > 1):
            i = 0                   
            for coin in coinIDs:
                print(i,": ", coin)
                i += 1
            selection = int(input("select a coinID to use (-1 for none): "))
            if (selection < 0 ):
                return "$none$"
        elif(len(coinIDs) ==1):
            selection = 0

        elif(self.useSearch==True):
            
            cantFind = True
            while (cantFind) :
                print ("Can't find this symbol " + sym)
                ans = input("(m)anual or (n)one: ")
                if (ans == "n"):
                    cantFind = False
                    return "$none$"
                elif (ans =="m"):
                    s = " please enter manual replacement: "
                    sym2 = input(s)
                    coinID = self.getCoinID(sym2)
                    cantFind = False
                    return(coinID)
                               
        try:

            return coinIDs[selection]['id']

        except:
                               
            raise ValueError("Could not find the symbol : " + sym)

    def convertDateToTS(self, dateString: str):

        date =  pd.to_datetime(dateString)
        dateTS = date.timestamp()
        return dateTS

    def convertDateToTSStr(self, dateString: str):
        date = str(self.convertDateToTS(dateString))
        dateTS = date[:10]
        return dateTS

    def getCoinMarketYear(self, sym: str, dateString: str):
        
        coinID = self.getCoinID(sym)
        if (coinID == "$none$"):
            return ({0:0.0})
        date = pd.to_datetime(dateString)
        dateStartString = "Jan 1, " + str(date.year)
        dateEndString = "Dec 31, " + str(date.year)
        print (dateStartString)

        #convert to pandas Date

        dateStartTS = self.convertDateToTSStr(dateStartString)
        dateEndTS = self.convertDateToTSStr(dateEndString)

        print("start date: " + str(dateStartTS))
        print("end date: " + str(dateEndTS))
        print(coinID)
        marketYear = cg.get_coin_market_chart_range_by_id(coinID,self.tsym,dateStartTS, dateEndTS)
        time.sleep(1.0)
        
        #print(marketYear)
        return marketYear["prices"]

    def getCoinData(self, sym: str, dateString: str):

        #make symbol lower case

        sym = sym.lower()

        if type(dateString) == str:
            mydate = pd.to_datetime(dateString)
        else:
            mydate = dateString
            dateString = mydate.strftime('%b. %d, %Y')


        

        mydate = mydate.floor(self.timeResolution)
        print(mydate.strftime('%b. %d, %Y'))

        dateTS = int(mydate.timestamp() * 1000)

        #check to see if the coin is in the dict
        if (sym in self.priceList):
            if (dateTS in self.priceList[sym]):
          
                return self.priceList[sym]
            
            else:
                print ("date not found for: "+ sym + "TS: " + str(dateTS))
                priceList = self.getCoinMarketYear(sym, dateString)
               
                priceDict = self.convertList(priceList)
                self.priceList[sym] = priceDict

                
                            
                #print(self.priceList[sym])
                return self.priceList[sym]


        else:
            priceList = self.getCoinMarketYear(sym, dateString)
            priceDict = self.convertList(priceList)
            self.priceList[sym] = priceDict
            
            return self.priceList[sym]

    def convertList(self, myList):
        res_dct = dict(myList)
        return res_dct
            
    def getPrice(self, dateString: str, sym: str):

        priceData={}

        try:
            sym = sym.lower()
        
        except:
            print("an exception occured")
            print(sym)
            raise Exception("couldn't perform lower() operation on symbol")
        
        #handle the correct types
        if type(dateString) == str:
            mydate = pd.to_datetime(dateString)
        else:
            mydate = dateString
            dateString = mydate.strftime('%b. %d, %Y')


        

        mydate = mydate.floor(self.timeResolution)
        print(mydate.strftime('%b. %d, %Y'))

        dateTS = int(mydate.timestamp() * 1000)

        
        if sym == 'cad':
            priceData[dateTS]=1.0
        elif sym in ['usd','jpy','gbp']:
            
            priceData[dateTS] = self.getForexData(sym,mydate)
        else:
            
            priceData = self.getCoinData(sym, dateString)

        #the result is returned in milliseconds need to multiply by 1000 in order to match result

        if priceData:
            if dateTS in priceData:
                print (sym + " on " + dateString + ": " + str(priceData[dateTS]))
                return priceData[dateTS]
            else:
                print("still not found 1")
                #print(priceData)
                if priceData:

                    
                    for date in priceData:
                        if date > dateTS:
                            try:
                                return priceData[dateTS]
                            except:
                                return 0.0
                        else:
                            prevDate = dateTS
                            
                    return 0.0
                        
                else:
                    return 0.0

        else:

            print ("date not found: "+ str(dateString)+ " " + str(dateTS)+"  " + sym)
            print ("retrying...")
            priceData = self.getCoinData(sym, dateString)
           
            #print (priceData)
            #third try sometimes coingecko doesn't respect the time resolution
            if not(dateTS in priceData):
                print("still not found 2")
                

                if priceData:
                    for date in priceData:
                        if date > dateTS:
                            return priceData[dateTS]
                        else:
                            prevDate = dateTS
                        
                else:
                    return 0.0
            return priceData[dateTS]
        
        

        
    def getForexData(self, sym: str, date):

        #NOTE USD support only at the moment

        if sym == 'usd':
            usNoonLegacyString = 'https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json'
            #note zfill will pad the month with a zero
            rTime = str(date.year) + '-' +str(date.month).zfill(2)+'-'+str(date.day).zfill(2)
            payload = {'start_date':rTime,
                       'end_date':rTime
                       }
            
            response = self.session.get(usNoonLegacyString, params=payload)
            #print(response.url)
            
            if response.status_code == requests.codes.ok:
                priceJSON = response.json()
                #print(priceJSON)
                #try to assign the value if no observations it'll throw and exception and it should try the
                #next business day
                try:
                    #print(date)
                    value = float(priceJSON['observations'][0]['FXUSDCAD']['v'])
                    #print(value)
                    return(value)
                except:
                    #print("no date using next day")
                    date2 = date + pd.to_timedelta(1,unit="D")
                    #print(date2)
                    newValue = self.getForexData(sym, date2)
                    return(newValue)
                
            
                #print(value)
                
            else:
                return 0.0

        else:
            return 0.0;
        

        
        
        
                 
