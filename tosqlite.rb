#! /usr/bin/ruby
# coding: utf-8

require 'rubygems'

require 'sqlite3'
require 'rubyXL'

def read_file(file)
  sheet = RubyXL::Parser.parse(file)[0]

  head,*rows = sheet.collect do |r|
    r.cells.collect { |cell| cell&.value }
  end

  rows.collect { |r| head.zip(r).to_h }
end

# KURSPASS23 = { "Tälja i färskt trä (kurspass 1)" => "1",
#                "Tovning: våttovning (kurspass 2)" => "2",
#                "Tovning: torrtovning (kurspass 3)" => "3",
#                "Workshop i tal och pondus (kurspass 1)" => "1",
#                "Tenngjutning" => "2",
#                "Läderhantverk" => "4-5",
#                "Leda scouting" => "1-5",
#                "Tovning: torrtovning (kurspass 2)" => "2",
#                "Repslagning" => "1",
#                "Tälja i färskt trä (kurspass 2)" => "2",
#                "Slipa kniv och yxa" => "3",
#                "Tälja advanced" => "4-5",
#                "Återbrukspyssel" => "4",
#                "Paracord (kurspass 5)" => "5",
#                "Tovning: våttovning (kurspass 1)" => "1",
#                "Sjukvård för scoutledare" => "2-3",
#                "Grundutbildning i vuxen-HLR (kurspass 4)" => "4",
#                "Workshop i tal och pondus (kurspass 5)" => "5",
#                "Tagling - splitsning" => "2",
#                "Paracord (kurspass 3)" => "3",
#                "Tenntrådsarmband" => "4",
#                "Luffarslöjd (kurspass 5)" => "5",
#                "Trygga möten: fördjupning" => "4",
#                "Grundutbildning i vuxen-HLR (kurspass 5)" => "5",
#                "Lär dig sticka" => "1-3",
#                "Luffarslöjd (kurspass 2)" => "2",
#                "Workshop: Ditt bästa knopmöte" => "3",
#                "Intro Scouternas program" => "1",
#                "Barn utanför boxen" => "1-5" }

# KURSPASS24 = {
#   "Leda scouting" => "1-5",
#   "Leda avdelning" => "1-5",
#   "Leda kår" => "1-5",
#   "Barn utanför boxen" => "1-5",
#   "Grundutbildning i vuxen-HLR (kurspass 1)" => "1",
#   "Grundutbildning i vuxen-HLR (kurspass 3)" => "3",
#   "Bildstöd - för att en bild säger mer än 1 000 ord (kurspass 3)" => "3",
#   "Bildstöd - för att en bild säger mer än 1 000 ord (kurspass 5)" => "5",
#   "Hur du skapar spännande sjukvårdsmöten för scouterna" => "1-2",
#   "Hur man arrangerar scoutarrangemang i fjällen (sommartid)" => "5",
#   "Intro Scouternas program" => "5",
#   "Luffarslöjd (kurspass 2)" => "2",
#   "Luffarslöjd (kurspass 3)" => "3",
#   "Läderhantverk" => "4-5",
#   "Lär dig sticka" => "2-3",
#   "Praktisk scouting för (nya) ledare" => "1-3",
#   "Repslagning (kurspass 1)" => "1",
#   "Repslagning (kurspass 4)" => "4",
#   "Scoutmetoden" => "1",
#   "Slipa kniv och yxa" => "3",
#   "Tagling - Splitsning" => "2",
#   "Tenntrådsarmband" => "4",
#   "Trygga möten: fördjupning" => "4",
#   "Tälja i fäskt trä (kurspass 1)" => "1",
#   "Tälja i fäskt trä (kurspass 2)" => "2",
#   "Ukulele för nybörjare" => "1-3",
#   "Återbrukspyssel" => "4"
# }

KURSPASS25 = {
"Bandvävning (kurspass 1)" => "1",
"Bandvävning (kurspass 2)" => "2",
"Bandvävning (kurspass 3)" => "3",
"Barn utanför boxen" => "1-5",
"Bildstöd – för att en bild säger mer än 1 000 ord (kurspass 1)" => "1",
"Bildstöd – för att en bild säger mer än 1 000 ord (kurspass 5)" => "5",
"Grundutbildning i vuxen-HLR (kurspass 1)" => "1",
"Grundutbildning i vuxen-HLR (kurspass 3)" => "3",
"Hur du skapar spännande sjukvårdsmöten för scouterna" => "4-5",
"Hur förmedlar vi scoutings värderingar?" => "1-5",
"Hållbar mat i scoutverksamhet" => "2-3",
"Intro Scouternas program" => "4",
"Korgflätning (kurspass 4)" => "4",
"Korgflätning (kurspass 5)" => "5",
"Leda scouting" => "1-5",
"Luffarslöjd (kurspass 4)" => "4",
"Luffarslöjd (kurspass 5)" => "5",
"Lär dig sticka" => "2-3",
"Mat, mellis och Muurikka (kurspass 1)" => "1",
"Mat, mellis och Muurikka (kurspass 4)" => "4",
"Nåltovning (kurspass 4)" => "4",
"Nåltovning (kurspass 5)" => "5",
"Praktisk scouting för (nya) ledare" => "1-3",
"Praktisk utbildning i kniv- och yxslipning" => "3",
"Repslagning (kurspass 1)" => "1",
"Repslagning (kurspass 4)" => "4",
"Scoutmetoden (kurspass 1)" => "1",
"Scoutmetoden (kurspass 5)" => "5",
"Tagling – splitsning (kurspass 2)" => "2",
"Tagling – splitsning (kurspass 5)" => "5",
"Trygga möten: fördjupning" => "2",
"Tälja i färskt trä (kurspass 1)" => "1",
"Tälja i färskt trä (kurspass 2)" => "2",
"Workshop: Enkla läderhantverk (kurspass 4)" => "4",
"Workshop: Enkla läderhantverk (kurspass 5)" => "5",
"Workshop: Lekar för alla åldrar" => "3",
"Workshop: Makramé i hundra knutar (kurspass 1)" => "1",
"Workshop: Makramé i hundra knutar (kurspass 2)" => "2",
"Workshop: Makramé i hundra knutar (kurspass 3)" => "3",
"Våttovning (kurspass 3)" => "3",
"Våttovning (kurspass 4)" => "4"
}

RAPPORT = [ "Medlemsnummer", "Namn", "Kön", "Personnummer", "E-post", "Mobiltelefon", "Adress", "Postnummer", "Postort", "Anmäld", "Närvaro" ]

rapport,anmalan,output, = ARGV

db = SQLite3::Database.new(output)

db.execute <<-SQL
  CREATE TABLE IF NOT EXISTS rapport (
    id    TEXT NOT NULL,
    namn  TEXT NOT NULL,
    sex   TEXT NOT NULL,
    personnummer TEXT,
    email TEXT NOT NULL,
    mobil TEXT NOT NULL,
    adress TEXT NOT NULL,
    postnummer TEXT NOT NULL,
    postort    TEXT NOT NULL,
    anm   TEXT NOT NULL,
    narvaro TEXT NOT NULL,
    PRIMARY KEY (id)
  );
SQL

db.execute <<-SQL
  CREATE TABLE IF NOT EXISTS kurser (
    deltagare  TEXT NOT NULL,
    kurs       TEXT NOT NULL,
    kurspass   TEXT NOT NULL,
    PRIMARY KEY (deltagare, kurs, kurspass)
  );
SQL

db.execute <<-SQL
  CREATE TABLE IF NOT EXISTS kursledare (
    deltagare  TEXT NOT NULL,
    kurs       TEXT NOT NULL,
    PRIMARY KEY (deltagare, kurs)
  );
SQL

db.execute <<-SQL
  CREATE TABLE IF NOT EXISTS form (
    id       TEXT NOT NULL,
    kaar     TEXT NOT NULL,
    grupp    TEXT NOT NULL,
    fredag   BOOLEAN NOT NULL,
    lordag   BOOLEAN NOT NULL,
    sondag   BOOLEAN NOT NULL,
    funktion TEXT,
    allergi  TEXT,
    logi     TEXT,
    kompisar TEXT,
    PRIMARY KEY (id)
  );
SQL


deltagare = read_file(rapport)

db.transaction do |t|
  st = t.prepare("INSERT INTO rapport VALUES(?,?,?,?,?,?,?,?,?,?,?);")
  deltagare.each do |row|
    begin
      st.execute(RAPPORT.collect {|f| row[f]})
    rescue 
      p RAPPORT.collect {|f| row[f]}
      raise
    end
  end
end

db.transaction do |t|
  st = t.prepare("INSERT INTO kurser VALUES (?,?,?);")
  deltagare.each do |row|
    id = row["Medlemsnummer"]
    row.each do |k,v|
      if k =~ /Anm.*ld till (.*)/ && v == "Ja"
        pass = KURSPASS25[$1]
        namn = $1.sub(/ \(kurspass \d\)/,'')
        st.execute([id, namn, pass])
      end
    end
  end
end

kurser = KURSPASS25.keys.collect do |kurs|
  kurs.sub(/ \(kurspass \d\)/, '')
end.sort.uniq

deltagare = read_file(anmalan)


db.transaction do |t|
  re = Regexp.compile("(#{kurser.join('|')}), (.*)")
  st = t.prepare("INSERT INTO kursledare VALUES(?,?);")
  deltagare.each do |row|
    id = row["Medlemsnummer"]
    k = row['Grundläggande - Vilken eller vilka kurser ska du leda?']
    next unless k
    if k =~ re
      k.split(/, /).each { |kk| st.execute([id, kk]) }
    else
      st.execute([id, k])
    end
  end
 end

db.transaction do |t|
  st = t.prepare("INSERT INTO form VALUES(?,?,?,?,?,?,?,?,?,?);")
  deltagare.each do |row|
    id = row["Medlemsnummer"]
    kar = row["Kår"]
    avg = $1 if row["Deltagaravgift"] =~ /(.*):.*/

    dagar = (row["Grundläggande - Lördag eller söndag?"] || '-').downcase
    dagar = "lördag,söndag" if dagar == "-"

    fredag = (row["Grundläggande - Kommer du redan på fredag kväll?"] == "Ja") ? 1 : 0
    lordag = (dagar =~ /lördag/) ? 1 : 0
    sondag = (dagar =~ /söndag/) ? 1 : 0

    funktion = row["Grundläggande - Vilken är din huvudsakliga funktion på Upplandskurserna?"]
    funktion = nil if funktion == "-"

    allergi = row["Allergiinformation och matpreferenser - Okej, vilka då?"]
    allergi = nil if allergi == "-"

    logi = row["Logi - Välj logiform"]
    logi = $1 if logi =~ /Boende i (.*)/
    logi.downcase! if logi != nil
    logi = nil if logi == "-"

    kompisar = row["Logi - Ange rumskompisar"]
    kompisar = row[ "Logi - Ange rumskompis"] if kompisar == '-'
    kompisar = nil if kompisar == '-'
    
    st.execute([id, kar, avg, fredag,lordag,sondag, funktion, allergi, logi, kompisar])
  end
end

db.execute('CREATE TABLE deltagare AS SELECT * FROM rapport INNER JOIN form ON rapport.id = form.id WHERE anm = "Ja";')
db.execute('CREATE TABLE kurslista AS SELECT namn,email,group_concat(kurs, ",") AS kurser,logi FROM deltagare INNER JOIN kurser ON deltagare.id = kurser.deltagare GROUP BY id ORDER BY kurser;')
