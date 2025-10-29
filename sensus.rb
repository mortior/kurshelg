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

kl = db.prepare("SELECT DISTINCT kurs,namn,personnummer,email,mobil FROM deltagare INNER JOIN kursledare ON deltagare.id = kursledare.id ORDER BY kurs;")

kursledare = Hash.new { |h,k| h[k] = [] }

kl.execute.each do |r|
  kurs,*who
  kursledare[kurs] << who
end

def max(a,b)
  a < b ? b : a
end

OFFSET = 3

kurslista.each do |kurs,kurspass|
  xlsx = RubyXL::Workbook.new
  xlsx.worksheets.delete_at(0)

  kurspass.each do |pass, deltagare|

    ws = xlsx.add_worksheet("Kurspass #{pass}")

    w = [ 10, 10, 10, 10, 10 ]

    rubrik = ws.add_cell(0, 0, kurs)
    rubrik.change_font_bold(true)
    rubrik.change_font_size((1.2*rubrik.font_size).to_i)
    ws.add_cell(1, 0, "kurspass: #{pass}")
    
    ["Namn", "Personnummer", "E-post", "Telefonnummer"].each_with_index do |text,col| 
      cell = ws.add_cell(OFFSET, col, text)
      cell.change_font_bold(true)
      [:bottom,:left,:right].each do |border|
        cell.change_border(border, 'thin')
      end
      w[col] = max(w[col], (1.3*text.length).to_i)
    end
    
    deltagare.each_with_index do |d, row|
      d.each_with_index do |val, col|
        cell = ws.add_cell(OFFSET + row + 1, col, val)
        [:top,:bottom,:left,:right].each do |border|
          cell.change_border(border, 'thin')
        end
        w[col] = max(w[col], (val || "").length)
      end
    end

    w.each_with_index { |width,col| ws.change_column_width(col, width) }
  end

  fil = kurs.gsub(/[\/ :?.,]/,'_')
  
  xlsx.write(File.join("sensus", "#{fil}.xlsx"))
end


#st = db.prepare("SELECT namn,email FROM deltagare WHERE id NOT IN SELECT deltagare FROM kurser ORDER BY namn;")
