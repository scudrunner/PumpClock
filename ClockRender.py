# -*- coding: utf-8 -*-

"""

Spyder Editor
This is a Python3 set of code 
 - Why - because the Web Help I found was 3
 
To write in the Var/www/html folder I need to change permissions on the pi
sudo chown pi /var/www/html
isues with putting this as a cron job, had to install 
sudo apt-get install postfix
grep CRON /var/log/syslog - showed issues
sudo tail -f /var/mail/pi showed mail and showed that the template was not found

"""

 

import urllib.request, json , datetime
import pytz
from datetime import timedelta
from jinja2 import Environment, FileSystemLoader

 

 

#--------------JSON Data Analysis

url1 = "https://tnf.ns.10be.de:6836/api/v1/entries.json"

     

url2 = "https://tnf.ns.10be.de:6836/api/v1/treatments.json"

 

 

with urllib.request.urlopen(url1) as url:

    data = json.loads(url.read().decode())

#    print("current BG")

#    print(data[0].get("sgv"))

#    print(data[0].get("dateString"))

#    print(data[0].get("direction"))

    lastsgvtime = datetime.datetime.strptime( data[0].get("dateString") ,'%Y-%m-%dT%H:%M:%S.%fZ')

 

trend = data[0].get("direction")

 

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

   

#    print(pumpdate)

   

    

now = datetime.datetime.utcnow()
nowlocal = now - timedelta(hours=4, minutes=0)


time = nowlocal.strftime("%H:%M")
#print("time:", time)

diffsgv = now - lastsgvtime

#print(diffsgv.seconds / 60)

 

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

#print(hours)

#print(pumplifepercentage, "percentage of pump used")

#----------------------------end of JSON data analysis

 

#begin the website creation

file_loader = FileSystemLoader('/home/pi/nightscout/templates')

 

env = Environment(loader=file_loader)

 

template = env.get_template('SVGtemplate.html')

 

output = template.render(

                recent_BG = data[0].get("sgv") ,

                recent_trend = arrow,

                BG_textStyleStart = BG_textStyleStart   ,

                BG_textStyleEnd = BG_textStyleEnd   ,

                Circle_colored = pumplifepercentage  ,

                Circle_empty = pumpleft    ,

                hours = hoursleft   ,
                
                time = time ,

                )

 

with open("/var/www/html/index.html", "w") as file:

    file.seek(0)

    file.write(output)

    file.truncate()

    