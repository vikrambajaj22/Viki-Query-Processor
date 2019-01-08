# Vikram Sunil Bajaj (vsb259)
from flask import Flask, render_template, request
from struct import unpack
from datetime import datetime
import string
import sqlite3
import math
import operator
import heapq


app = Flask('search_engine')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/results.html', methods=['POST'])
def process_query():
    query = request.form['search']
    choice = request.form['choice']
    message = ''
    # process the query
    terms = pre_process_query(query)  # remove punctuation, words with non-ASCII characters, duplicate words,
    # and also convert to lowercase, contains only words that are in lexicon

    global result_docs, result_scores, top_10_urls, term_freqs, snippets
    if len(terms) == 0:
        message += 'No Results'
    else:
        # report words that aren't in lexicon, if any
        unknown_terms = []
        for t in list(set(query.strip().split())):
            if t not in terms:
                unknown_terms.append(t)
        if len(unknown_terms) == 0:
            pass
        else:
            message += 'Terms not in Lexicon: '
            for t in unknown_terms:
                message += t + ', '
            message += 'Results shown below for known terms ...\n'

        start = datetime.now()
        doc_id_lists, freq_lists = get_lists(terms)  # returns lists with doc_ids and freq's for each term

        if choice == 'conjunctive':
            # process with AND semantics i.e. all terms must be in resulting docs
            result_docs = []  # stores doc_ids of results
            # implementing the nextGEQ() interface
            h = []  # heap that will always store top 10 doc_ids based on BM25 scores
            # unsorted lists needed later while computing term frequencies (use .copy() if entire lists are to be used)
            unsorted_doc_id_lists = [x[:1500] for x in doc_id_lists]
            unsorted_freq_lists = [x[:1500] for x in freq_lists]
            # start by sorting the doc_id lists and corresponding freq lists "by length" of lists (makes it faster)
            doc_id_lists.sort(key = len)
            freq_lists.sort(key = len)
            # the aim is to quickly find doc_ids that are present in all sub-lists
            # keeping the first 1500 doc_ids and frequencies
            doc_id_lists = [x[:1500] for x in doc_id_lists]
            freq_lists = [x[:1500] for x in freq_lists]

            max_doc_id = max([doc_list[-1] for doc_list in doc_id_lists])  # compare last elements since ids are ordered
            doc_id = 0
            while doc_id <= max_doc_id:
                doc_id = nextGEQ(doc_id_lists[0], doc_id)  # initially, getting first doc_id in shortest list
                i = 1
                d = doc_id
                while i < len(terms) and d == doc_id:  # checking if doc_id is in lists for all terms
                    d = nextGEQ(doc_id_lists[i], doc_id)
                    i += 1
                if d > doc_id:
                    doc_id = d  # discard previous doc_id since it wasn't in all lists, replace with new one
                elif d == doc_id:
                    # doc_id was in all lists, so get frequencies and compute BM25 score of doc_id
                    score = 0  # BM25 score for doc
                    for i in range(len(terms)):
                        # get index of doc_id in doc_id_list of term
                        doc_index = doc_id_lists[i].index(d)
                        freq = freq_lists[i][doc_index]  # freq of term in d
                        score += bm25_score(terms[i], d, freq)
                    item = (score, d)
                    heapq.heappush(h, item)  # push onto heap
                    h = heapq.nlargest(10, h)  # keep only 10 best doc_ids based on scores
                    doc_id += 1  # increment doc_id
                else:
                    doc_id += 1
            best_docs = heapq.nlargest(10, h)  # final best docs
            result_docs = [x[1] for x in best_docs]  # top_10 doc_ids
            result_scores = [x[0] for x in best_docs]  # corresponding BM25 scores
            top_10_urls = [url_table[x][0] for x in result_docs]  # corresponding URLs
            # term frequencies for result_docs
            term_freqs = {}
            for d in result_docs:
                term_freqs[d] = {}
            for i in range(len(terms)):
                t = terms[i]
                doc_list = unsorted_doc_id_lists[i]
                freq_list = unsorted_freq_lists[i]
                for d in result_docs:
                    if d in doc_list:
                        term_freqs[d][t] = freq_list[doc_list.index(d)]  # freq of t in d
                    else:
                        term_freqs[d][t] = 0
        else:
            # process with OR semantics i.e. any of the terms should be in the doc
            result_docs = []  # stores doc_ids of results
            bm25_scores = {}  # stores BM25 scores for the doc_ids
            term_freqs = {}  # stores frequencies of terms in each doc
            # term_freqs[doc_id] = {t1:#, t2:#, ...tn:#} format
            for i in range(len(terms)):
                t = terms[i]
                doc_list = doc_id_lists[i][:1500]  # doc_id list for term i (first 1500 ids)
                freq_list = freq_lists[i][:1500]  # freq list for term i (first 1500 freq's)
                for j in range(len(doc_list)):
                    if doc_list[j] in bm25_scores:
                        bm25_scores[doc_list[j]] += bm25_score(t, doc_list[j], freq_list[j])
                    else:
                        bm25_scores[doc_list[j]] = bm25_score(t, doc_list[j], freq_list[j])
            # sort dict in desc. order of scores
            sorted_scores = sorted(bm25_scores.items(), key=operator.itemgetter(1), reverse=True)
            top_10 = sorted_scores[:10]
            result_docs = [x[0] for x in top_10]  # top_10 doc_id's
            result_scores = [x[1] for x in top_10]  # top_10 BM25 scores
            top_10_urls = [url_table[x][0] for x in result_docs]  # URLs for result_docs
            # determining term frequencies for each doc_id in the top-10 doc_ids
            for d in result_docs:
                term_freqs[d] = {}
            for i in range(len(terms)):
                t = terms[i]
                doc_list = doc_id_lists[i]
                freq_list = freq_lists[i]
                for d in result_docs:
                    if d in doc_list:
                        term_freqs[d][t] = freq_list[doc_list.index(d)]  # freq of t in d
                    else:
                        term_freqs[d][t] = 0
        snippets = []
        # connect to the database for snippets
        conn = sqlite3.connect('web_search_engine.db')
        c = conn.cursor()
        for d in result_docs:
            snippets.append(get_snippet(d, terms, c))
        end = datetime.now()
        time = (end - start).total_seconds()
        conn.close()
        if len(result_scores) > 0:
            message += 'Results retrieved in %f seconds' % round(time, 2)
        else:
            message += 'No Results'
    if len(result_docs) > 0 and result_scores and top_10_urls and term_freqs and snippets:
        return render_template('results.html', query=query, message=message, choice=choice,
                           result_docs=result_docs, result_scores=result_scores, top_10_urls=top_10_urls,
                           term_freqs=term_freqs, snippets=snippets)
    return render_template('results.html', query=query, message=message, choice=choice)


def get_lists(terms):
    doc_id_lists = []
    freq_lists = []
    f = open('inverted_index.dat', 'rb')
    for term in terms:
        start = lexicon_dict[term][0]
        num_docs = lexicon_dict[term][1]
        pos = f.seek(start)
        decoded = vb_decode(f.read(num_docs*2))  # read doc_ids and frequencies and decode
        doc_gap_list = decoded[:len(decoded)//2]  # actually stores decoded gaps
        freq_list = decoded[len(decoded) // 2:]
        # recover doc_ids
        doc_id_list = [doc_gap_list[0]]
        prev = doc_id_list[0]
        for i in range(1, len(doc_gap_list)):
            doc_id_list.append(prev + doc_gap_list[i])
            prev = doc_id_list[i]
        doc_id_lists.append(doc_id_list)
        freq_lists.append(freq_list)
    f.close()
    return doc_id_lists, freq_lists


def nextGEQ(doc_list, doc_id):
    i = 0
    while i < len(doc_list) and doc_list[i] < doc_id:
        i += 1
    if i == len(doc_list):  # all doc_ids were lesser than doc_id
        return doc_list[i-1]  # the last doc_id in the list
    return doc_list[i]  # the next doc_id which is greater than or equal to doc_id


def bm25_score(term, doc, freq):
    """ terms: query terms, doc: doc_id for which the BM25 is being computed, freq: freq of term in doc """
    k = 1.2
    b = 0.75

    N = len(url_table)
    doc_size = url_table[doc][1]
    K = k * ((1-b)+b*(doc_size/avg_size))

    f_t = lexicon_dict[term][1]  # num of docs that contain term
    f_dt = freq  # freq of term in doc
    bm25 = math.log((N-f_t+0.5)/(f_t+0.5)) * ((k+1)*f_dt)/(K+f_dt)

    return bm25


def get_snippet(d, terms, c):
    c.execute("SELECT page_text FROM docs WHERE doc_id=%d" % d)
    page_text = c.fetchone()[0]
    text_list = page_text.split()
    snippet = ''
    for keyword in terms:
        if keyword in text_list:
            snippet += '... ' + ' '.join(text_list[max(text_list.index(keyword) - 4, 0): text_list.index(keyword)] + [
                '<b>' + keyword + '</b>'] + text_list[
                                                   text_list.index(keyword) + 1: text_list.index(keyword) + 4]) + ' ...'
    return snippet


def pre_process_query(query):
    query = query.lower().strip()
    terms = []
    # processed in the same way as done during posting generation
    for term in ''.join([ch for ch in query if ch not in string.punctuation]).split():
        if all([ord(x)>32 and ord(x)<127 for x in term]):  # ASCII checking
            terms.append(term)
    # keep terms that are in the lexicon
    updated_terms = [t for t in terms if t in lexicon_dict]
    return list(set(updated_terms))  # duplicates removed


def load_lexicon():
    lexicon = {}
    print('Loading Lexicon...')
    lex_start = datetime.now()
    with open('lexicon.txt', 'r') as f:
        for line in f:
            line_split = line.strip().split(', ')
            term = line_split[0]  # term
            start_pos = int(line_split[1])  # start of inverted list in inverted index
            num_docs = int(line_split[2])  # number of docs containing term
            lexicon[term] = (start_pos, num_docs)
    lex_end = datetime.now()
    print('Lexicon Loaded!')
    lex_time = (lex_end - lex_start).total_seconds()
    print('Time to Load Lexicon:', round(lex_time/60, 2), 'min')
    return lexicon


def load_url_table():
    url_table = []  # indexed by doc_id
    avg_size = 0  # average doc size (needed for BM25)
    print('Loading URL Table...')
    url_start = datetime.now()
    with open('url_table.txt', 'r') as f:
        for line in f:
            line_split = line.strip().split(', ')
            doc_id = int(line_split[0])  # doc_id
            url = line_split[1].strip()  # url
            size = int(line_split[2])  # size (number of terms in doc)
            url_table.append((url, size))
            avg_size += size
    url_end = datetime.now()
    print('URL Table Loaded!')
    url_time = (url_end - url_start).total_seconds()
    print('Time to load URL Table:', round(url_time/60, 2), 'min')
    avg_size /= len(url_table)
    return url_table, avg_size


def vb_decode(bytestream):
    n = 0
    numbers = []
    bytestream = unpack('%dB' % len(bytestream), bytestream)
    for byte in bytestream:
        if byte < 128:
            n = 128 * n + byte
        else:
            n = 128 * n + (byte - 128)
            numbers.append(n)
            n = 0
    return numbers


if __name__ == '__main__':
    lexicon_dict = load_lexicon()  # 1min
    url_table, avg_size = load_url_table()  # 1min
    # start the server for the UI
    app.run()
