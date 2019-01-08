# Vikram Sunil Bajaj (vsb259)
# first, download the WET files file list (CC-MAIN-2018-39/wet.paths.gz)
# from http://commoncrawl.org/2018/10/september-2018-crawl-archive-now-available/ and extract it.
# then, run this code.

# import packages
import os
import requests

# create a directory to store the downloaded files
if not os.path.exists('wet_files'):
    os.mkdir('wet_files')

# open the extracted file list
with open('wet.paths/wet.paths', 'r') as f:
    file_paths = f.readlines()

# get the first 150
first_150 = ['https://commoncrawl.s3.amazonaws.com/' + path.strip('\n') for path in file_paths[:150]]

# download the files and store them in the wet_files directory
i = 0
for path in first_150:
    file_name = 'wet_files/' + path[path.rindex('-')+1:]
    if not os.path.exists(file_name):
        print('Downloading File %d ...' % (i+1))
        res = requests.get(path)
        with open(file_name, 'wb') as f:
            f.write(res.content)
    else:
        print(file_name, 'already exists! Skipping File %d' % (i+1))
    i += 1
