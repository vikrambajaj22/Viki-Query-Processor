# Vikram Sunil Bajaj (vsb259)
import os
import gzip
# import json

# results in url_table json file (Time: 40min, 150 WET files)
doc_id = -1
# url_table = []  # stores url, number of terms (size) of a doc (indexed by doc_id)

url_file = open('url_table.txt', 'w')  # url table file pointer

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
                    # url_table.append((target_url_line[target_url_line.index(':') + 2:-1], len(terms)))
                    url_file.write('%d, %s, %d\n' % (doc_id, target_url_line[target_url_line.index(':') + 2:-1],
                                                     len(terms)))
                doc_id += 1
                terms = []
                next(f)  # skip a line
                target_url_line = f.readline()
                for _ in range(6):  # skip rest of header
                    next(f)
            else:
                terms.extend(line.strip().split())
url_file.close()

# json dump the url_table
# with open('url_table.json', 'w') as f:
#     json.dump(url_table, f)
