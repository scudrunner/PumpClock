# -*- coding: utf-8 -*-

"""
Version 3

Version 3 change - adding in CGM monitoring
Spyder Editor
This is a Python3 set of code 
 - Why - because the Web Help I found was 3
rebuilding V2 to haandle errors of website being down
     step one will be to give unknown - done 
     step 2 will be to define the variables to persist (maybe for pod)
     step 3 work on javascrips for clock maybe...
     need to functionize this to make it more readable
To write in the Var/www/html folder I need to change permissions on the pi
sudo chown pi /var/www/html
isues with putting this as a cron job, had to install 
sudo apt-get install postfix
grep CRON /var/log/syslog - showed issues
sudo tail -f /var/mail/pi showed mail and showed that the template was not found
chmod +x Clockrender.py   to allow it to be executable...
"""

 

import urllib.request, json , datetime
import pytz
from datetime import timedelta
from jinja2 import Environment, FileSystemLoader

 

 

#--------------JSON Data Analysis

url1 = "https://tnf.ns.10be.de:6836/api/v1/entries.json"
url2 = "https://tnf.ns.10be.de:6836/api/v1/treatments.json"

UTCoffset = 5 
# The UTC is 5 for winter and 4 for Summer in Boston
 
req = urllib.request.Request(url1)
try: urllib.request.urlopen(req)
except urllib.error.URLError as e:
    print(e.reason)
    BG = 9999
    arrow = "&#8212;"
    BG_textStyleStart = "<b><strike>"
    BG_textStyleEnd = "</b></strike>"
    pumplifepercentage = 100
    pumpleft = 0
    hoursleft = "??"
    now = datetime.datetime.utcnow()
    nowlocal = now - timedelta(hours=UTCoffset, minutes=0)
    time = nowlocal.strftime("%H:%M")

else:    
    with urllib.request.urlopen(url1) as url:
        data = json.loads(url.read().decode()) 
    #    print("current BG") 
    #    print(data[0].get("sgv")) 
    #    print(data[0].get("dateString")) 
    #    print(data[0].get("direction")) 
    lastsgvtime = datetime.datetime.strptime( data[0].get("dateString") ,'%Y-%m-%dT%H:%M:%S.%fZ') 
    trend = data[0].get("direction") 
    BG = data[0].get("sgv") 
    if trend == "SingleUp" : 
                    arrow = "&#8593;" 
    elif trend == "Flat" : 
                    arrow ="&#8594;" 
    elif trend =="FortyFiveUp" : 
                    arrow ="&#8599;" 
    elif trend =="FortyFiveDown" : 
                    arrow ="&#8600;" 
    elif trend =="SingleDown" : 
                    arrow ="&#8595;" 
    elif trend =="DoubleUp" : 
                    arrow ="&#8657;" 
    elif trend =="DoubleDown" : 
                    arrow ="&#8659;" 
    else : 
                    arrow = "&#8212;"
      
    with urllib.request.urlopen(url2) as url:
        data2 = json.loads(url.read().decode()) 
  
    pump_index = next((index for (index, d) in enumerate(data2) if d["eventType"] == "Resume Pump"), None) 
    #    print(pump_index) 
    pumpdate = datetime.datetime.strptime( data2[pump_index].get("timestamp"),'%Y-%m-%dT%H:%M:%SZ')
    #print(pumpdate)

    	
	#looking for CGM Start Date
    CGM_index = next((index for (index, d) in enumerate(data2) if d["eventType"] == "Sensor Start"), None) 
    #print(CGM_index)
    
    if CGM_index  :  #this is if the CGM sensor start is in the JSON
            #print(data2[CGM_index].get("created_at"))
            with open("/home/pi/nightscout/CGMDate.txt", "w") as file:
                  file.seek(0)
                  file.write(data2[CGM_index].get("created_at"))
                  file.truncate()
            
            CGMdate = datetime.datetime.strptime( data2[CGM_index].get("created_at"),'%Y-%m-%dT%H:%M:%S.%fZ')
    else :   # here I need to read the last CGM start from a file
            with open("/home/pi/nightscout/CGMDate.txt", "r") as file:
                  CGMDate_text = file.read()
            #print(CGMDate_text)
            CGMdate = datetime.datetime.strptime(CGMDate_text,'%Y-%m-%dT%H:%M:%S.%fZ')
            #print(CGMdate)
    
	
    now = datetime.datetime.utcnow()
    nowlocal = now - timedelta(hours=UTCoffset, minutes=0)
    time = nowlocal.strftime("%H:%M")
    #print("time:", time)
    
    diffsgv = now - lastsgvtime
    if diffsgv.seconds < 600 :
                    BG_textStyleStart = "<b>"
                    BG_textStyleEnd = "</b>"
    else :
                    BG_textStyleStart = "<b><strike>"
                    BG_textStyleEnd = "</b></strike>"
    #print
    #print( "Current date and time using str method of datetime object:")
    #print( str(now))
    
    
    diffdate = now - pumpdate
    days, seconds = diffdate.days, diffdate.seconds
    hours = round((days * 24 + seconds / 3600),0)
    pumplifepercentage = round((hours/72)*100,0)
    
    pumpleft = 100 - pumplifepercentage
    
    hoursleft = 72 - hours


    diffCGM = now - CGMdate
    days, seconds = diffCGM.days, diffCGM.seconds
    hours = round((days * 24 + seconds / 3600),0)
    CGMlifepercentage = round((hours/(240))*100,0)
    CGMbar = int ( round( (CGMlifepercentage/100) *  40, 0) )
    if CGMbar > 40:
       CGMbar = 40	
	
    if CGMbar > 34 :
      CGMbarcolor = "yellow"
    else :
      CGMbarcolor = "grey"
    #print( CGMbar)


#print(hours)
#print(pumplifepercentage, "percentage of pump used")
#----------------------------end of JSON data analysis

 
#begin the website creation
file_loader = FileSystemLoader('/home/pi/nightscout/templates')
env = Environment(loader=file_loader)
template = env.get_template('SVGtemplate.html')
output = template.render(
                recent_BG = BG ,
                recent_trend = arrow,
                BG_textStyleStart = BG_textStyleStart   ,
                BG_textStyleEnd = BG_textStyleEnd   ,
                Circle_colored = pumplifepercentage  ,
                Circle_empty = pumpleft    ,
                hours = hoursleft   ,   
                time = time ,
                CGMbar = CGMbar  , 
                CGMbarcolor = CGMbarcolor
                )

with open("/var/www/html/index.html", "w") as file:
    file.seek(0)
    file.write(output)
    file.truncate()

    