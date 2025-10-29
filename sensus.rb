#! /usr/bin/ruby

require 'rubygems'
require 'sqlite3'
require 'rubyXL'
require 'rubyXL/convenience_methods'

sqlfile, = ARGV

db = SQLite3::Database.open(sqlfile)

st = db.prepare("SELECT kurs,kurspass,namn,personnummer,email,mobil FROM deltagare INNER JOIN kurser ON deltagare.id = kurser.deltagare ORDER BY kurs,kurspass,namn;")

kurslista = Hash.new { |h,k| h[k] = Hash.new {|h2,k2| h2[k2] = [] }}

st.execute.collect do |r|
  kurs,kurspass,*who = r
  kurslista[kurs][kurspass] << who
end

kl = db.prepare("SELECT DISTINCT kurs,namn,personnummer,email,mobil FROM deltagare INNER JOIN kursledare ON deltagare.id = kursledare.deltagare ORDER BY kurs;")

kursledare = Hash.new { |h,k| h[k] = [] }

kl.execute.each do |r|
  kurs,*who = r
  kursledare[kurs] << who
end

def max(a,b)
  a < b ? b : a
end

def fill_sheet(ws, title, columns, data)

  w = Array.new(columns.length, 10)

  rubrik = ws.add_cell(0, 0, title)
  rubrik.change_font_bold(true)
  rubrik.change_font_size((1.2*rubrik.font_size).to_i)

  offset = 3

  columns.each_with_index do |text,col|
    cell = ws.add_cell(offset, col, text)
    cell.change_font_bold(true)
    [:bottom,:left,:right].each do |border|
      cell.change_border(border, 'thin')
    end
    w[col] = max(w[col], (1.3*text.length).to_i)
  end

  data.each_with_index do |d, row|
    d.each_with_index do |val, col|
      cell = ws.add_cell(offset + row + 1, col, val)
      [:top,:bottom,:left,:right].each do |border|
        cell.change_border(border, 'thin')
      end
      w[col] = max(w[col], (val || "").length)
    end
  end
  w.each_with_index { |width,col| ws.change_column_width(col, width) }
end

kurslista.each do |kurs,kurspass|

  next unless kursledare.has_key? kurs

  xlsx = RubyXL::Workbook.new
  xlsx.worksheets.delete_at(0)

  cols = ["Namn", "Personnummer", "E-post", "Telefonnummer"]

  klws = xlsx.add_worksheet("Kursledare")
  fill_sheet(klws, "Kursledare", cols, kursledare[kurs])

  kurspass.each do |pass, deltagare|
    ws = xlsx.add_worksheet("Kurspass #{pass}")
    fill_sheet(ws, "Kurspass #{pass}", cols, deltagare)
  end

  fil = kurs.gsub(/[\/ :?.,()]/,'_')

  xlsx.write(File.join("sensus", "#{fil}.xlsx"))
end


#st = db.prepare("SELECT namn,email FROM deltagare WHERE id NOT IN SELECT deltagare FROM kurser ORDER BY namn;")
