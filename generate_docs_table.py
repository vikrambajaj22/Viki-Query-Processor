# Vikram Sunil Bajaj (vsb259)
import string
import sqlite3
import os
import gzip

# generates a SQL Table with doc_id, URL, page_text (ASCII text only) (as String) for snippet generation

conn = sqlite3.connect('web_search_engine.db')

c = conn.cursor()

c.execute("CREATE TABLE docs (doc_id integer primary key, url text, page_text text)")

# takes 4hr 25min to create the table for 150 WET files
doc_id = -1
doc_dict = {}

for filename in os.listdir('wet_files'):
    print('Parsing', filename)
    with gzip.open('wet_files/' + filename, 'rt', encoding='utf-8') as f:
        for _ in range(18):  # skip the beginning of the file i.e. the part before the first page
            next(f)
        for line in f:
            if 'WARC/1.0' in line:  # every new page starts with this header information
                if doc_id == -1:
                    pass
                else:
                    url = target_url_line[target_url_line.index(':') + 2:-1]
                    page_text = ' '.join(doc)
                    c.execute("INSERT INTO docs VALUES (?, ?, ?)", (doc_id, url, page_text))
                doc_id += 1
                doc = []  # stores document temporarily
                next(f)  # skip a line
                target_url_line = f.readline()
                for _ in range(6):  # skip rest of header
                    next(f)
            else:
                # remove non alpha-numeric char (incl. punctuation) first
                for term in (t for t in
                             ''.join(ch for ch in line.strip() if ch not in string.punctuation).split()):  # generator
                    if all(ord(ch) > 32 and ord(ch) < 127 for ch in
                           term):  # checking if all characters in the term are ASCII
                        # 0 through 31, and 127, represent non-printable control characters; 32 is space)
                        doc.append(term.lower())  # storing in lowercase in doc

print('Table Created')
conn.commit()  # save changes to db
conn.close()  # close connection to db

# fetching record for a given doc_id
conn = sqlite3.connect('web_search_engine.db')

c = conn.cursor()
c.execute('SELECT * FROM docs WHERE doc_id=50')
print(c.fetchone())
conn.close()
