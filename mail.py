#! /usr/bin/python3

"""Sends the welcome mails for Upplandskurserna.

  mail.py [--dry-run] [--save DIR] [--only EMAIL] DATABASE PROGRAM LISTOR

DATABASE is the sqlite file made by tosqlite.rb, PROGRAM the program (pdf) to
attach and LISTOR the directory with the lists made by kurslistor.rb.

Sends one mail to each recipient. Which parts of the text a recipient gets
depends on the role: deltagare (signed up for a course they do not lead) and/or
kursledare. Someone who is both gets the parts for both. Kursledare also get
the participant lists (made by kurslistor.rb) for all the courses they lead.

With --dry-run the mails are only listed, nothing is sent. With --save DIR
nothing is sent either, instead each mail is written to DIR as an .eml and an
.html file for inspection. With --only EMAIL only the mail to that recipient is
made.
"""

import argparse
import re
import smtplib
import ssl
import sqlite3
import time

from email.message import EmailMessage
from pathlib import Path

import html2text

PORT = 465  # For SSL
IDENTITY = "account@example.com"
PASSWORD = "XXX"
# The visible sender, as "Name <account@domain>". The address must be IDENTITY
# or one of its aliases in Google Workspace.
SENDER = "Sender Name <sender@example.com>"

XLSX_TYPE = "vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def firstname(name):
    return name.split(' ')[0]


def filnamn(kurs):
    base = re.sub(r"[/ :?.,()]", '_', kurs)
    return f'{base}.xlsx'


def info(kurs):
    name, slot = kurs
    if slot == '1-5':
        return name
    elif slot == '1-3':
        return f'{name} på lördag'
    elif slot == '4-5':
        return f'{name} på söndag'
    else:
        return f'{name} i kurspass {slot}'


def passorder(kurs):
    """Sort key for (name, slot): by first and last kurspass, then name."""
    name, slot = kurs
    first, _, last = slot.partition('-')
    return int(first), int(last or first), name


def combine(seq):
    *top, last = seq
    return ", ".join(top) + ' och ' + last


def logimsg(logi):
    """The Logi paragraph."""
    if logi == 'golvförläggning':
        return "<h3>Logi</h3><p>Du har anmält golvförläggning, tag med dig sovutrustning för det.</p>"
    elif logi == 'boende på hotellet kompassen':
        return f"<h3>Logi</h3><p>Du kommer att bo på hotellet Kompassen. Rumsnummer och dörrkod kommer med SMS direkt från hotellet, sänglinne och handdukar finns på rummet.</p>"
    else:
        return ''


def make_message(subject, to, html, program):
    """program is the path of the pdf to attach"""
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SENDER
    msg['To'] = to

    msg.set_content(html2text.html2text(html))
    msg.add_alternative(html, subtype="html")
    msg.add_attachment(program.read_bytes(), maintype="application", subtype="pdf", filename=program.name)
    return msg


def save(msg, outdir):
    stem = re.sub(r"[^\w.@-]", '_', msg['To'])
    (outdir / f'{stem}.eml').write_bytes(bytes(msg))
    html = msg.get_body(('html',)).get_content()
    (outdir / f'{stem}.html').write_text(html, encoding='utf-8')


def send(msg, dry_run, outdir=None):
    if outdir:
        save(msg, outdir)
    if dry_run:
        attachments = [a.get_filename() for a in msg.iter_attachments()]
        print(f"  (dry run) {msg['Subject']} -> {msg['To']}, bilagor: {', '.join(attachments)}")
        return

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", PORT, context=context) as server:
        server.login(IDENTITY, PASSWORD)
        server.send_message(msg)

    time.sleep(15)


DELTAGARE = "deltagare"
KURSLEDARE = "kursledare"
ALLA = {DELTAGARE, KURSLEDARE}

# The text of the mail in order. Each part is included if the recipient has the
# role given first (or any of the roles, if a set). Fields: {name}, {courses}, {logimsg},
# {skola}.
SECTIONS = [
(ALLA, '''<html>
<head></head>
<body>
<h3>Hej {name}</h3>
'''),
(KURSLEDARE,'''<p>
Välkommen som kursledare på Upplandskurserna 2026.
</p>
<h3>Sensus</h3>
<p>
Precis som tidigare år samarbetar Upplandskurserna med Sensus, vilket innebär
att alla kurser utom de som tillhör Scouternas folkhögskola kommer att vara
Sensuscirklar där du som kursledare är cirkelledare. Du kommer att få ett
meddelande från Sensus innan kurshelgen som talar om att din cirkel är startad
och hur du närvarorapporterar den. Vår Sensuskontakt Förnamn Efternamn kommer att
närvara på Upplandskurserna så du kan ställa frågor till honom där. Han kan
även nås via e-post på sensus-contact@example.com.
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
blädderblock eller liknande till dina kurser och du inte redan meddelat
oss, kontakta oss snarast så att vi kan fixa det.
</p>
<h3>Kursmaterial</h3>
<p>
Vårt samarbete med Sensus gör att de köper in kursmaterial till de flesta av
våra kursen. Det mesta ska redan vara fixat, men stäm av med Förnamn
(sensus-contact@example.com) om det återstår några oklarheter.
</p>
'''),
    (DELTAGARE, '''<p>
Välkommen som deltagare på Upplandskurserna 2026. Detta är en bekräftelse på
att du är anmäld till {courses}. Det kan hända att det dyker upp specifik
information från din kursledare i din e-brevlåda.
</p>
'''),

(ALLA, '''<p>
Vi har glädjen att meddela att vi blir ungefär 150 scouter som sammanstrålar i
Enköping 8-9 november.
</p>

<h3>Att ta hänsyn till</h3>
<p>
Då det förekommer luftburen allergi för starka dofter och kanel, ber vi dig att
vänligen lämna parfymer och bullar hemma.
</p>
<p>
Endast personer som har föranmält ankomst på fredagen kan komma då.
</p>

<h3>Att ta med</h3>
<ul>
<li><b>Ta med dig egen kåsa och vattenflaska.</b></li>
<li><b>Inneskor eller varma sockor (det är skogräns).</b></li>
<li><b>Pysselprojekt till kvällen (om du vill).</b></li>
</ul>

{logimsg}

<h3>Parkering</h3>
<p>
Om du kommer med bil rekommenderar vi Idrottshusets parkering, den är
avgiftsfri under lördagar och söndagar. Från parkeringen är det en promenad på
c:a 200 meter till Westerlundska gymnasiet.
</p>
<h3>Bussar</h3>
<p>
Om du kommer med buss, tag bussen till Enköpings station, byt där till buss 22
mot Centrum (läge B2) och åk till Westerlundska gymnasiet. Om du kommer från
Uppsala är det buss 804. Vi rekommenderar bussen som går från Resecentrum i
Uppsala klockan 7.29, den är vid Enköpings station klockan 8.20. Om du kommer
från Bålsta är det buss 803. Vi rekommenderar bussen som går från Bålsta
station klockan 7.47, den är vid Enköpings station klockan 8.18.
</p>
<h3>Ankomst</h3>
<p>
När du kommer till Westerlundska, gå till huvudentrén på Torggatan 6B. Leta
efter beachflaggor med Scouternas logotyp. Incheckning sker i entrehallen
innanför dörrarna.
</p>

<h3>Utvärdering</h3>
<p>
Efter kurshelgen vill vi gärna att du fyller i vår digitala utvärdering. Den
öppnar på söndagsmorgonen under kurshelgen. Du får ett e-brev med en länk till
formuläret i samband med att utvärderingen öppnar. Du kan även fylla i din
utvärdering via QR-kod som sätts upp runt om i lokalerna.
</p>
<h3>VARMT VÄLKOMMEN TILL UPPLANDSKURSERNA 2026</h3>
<p>
Arrangörspatrullen{skola}
</p>
</body>
''')
    ]

def compose(roles, **fields):
    """The html of the mail for someone with the given roles."""
    return "".join(text for audience, text in SECTIONS
                   if audience is ALLA
                   or roles & ({audience} if isinstance(audience, str) else audience)).format(**fields)


def send_all(cur, program, listdir, dry_run, outdir=None, only=None):
    cur.execute('SELECT id, namn, email, logi FROM deltagare')
    rows = cur.fetchall()
    if only:
        rows = [row for row in rows if row[2].strip().lower() == only.strip().lower()]
        if not rows:
            raise SystemExit(f"no recipient with the address {only}")

    for memid, name, mail, logi in rows:
        print(name, mail)

        cur.execute('SELECT DISTINCT kurs FROM kursledare WHERE deltagare = ?', (memid,))
        leder = [kurs for (kurs,) in cur.fetchall()]

        # the lists of the courses the recipient leads; a course without a list
        # has no participants and does not make them a kursledare
        filer = []
        for kurs_ledd in leder:
            fil = listdir / filnamn(kurs_ledd)
            if fil.exists():
                filer.append(fil)
            else:
                print(f"INGEN LISTA FÖR {kurs_ledd} ({name})")

        # a kursledare is signed up for the course they lead, that does not
        # make them a participant
        cur.execute('SELECT kurs, kurspass FROM kurser WHERE deltagare = ?', (memid,))
        courses = [info(kurs) for kurs in sorted(cur.fetchall(), key=passorder)
                   if kurs[0] not in leder]

        roles = set()
        if courses:
            roles.add(DELTAGARE)
        if filer:
            roles.add(KURSLEDARE)

        # someone without a role still gets the parts for everyone
        if not roles:
            print(f"INGEN KURS FÖR {name}, skickar bara det som gäller alla")

        if len(courses) == 1:
            kurs = 'kursen ' + courses[0]
        else:
            kurs = 'kurserna ' + combine(courses) if courses else ''

        if not courses or courses[0] == 'Leda scouting':
            skola = ''
        else:
            skola = ' i samarbete med Sensus'

        html = compose(roles, name=firstname(name), courses=kurs,
                       logimsg=logimsg(logi), skola=skola)

        if roles == {KURSLEDARE}:
            subject = "Välkommen som kursledare på Upplandskurserna 2026"
        else:
            subject = "Välkommen till Upplandskurserna 2026"

        msg = make_message(subject, mail, html, program)

        for fil in filer:
            msg.add_attachment(fil.read_bytes(), maintype="application",
                               subtype=XLSX_TYPE, filename=fil.name)

        send(msg, dry_run, outdir)


def main():
    parser = argparse.ArgumentParser(description="Send the welcome mails for Upplandskurserna")
    parser.add_argument("database", help="sqlite file made by tosqlite.rb")
    parser.add_argument("program", type=Path, help="the program (pdf) to attach")
    parser.add_argument("listor", type=Path, help="directory with the lists made by kurslistor.rb")
    parser.add_argument("--dry-run", action="store_true", help="list the mails without sending them")
    parser.add_argument("--save", type=Path, metavar="DIR",
                        help="write the mails to DIR (as .eml and .html) instead of sending them")
    parser.add_argument("--only", metavar="EMAIL",
                        help="only make the mail to the recipient with this address")
    args = parser.parse_args()

    if not args.program.is_file():
        parser.error(f"{args.program} is not a file")
    if not args.listor.is_dir():
        parser.error(f"{args.listor} is not a directory")
    if not Path(args.database).is_file():
        parser.error(f"{args.database} is not a file")

    con = sqlite3.connect(args.database)
    cur = con.cursor()

    if args.save:
        args.save.mkdir(parents=True, exist_ok=True)

    send_all(cur, args.program, args.listor, args.dry_run or bool(args.save), args.save, args.only)


if __name__ == "__main__":
    main()
