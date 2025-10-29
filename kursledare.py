#! /usr/bin/python3

import email,smtplib, ssl

from email.message import EmailMessage
from email.headerregistry import Address


import html2text
import sqlite3
import time

port = 465  # For SSL
identity = "XXX"
password = "XXX"

receiver = "XXX"

def firstname(name):
    return name.split(' ')[0]

template = """\
<html>
<head></head>
<body>
<h3>Hej {name}</h3>
<p>
Här kommer en bekräftelse på att du är anmäld till Upplandskurserna 2025 och
{courses}. Det kan hända att det dyker upp specifik information från din
kursledare i din e-brevlåda.
</p>
<p>
Vi har glädjen att meddela att vi blir drygt 160 scouter som sammanstrålar i
Enköping 8-9 november.
</p>

<h3>Att ta hänsyn till</h3>
<p>
Då det förekommer luftburen allergi för starka dofter och kanel, ber vi dig att
vänligen lämna parfymer och bullar hemma.
</p>

<h3>Att ta med</h3>
<ul>
<li><b>Ta med dig egen kåsa och vattenflaska.</b></li>
<li><b>Inneskor eller varma sockor (det är skogräns).</b></li>
</ul>

{logimsg}

<h3>Parkering</h3>
<p>
Om du kommer med bil rekommenderar vi Idrottshusets parkering. Enligt uppgift
är den avgiftsfri under lördagar och söndagar. Därifrån är det en promenad på
c:a 200 meter till Westerlundska gymnasiet.
</p>
<h3>Bussar</h3>
<p>
Om du kommer med buss, tag bussen till Enköpings station, byt där till buss 22
mot Centrum (läge B2) och åk till Westerlundska gymnasiet. Om du kommer från
Uppsala är det buss 804. Vi rekommenderar bussen som går från Resecentrum i
Uppsala klockan 7.28, den är vid Enköpings station klockan 8.28. Om du kommer
från Bålsta är det buss 803. Vi rekommenderar bussen som går från Bålsta
station klockan 7.47, den är vid Enköpings station klockan 8.19.
</p>
<h3>Ankomst</h3>
<p>
När du kommer till Westerlundska, gå till huvudentrén på Torggatan 6B. Leta
efter beachflaggor med Scouternas logotyp. Incheckning sker i entrehallen
innanför dörrarna.
</p>
<p>
För dig som kommer på söndagen: Du får specifik information mycket snart.
</p>
<h3>Lägerbål</h3>
<p>
På lördag kväll blir det lägerbål utomhus. <b>Ta med något att sitta på (inga
sittbänkar finns)</b>.
</p>

<h3>Utvärdering</h3>
<p>
Efter kurshelgen vill vi gärna att du fyller i vår digitala utvärdering. Den
öppnar på söndagsmorgonen under kurshelgen. Du får ett e-brev med en länk till
formuläret i samband med att utvärderingen öppnar. Du kan även fylla i din
utvärdering via QR-kod som sätts upp runt om i lokalerna.
</p>
<h3>VARMT VÄLKOMMEN TILL UPPLANDSKURSERNA 2025</h3>
<p>
Arrangörspatrullen{skola}
</p>
</body>
</html>
"""

with open("program-2025.pdf", "rb") as p:
    program = p.read()


con = sqlite3.connect('uk241104.sqlite')
cur = con.cursor()

for row in cur.execute('SELECT * FROM kurslista'):
    pnr,name,mail,courses,logi = row

    print(name,mail)

    if logi == 'golvförläggning':
        logimsg = "<h3>Logi</h3><p>Du har anmält golvförläggning, tag med dig sovutrustning för det.</p>"
    elif logi == 'boende på hotellet kompassen':
        logimsg = "<h3>Logi</h3><p>Du kommer att bo på hotellet Kompassen. Rumsnummer och dörrkod kommer med SMS direkt från hotellet, sänglinne och handdukar finns på rummet.</p>"
    else:
        logimsg = ''

    if ',' in courses:
        kurs = "kurserna " + courses
    else:
        kurs = "kursen " + courses

    if courses == 'Leda scouting' or courses == 'Leda avdelning':
        skola = ''
    else:
        skola = ' i samarbete med Sensus'
        
    html = template.format(name=firstname(name), courses=kurs, logimsg=logimsg, skola=skola)
    text = html2text.html2text(html)
    
    msg = EmailMessage()
    msg['Subject'] = "Välkommen till Upplandskurserna 2025"
    msg['From'] = Address("Upplandskurserna", "sender", "example.com")
    msg['To'] = mail

    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    msg.add_attachment(program, maintype="application", subtype="pdf", filename="program-2024.pdf")

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(identity, password)
        server.send_message(msg)

    time.sleep(15)
