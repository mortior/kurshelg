# Upplandskurserna

Scripts for the administration around the Upplandskurserna weekend (Scouterna
Uppland): turn the exports from the registration system into a database,
generate participant lists per course, and send out welcome mails.

The mail text and the output are in Swedish.

## Overview

```
data/*.xlsx ──tosqlite.rb──> uk<date>.sqlite ──kurslistor.rb──> listor/*.xlsx   (for course leaders)
                                   │                        └─> sensus/*.xlsx   (for Sensus)
                                   └──────────mail.py (+ program PDF, listor/)──> welcome mails
```

| File             | Language | Purpose                                                              |
|------------------|----------|----------------------------------------------------------------------|
| `tosqlite.rb`    | Ruby     | Reads the two Excel exports and builds the sqlite database           |
| `kurslistor.rb`  | Ruby     | Writes one Excel workbook per course from the database               |
| `mail.py`        | Python   | Composes and sends (or saves) one welcome mail per registered person |
| `Gemfile`        | –        | Ruby dependencies (`rubyXL`, `sqlite3`)                              |
| `requirements.txt` | –      | Python dependencies (`html2text`)                                    |

Directories (all git-ignored, since they contain personal data or are generated):

- `data/` – the input exports
- `listor/` – generated lists for the course leaders (no personnummer)
- `sensus/` – generated lists for Sensus (with personnummer, only courses that have a course leader)
- `utkast/` – drafts/saved mails
- `*.sqlite` – the generated database

## Setup

Ruby:

```sh
bundle install
```

Python (a virtualenv in `.venv/` is used):

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Mail account

`mail.py` sends through `smtp.gmail.com` (SSL, port 465) and assumes the
outgoing account is a **Google Workspace** account. Before sending for real you
must set these constants near the top of `mail.py`:

```python
IDENTITY = "account@example.com"      # the address of the account that sends
PASSWORD = "xxxxxxxxxxxxxxxx"         # an app password for that account
SENDER = "Sender Name <sender@example.com>"  # visible sender
```

`IDENTITY` and `PASSWORD` are the login; `SENDER` is what the recipients see in
the `From` header, in the format `Name <account@domain>`.

`--dry-run` and `--save` never log in, so they work without valid values.

To set them up for your own account:

1. Set `IDENTITY` to the full address of the Workspace account you send from.
2. Turn on 2-Step Verification for the account (Google Account → Security).
   App passwords are not available without it. Some Workspace admins disable
   this option; if it is missing, ask your admin to allow 2-Step Verification
   and app passwords for the account.
3. Create an app password at <https://myaccount.google.com/apppasswords> (name
   it e.g. "upplandskurserna"). Google shows a 16-character password, possibly
   grouped with spaces.
4. Set `PASSWORD` to that password **without the spaces**. Your normal account
   password will not work.
5. Test with a single mail to yourself:
   `.venv/bin/python mail.py --only your@address uk261025.sqlite program-2026.pdf listor`
   (note: `--only` without `--dry-run`/`--save` really sends, and your address
   must be in the database).

Notes:

- The address in `SENDER` can be the same as `IDENTITY`, or an alias of it. Google
  rewrites or rejects a `From` address that is not the account itself or one of
  its configured aliases. To use an alias, add it to the sending account first
  (Gmail → Settings → Accounts → "Send mail as", or have the Workspace admin add
  it as an alias for the user), then use it in `SENDER`.
- Workspace accounts have daily sending limits (around 2000 mails/day), which is
  far above what this needs; the 15 second pause between mails is there to stay
  well clear of rate limiting.
- Do not commit a real password. Revoke the app password on the same Google
  page when you no longer need it.

## Usage

### 1. Export the input data

The input data is produced by Scoutnet. Place two Excel files in `data/`:

1. **Participants report** (here called `data/participants.xlsx`):
   the Scoutnet report "Alla arrangemangsdeltagare", exported in Excel format.
   One row per person with columns such as `Medlemsnummer`, `Namn`, `E-post`,
   `Anmäld`, `Närvaro` and one `Anmäld till <kurs>` column per course.

2. **Registration form** (here called `data/registration.xlsx`):
   the Scoutnet report "Anmälan till kurshelgen", exported in Excel format.
   The answers to the registration form (kår, logi, allergies, which courses
   the person leads, and the course choices per kurspass).

**Important:** the scripts assume that the data is in the format produced by the
Scoutnet activity "Upplandskurserna 2026" – the column names and the form
questions are used literally (see `tosqlite.rb`). If the activity is set up
differently, for example with other questions or course groupings, the scripts
must be changed to match.

Only the first sheet of each file is read, and the first row must be the header.

### 2. Build the database

```sh
./tosqlite.rb data/participants.xlsx data/registration.xlsx uk261025.sqlite
```

The arguments are: participants report, registration form, output file. The
script uses `CREATE TABLE IF NOT EXISTS` and plain `INSERT`, so **delete the old
sqlite file first** (or use a new name) when re-running, otherwise you get
primary key errors.

### 3. Generate the course lists

```sh
./kurslistor.rb uk261025.sqlite
```

This writes `listor/` and `sensus/` in the current directory, one `.xlsx` per
course with one sheet per kurspass (leaders on top, participants below).
Courses where everyone in a kurspass is a leader are skipped for `listor/`.

### 4. Check, then send the mails

```sh
# List what would be sent, send nothing
.venv/bin/python mail.py --dry-run uk261025.sqlite program-2026.pdf listor

# Write every mail to a directory as .eml and .html for inspection
.venv/bin/python mail.py --save utkast uk261025.sqlite program-2026.pdf listor

# Only the mail to one recipient (works with the other options too)
.venv/bin/python mail.py --save utkast --only someone@example.com uk261025.sqlite program-2026.pdf listor

# Actually send
.venv/bin/python mail.py uk261025.sqlite program-2026.pdf listor
```

Arguments: the database, the program PDF to attach, and the directory with the
lists from step 3. `--dry-run` and `--save` both mean nothing is sent. Sending
waits 15 seconds between mails to avoid being rate limited.

Watch the output for the warnings `INGEN LISTA FÖR …` (a course the person leads
has no list) and `INGEN KURS FÖR …` (person with no course; they only get the
parts of the mail meant for everyone).

## How it is set up

### Database (`tosqlite.rb`)

| Table        | Contents                                                                           |
|--------------|------------------------------------------------------------------------------------|
| `rapport`    | The participants report as is, one row per person (key: `id` = Medlemsnummer)       |
| `kurser`     | `(deltagare, kurs, kurspass)` – the courses each person is signed up for           |
| `kursledare` | `(deltagare, kurs)` – the courses each person leads                                |
| `form`       | Per person from the registration form: kår, days attending, function, allergies, logi, room mates |
| `deltagare`  | `rapport` joined with `form` for those with `Anmäld = Ja` – the people the other scripts use |
| `kurslista`  | Convenience view (as a table) of name, e-mail, courses and logi per person         |

How the course slots (`kurspass`) are derived: they are not hard coded but read
from the registration form columns.

- `Kortare kurser lördag/söndag, kurspass N` → the course is held in slot N
- `Kurser - Leda scouting` → slots 1–5
- `Kurser - Heldagskurser söndag` → slots 4–5

Slots are stored compressed: `1`, `4-5` or `1,4`. Course names in the report
are matched to the form names case-insensitively and may have a
` (kurspass N)` suffix, which then restricts the person to that slot. A course
in the report that is missing from the form aborts with an error.

Course leaders come from the form column
`Grund - Vilken eller vilka kurser ska du leda?`.

### Lists (`kurslistor.rb`)

Reads `deltagare`, `kurser` and `kursledare`, groups per course and kurspass,
and writes workbooks with RubyXL. File names are the course name with
`/ : ? . , ( )` and spaces replaced by `_`; `mail.py` uses the same rule
(`filnamn`) to find the list for a course, so the two must be kept in sync.

### Mails (`mail.py`)

For each person in `deltagare`:

- **Roles**: *kursledare* if they lead a course that has a list in `listor/`,
  *deltagare* if they are signed up for any course they do not lead. A person
  can have both, or neither.
- **Text**: `SECTIONS` is an ordered list of `(audience, html)` parts. A part is
  included if the person has the role (or one of the roles) given for it;
  `ALLA` parts are always included. Fields available in the text: `{name}`,
  `{courses}`, `{logimsg}`, `{skola}`. Edit `SECTIONS` to change the mail.
- **Logi paragraph**: depends on the logi choice (floor sleeping or hotel
  Kompassen).
- **Attachments**: the program PDF for everyone, plus the course lists from
  `listor/` for each course the person leads.
- The mail is sent as multipart with both an HTML and a plain text
  (`html2text`) version, through Gmail's SMTP server over SSL (port 465).

### The mail text and how to change it

The text of the mail is the list `SECTIONS` in `mail.py`. Each entry is a tuple
`(audience, html)`:

```python
SECTIONS = [
(ALLA, '''<html>
<head></head>
<body>
<h3>Hej {name}</h3>
'''),
(KURSLEDARE, '''<p>Välkommen som kursledare ...</p>'''),
(DELTAGARE, '''<p>Välkommen som deltagare ... anmäld till {courses}.</p>'''),
(ALLA, '''<p>Information for everyone ...</p>
</body>
'''),
]
```

**Audience** decides who gets the part. It is one of:

- `DELTAGARE` – only people with the role deltagare,
- `KURSLEDARE` – only people with the role kursledare,
- `ALLA` – everyone, including people with no role,
- a set of roles, e.g. `{DELTAGARE, KURSLEDARE}` – anyone with at least one of
  them (this differs from `ALLA`, which also includes people with no role).

Someone with both roles gets the parts for both, in the order they appear in
`SECTIONS`. The roles are worked out in `send_all` (see above).

**html** is a plain string, and the parts are simply concatenated in order, so
together they must form one valid HTML document: the first part opens
`<html>`/`<body>`, the last closes `</body>`. Keep that in mind when adding or
removing the first or last part. The plain text version of the mail is made
from the finished HTML automatically.

**Fields** are inserted with Python's `str.format`, so these placeholders can be
used in any part:

| Placeholder  | Value                                                                               |
|--------------|-------------------------------------------------------------------------------------|
| `{name}`     | First name of the recipient                                                         |
| `{courses}`  | The courses they take as a participant, e.g. `kursen X` or `kurserna X, Y och Z` (empty for someone who only leads) |
| `{logimsg}`  | The Logi section (floor sleeping or hotel), empty if neither                         |
| `{skola}`    | ` i samarbete med Sensus`, or empty for the course *Leda scouting* or no course     |

Because `str.format` is used, a literal `{` or `}` in the text (for example in
inline CSS) must be written as `{{` or `}}`, and any placeholder not in the table
above gives a `KeyError`.

**To change the wording** just edit the text in the relevant part.

**To use the scripts for another purpose** (another event, another kind of
mail):

1. Replace the text in `SECTIONS`, keeping the first/last part structure above.
   Remove parts you do not need; delete the placeholders you do not use.
2. Change the subject lines in `send_all` (`subject = ...`), which are chosen
   there: one for people who are only kursledare, one for everyone else.
3. If you need a new placeholder, add it as a keyword argument in the
   `compose(...)` call in `send_all` and compute its value there (or in a helper
   like `logimsg`). To have a part for a new group of people, add a role
   constant, add it to the roles set in `send_all`, and use it as the audience.
4. The attachments are added in `make_message` (the program PDF) and `send_all`
   (the course lists for kursledare); change or remove them there. If the mail
   should have no lists, the kursledare role as it is worked out depends on
   them, so adjust that logic too.
5. Check the result with `--save DIR` and open the `.html` files before sending
   anything.

## Notes

- **Credentials**: `mail.py` currently has the SMTP login (`IDENTITY` and
  `PASSWORD`) written directly in the source. Consider moving the password to
  an environment variable and rotating it, especially if the repository is ever
  shared.
- The input data and generated files contain personal data (including
  personnummer in `sensus/`) and are deliberately git-ignored. Do not commit
  them.
