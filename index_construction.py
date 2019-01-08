# Vikram Sunil Bajaj (vsb259)
from struct import pack
# import json


def vb_encode(number):  # varbyte encoding of a number
    bytes = []
    while True:
        bytes.insert(0, number % 128)
        if number < 128:
            break
        number //= 128
    bytes[-1] += 128
    return pack('%dB' % len(bytes), *bytes)


def get_gaps(arr):
    """ gets element-wise gaps (used to get gaps between doc ids) """
    return [arr[0]] + [arr[i]-arr[i-1] for i in range(1, len(arr))]


def build_index_lexicon(postings_file):
    """ builds the compressed inverted index and lexicon using the final postings file """
    lexicon = {}

    lex_file = open('lexicon.txt', 'w')  # lexicon file pointer
    inverted_index = open('inverted_index.dat', 'wb')  # inverted index file pointer (.dat for binary file)

    with open(postings_file, 'r') as f:
        for line in f:
            line_split = line.split(',')

            term = line_split[0]
            doc_id = int(line_split[1])
            freq = int(line_split[2])

            if term not in lexicon:
                temp_term = term
                file_pointer = inverted_index.tell()  # to get the start position of the inverted list for a term
                lexicon[term] = [file_pointer]
                doc_ids_list = []
                freq_list = []
            while temp_term in lexicon:
                doc_ids_list.append(doc_id)
                freq_list.append(freq)
                line = next(f)
                line_split = line.split(',')
                if len(line_split) == 3:
                    temp_term = line_split[0]
                    doc_id = int(line_split[1])
                    freq = int(line_split[2])
            lexicon[term].append(len(doc_ids_list))  # number of docs containing the term
            # for each term, lexicon stores [start of inverted list, num of docs containing term] (term is key)
            doc_ids_gaps = get_gaps(doc_ids_list)  # get gaps between doc_ids (ex. [10,20,50,90] becomes [10,10,30,40])
            vb_encoded_gaps = [vb_encode(g) for g in doc_ids_gaps]  # varbyte encoding of the gaps
            vb_encoded_freq = [vb_encode(fr) for fr in freq_list]  # varbyte encoding the frequencies
            # write 'term, start of inverted list, num of docs containing term' to lexicon file
            lex_file.write('%s, %d, %d\n' % (term, lexicon[term][0], lexicon[term][1]))
            # write vb_encoded_gaps, vb_encoded_freq to inverted_index.dat
            for g in vb_encoded_gaps:
                inverted_index.write(g)
            for fr in vb_encoded_freq:
                inverted_index.write(fr)
    lex_file.close()
    inverted_index.close()
    # create lexicon dict using json
    # with open('lexicon_dict.json', 'w') as f:
    #     json.dump(lexicon, f)


build_index_lexicon('sorted_postings/final_postings/final_postings.txt')
# index and lexicon get generated in 2hr 20min

