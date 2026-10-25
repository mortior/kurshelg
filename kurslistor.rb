#! /usr/bin/ruby

# Generates both kinds of course lists from the database made by tosqlite.rb:
#   listor/  - lists for the course leaders (kursledare first, no personnummer)
#   sensus/  - lists for Sensus (with personnummer, only courses with kursledare)

require 'rubygems'
require 'fileutils'
require 'sqlite3'
require 'rubyXL'
require 'rubyXL/convenience_methods'

sqlfile, = ARGV

db = SQLite3::Database.open(sqlfile)

Person = Struct.new(:leader, :namn, :personnummer, :email, :mobil)

HEADINGS = {
  namn: "Namn",
  personnummer: "Personnummer",
  email: "E-post",
  mobil: "Telefonnummer"
}

LISTOR_FIELDS = [:namn, :email, :mobil]
SENSUS_FIELDS = [:namn, :personnummer, :email, :mobil]

OFFSET = 3

# Participants per course and kurspass; leaders are flagged
st = db.prepare("SELECT kurser.kurs,kurspass,kursledare.kurs IS NOT NULL,namn,personnummer,email,mobil FROM deltagare INNER JOIN kurser ON deltagare.id = kurser.deltagare LEFT JOIN kursledare ON kursledare.deltagare = kurser.deltagare AND kursledare.kurs = kurser.kurs ORDER BY kurser.kurs,kurspass,namn;")

kurslista = Hash.new { |h,k| h[k] = Hash.new {|h2,k2| h2[k2] = [] }}

st.execute.each do |r|
  kurs,kurspass,leader,*who = r
  kurslista[kurs][kurspass] << Person.new(leader == 1, *who)
end

def max(a,b)
  a < b ? b : a
end

# Adds a sheet with a title (and optional subtitle) and yields a lambda
# table.call(row, people, label=nil) that writes a table of people starting at
# row, preceded by a label if given, and returns the first free row.
def add_sheet(xlsx, name, title, fields, subtitle: nil)
  ws = xlsx.add_worksheet(name)
  w = Array.new(fields.length, 10)

  rubrik = ws.add_cell(0, 0, title)
  rubrik.change_font_bold(true)
  rubrik.change_font_size((1.2*rubrik.font_size).to_i)
  ws.add_cell(1, 0, subtitle) if subtitle

  table = lambda do |row, people, label = nil|
    if label
      ws.add_cell(row, 0, label).change_font_bold(true)
      row += 1
    end

    fields.each_with_index do |field,col|
      text = HEADINGS[field]
      cell = ws.add_cell(row, col, text)
      cell.change_font_bold(true)
      [:bottom,:left,:right].each do |border|
        cell.change_border(border, 'thin')
      end
      w[col] = max(w[col], (1.3*text.length).to_i)
    end

    people.each_with_index do |person, i|
      fields.each_with_index do |field,col|
        val = person[field]
        cell = ws.add_cell(row + i + 1, col, val)
        [:top,:bottom,:left,:right].each do |border|
          cell.change_border(border, 'thin')
        end
        w[col] = max(w[col], (val || "").length)
      end
    end

    row + people.size + 1
  end

  yield table

  w.each_with_index { |width,col| ws.change_column_width(col, width) }
end

def write_workbook(xlsx, dir, kurs)
  fil = kurs.gsub(/[\/ :?.,()]/,'_')
  FileUtils.mkdir_p(dir)
  xlsx.write(File.join(dir, "#{fil}.xlsx"))
end

def new_workbook
  xlsx = RubyXL::Workbook.new
  xlsx.worksheets.delete_at(0)
  xlsx
end

# Writes the lists of one kind: a workbook per course with a sheet per
# kurspass, the kursledare in a table on top of the participants
def write_lists(kurslista, dir, fields, skip_leader_only: false, only_courses_with_leaders: false)
  kurslista.each do |kurs,kurspass|
    next if only_courses_with_leaders && kurspass.values.flatten.none?(&:leader)

    xlsx = new_workbook

    kurspass.each do |pass, deltagare|
      next if skip_leader_only && deltagare.all?(&:leader)

      ledare, ovriga = deltagare.partition(&:leader)

      add_sheet(xlsx, "Kurspass #{pass}", kurs, fields, subtitle: "kurspass: #{pass}") do |table|
        row = table.call(OFFSET, ledare, "Kursledare")
        table.call(row + 1, ovriga, "Deltagare") unless ovriga.empty?
      end
    end

    write_workbook(xlsx, dir, kurs) unless xlsx.worksheets.empty?
  end
end

write_lists(kurslista, "listor", LISTOR_FIELDS, skip_leader_only: true)
write_lists(kurslista, "sensus", SENSUS_FIELDS, only_courses_with_leaders: true)
