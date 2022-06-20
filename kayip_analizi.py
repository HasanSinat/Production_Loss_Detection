
from calendar import month
from turtle import clear
import requests, datetime
import sys
from datetime import  date
import secrets

"""

Estimated production loss calculator. It founds loses due to outage and calculate an estimated production value using other days values.  

"""
solarEdgePlants = secrets.solarEdgePlants
api_key = secrets.api_key
date_format = "%Y-%m-%d %H:%M:%S"
loseDates=list() # list to add loss dates.
selecter = 1 # selecter to select plant id from selected plant name 
counter = 0  #counter to use in for loop to place values in the right index

for plant in solarEdgePlants:
    print(selecter, "-", plant['name'] )
    selecter += 1

selection = int(input("Seçinniz: "))
print("Seçilen Santral:", solarEdgePlants[selection-1]['name'])
siteID = solarEdgePlants[selection-1]['id']
startTime_ = input("Başlangıç Tarihi Giriniz (YYYY-MM-DD) : ")
endTime_ = input("Bitiş Tarihi Giriniz (YYYY-MM-DD) : ")

earliestTime=datetime.time(8,0,0) #cap for production hours. 
latestTime = datetime.time(19,0,0)

def solarEdge():

    url = f"https://monitoringapi.solaredge.com/site/{siteID}/energyDetails?meters=PRODUCTION&timeUnit=HOUR&startTime={startTime_} 08:00:00&endTime={endTime_} 22:00:00&api_key={api_key}"
    try:
        response_ = requests.get(url).json() 
    except:
        sys.exit("Data Alınamadı, Lütfen Sonra Tekrar Deneyiniz.")

    x = datetime.datetime.strptime(startTime_, "%Y-%m-%d") 
    y =datetime.datetime.strptime(endTime_,"%Y-%m-%d" )
    
     #en son aşamada oluşturulan listeye value değerlerini sonradan ekleyebilmek için oluşutduğum counter.

    for hour in response_["energyDetails"]["meters"][0]["values"]:
        hour["date"] = datetime.datetime.strptime(hour["date"], date_format)#her date değerini üzerinde çalışılabilir datetime objesine dönüştürüyorum.

    for hour in response_["energyDetails"]["meters"][0]["values"]: #for döngüsüyle her saatin içine giriyorum.

        if hour["date"].time() >= earliestTime and hour["date"].time() <= latestTime:
            if "value" not in hour:  #if value key doesnt appear that means there is an outage loss 
                loseDates.append(dict(date = hour["date"],  value= "Kayıp Hesaplanamadı" ))
                previous_day = hour["date"] - datetime.timedelta(days=1)
                if previous_day < x :
                    previous_day = hour["date"] + datetime.timedelta(days=3)
                next_day = hour["date"] + datetime.timedelta(days=1)
                if next_day > y :
                    next_day = hour["date"] - datetime.timedelta(days=3)

                previous_day_value = 0
                next_day_value = 0
                try:
                    for hours in response_["energyDetails"]["meters"][0]["values"]:
                        if "value" in hours and hours['value'] != 0:                  
                            if hours["date"] == previous_day:                   
                                previous_day_value = hours["value"]            
                            elif hours["date"] == next_day:                    
                                next_day_value = hours["value"]
                except:
                    break            
                if previous_day_value !=0 and next_day_value !=0 :            
                    difference =  abs(next_day_value - previous_day_value) / next_day_value * 100
                        
                    while difference >= 35 :  #cap for production difference between days in order to avoid abnormal values
                        if next_day_value > previous_day_value:
                            previous_day = previous_day - datetime.timedelta(days = 1) 
                            if x > previous_day:
                                previous_day = previous_day + datetime.timedelta(days = 10) 
                            for hours in response_["energyDetails"]["meters"][0]["values"]:
                                if "value" in hours:
                                    if hours["date"] == previous_day:
                                        previous_day_value = hours["value"]
                                            
                        elif next_day_value < previous_day_value :
                            next_day = next_day + datetime.timedelta(days = 1)                
                            if  y < next_day:
                                next_day = next_day - datetime.timedelta(days = 10)
                            for hours in response_["energyDetails"]["meters"][0]["values"]:
                                if "value" in hours: 
                                    if hours["date"] == next_day:
                                        next_day_value = hours["value"]
                        difference =  abs(next_day_value - previous_day_value) / next_day_value * 100
                    loseDates[counter]['value'] = (previous_day_value + next_day_value) / 2
                    counter +=1 
                
    print("----------------------------------------------------------------")
    
    if not loseDates:
            sys.exit("Verilen Tarihler Arasında Güç Kaybı Yaşanmamıştır. ")
    for dates in loseDates:
        looseDate = datetime.datetime.strftime(dates['date'], date_format)
        looseValue= dates['value']
        print("| Kayıp Tarihi: ", looseDate, " Tahmini Kayıp: ", looseValue, "|")

    
    print("----------------------------------------------------------------")

solarEdge()


