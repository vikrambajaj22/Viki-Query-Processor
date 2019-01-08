# Vikram Sunil Bajaj (vsb259)
import gzip
import string
import os
from collections import Counter

if not os.path.isdir('sorted_postings'):
    os.mkdir('sorted_postings')

# generates 1 sorted postings file per WET file
# keeps only ascii characters (this gets rid of all non-english characters), after removing punctuation
# postings of form term, docid, freq
# sorts postings before writing to file
# takes about 7hr 20min for 150 WET files i.e. for 5,906,499 pages/docs (approx. 224 docs per sec)

doc_id = -1

if not os.path.isdir('sorted_postings'):
    os.mkdir('sorted_postings')

for filename in os.listdir('wet_files'):
    postings = []
    print('Parsing', filename)
    with gzip.open('wet_files/'+filename, 'rt', encoding='utf-8') as f:
        for _ in range(18):  # skip the beginning of the file i.e. the part before the first page
            next(f)
        for line in f:
            if 'WARC/1.0' in line:  # every new page starts with this header information
                if doc_id == -1:
                    pass
                else:
                    # generate postings for doc, using term freq in that doc
                    freq = Counter(doc)  # gets dict with freq of each term in doc
                    for term in freq:
                        postings.append((term, doc_id, freq[term]))
                doc_id += 1
                doc = []  # stores document temporarily
                for _ in range(8):
                    next(f)  # skip header information
            else:
                # remove non alpha-numeric char (incl. punctuation) first
                for term in (t for t in ''.join(ch for ch in line.strip() if ch not in string.punctuation).split()):
                    # generator used as an iterable instead of a list for memory efficiency
                    if all(ord(ch)>32 and ord(ch)<127 for ch in term):  # checking if all characters in term are ASCII
                        # (0 through 31, and 127, represent non-printable control characters; 32 is space)
                        doc.append(term.lower())  # storing in lowercase in doc
    # sort postings by term
    print('Sorting Postings...')
    postings.sort()
    # dump page postings to a file
    print('Writing Postings to File...')
    with open("sorted_postings/"+filename+"_sorted_postings.txt", "w") as p:
        p.writelines('%s, %s, %s\n' % (str(posting[0]), str(posting[1]), str(posting[2])) for posting in postings)
    print('\n')

# using Unix merge to merge the 150 sorted posting files into a single file
# takes about 1hr 20min for 150 files with buffer-size 1024; final file has 1,611,630,894 postings
os.chdir('sorted_postings')
os.system('bash; sort -m -k1,1 -k2n,2 --buffer-size=1024 *.txt > final_postings.txt; mkdir final_postings')
# uses the new Linux bash in Windows 10, also -m: merge, dont re-sort files
# -k1,1 -k2n,2 sorts by first field (term), then numeric sort by second field (doc_id)
os.system('bash; mv final_postings.txt final_postings')
os.chdir('..')
