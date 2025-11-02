#! /usr/bin/python3

import os
import re
import smtplib
import ssl

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


def filnamn(kurs):
    base = re.sub(r"[/ :?.,]", '_', kurs[0])
    return f'{base}.xlsx'


def exists(kurs):
    fn = filnamn(kurs)
    return os.path.exists(f'listor/{fn}')


template = """\
<html>
<head></head>
<body>
<h3>Hej {name}</h3>
<p>
Välkommen som kursledare på Upplandskurserna 2025. Vi har glädjen att meddela
att vi blir drygt 160 scouter som sammanstrålar i Enköping 8-9 november.

</p>
<h3>Sensus</h3>
<p>
Precis som tidigare år samarbetar Upplandskurserna med Sensus, vilket innebär
att alla kurser utom de som tillhör Scouternas folkhögskola kommer att vara
Sensuscirklar där du som kursledare är cirkelledare.
</p>
<h3>Kursinformation</h3>
<p>
Bifogat till det här mailet är listor över deltagarna på dina kurser (namn,
e-postadress och telefonnummer). Om samma kurs går flera gånger ligger varje
kurspass i en egen flik i dokumentet. Om du har någon särskild information till
dina kursdeltagare ber vi dig att skicka den direkt till dem.
</p>
<p>
Det finns stor skärm i alla kurslokaler. För att använda den behöver du ta med
egen dator samt kabel för anslutning (HDMI eller USB-C). Om du behöver
blädderblock eller liknande till dina kurser och som du inte redan meddelat
oss, kontakta oss snarast så vi kan fixa det.
</p>
<h3>Kursmaterial</h3>
<p>
Vårt samarbete med Sensus gör att de köper in kursmaterial åt oss. Det mesta
ska redan vara fixat, men stäm av med Förnamn (contact@example.com) så
snart som möjligt att allt är klart.
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
Om du kommer med bil rekommenderar vi Idrottshusets parkering, den är
avgiftsfri under lördagar och söndagar. Från parkeringen är det en promenad på
c:a 200 meter till Westerlundska gymnasiet.
</p>
<h3>Ankomst</h3>
<p>
När du kommer till Westerlundska, gå till huvudentrén på Torggatan 6B. Leta
efter beachflaggor med Scouternas logotyp. Incheckning sker i entrehallen
innanför dörrarna.
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
Arrangörspatrullen
</p>
</body>
</html>
"""

with open("program-2025.pdf", "rb") as p:
    program = p.read()


con = sqlite3.connect('uk251101.sqlite')
cur = con.cursor()
cur.execute('SELECT DISTINCT id, namn,email,logi FROM deltagare inner join kursledare WHERE deltagare.id = kursledare.deltagare;')
rows = cur.fetchall()

for row in rows:
    memid, name, mail, logi = row

    print(name, mail)

    if logi == 'golvförläggning':
        logimsg = "<h3>Logi</h3><p>Du har anmält golvförläggning, tag med dig sovutrustning för det.</p>"
    elif logi == 'boende på hotellet kompassen':
        logimsg = "<h3>Logi</h3><p>Du kommer att bo på hotellet Kompassen. Rumsnummer och dörrkod kommer med SMS direkt från hotellet, sänglinne och handdukar finns på rummet.</p>"
    else:
        logimsg = ''

    html = template.format(name=firstname(name), logimsg=logimsg)
    text = html2text.html2text(html)

    msg = EmailMessage()
    msg['Subject'] = "Välkommen som kursledare på Upplandskurserna 2025"
    msg['From'] = Address("Upplandskurserna", "sender", "example.com")
    msg['To'] = mail

    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    msg.add_attachment(program, maintype="application", subtype="pdf", filename="program-2024.pdf")

    cur.execute(f'SELECT DISTINCT kurs FROM kursledare WHERE deltagare = "{memid}" ')

    kurser = [filnamn(x) for x in cur if exists(x)]

    if not kurser:
        print(f'INGEN KURS FÖR {name}')
        continue

    for kurs in kurser:
        with open(f'listor/{kurs}', "rb") as k:
            xslx = k.read()
        msg.add_attachment(xslx, maintype="application", subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=kurs)

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(identity, password)
        server.send_message(msg)

    time.sleep(15)
