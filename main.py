"""
Part of speech tagging
Chernivtsi National University
Danylo Dubinin
"""

" 1. Imports "

import nltk
# Natural Language Toolkit
# http://www.nltk.org/

from math import log
from time import clock

import numpy
# Scientific computing
# http://www.numpy.org/

import re
# Regular Expressions

from collections import Counter

import pickle
# A liquid or marinade :) uhmm... I mean...
# Binary protocols for serializing and de-serializing object structures
# https://docs.python.org/3/library/pickle.html


" 2. Global parameters and constants "

" Start and stop symbols embraces sentences. "
STAR = '*'
STOP = 'STOP'

" for smoothing "
RARE = '_RARE_'

" Maximum number of occurances a word must have to be considered rare "
# TODO: parameter identification
RARE_MAX_FREQ = 5

# When probability is zero, its logarithm is undefined, instead we use big
# negative number to denote log(0)
# NOTE: float('-inf') maybe?
#       http://stackoverflow.com/questions/1628026/python-infinity-any-caveats
LOG_OF_ZERO = -1000


" 3. Function definitions "

def split_wordtags(sentences):
    """
    Receives a list of tagged sentences and processes each sentence to generate
    a list of words and a list of tags.
    Start and stop symbols are included in returned lists, as defined by the
    constants STAR and STOP respectively.

    Parameters
    ----------
    sentences : list of str
        Each sentence is a string of space-separated "WORD/TAG" tokens, with a
        newline character in the end.

    Returns
    -------
    words, tags : 2d lists of str
        lists where every element is a list of the words/tags of a particular
        sentence

    """
    words = []
    tags  = []
    for sentence in sentences:
        sentence_split = sentence.split()
        word_tag = [re.split(r'(^.+)/([A-Z.]+$)', pair)[1:3] \
                for pair in sentence_split]
        word_tag = [[STAR]*2]*2 + word_tag + [[STOP]*2]
        word_tag_transposed = numpy.array(word_tag).transpose()
        words.append(list(word_tag_transposed[0]))
        tags .append(list(word_tag_transposed[1]))
    return words, tags

def calculate_q(tags):
    """         
    Takes tags from the training data and calculates tag trigram probabilities.  

    Parameters
    ----------
        tags : list of list of str
            Each element of tags list is list of tags of particular sentence. 

    Returns
    -------
        q_values : dict of tuple:float
            The keys are tuples of str that represent the tag trigram.
            The values are the float log probability of that trigram.

    """
    trigrams = [trigram for sentence in tags \
            for trigram in nltk.trigrams(sentence)]
    bigrams  = [bigram  for sentence in tags \
            for bigram  in nltk.bigrams(sentence)]
    trigrams_c = Counter(trigrams)
    bigram_c   = Counter(bigrams )
    q_values = {trigram: log(count,2)-log(bigram_c[trigram[:-1]],2) \
            for trigram,count in trigrams_c.items()}
    return q_values

# This function takes output from calculate_q() and outputs it in the proper
# format
# TODO: pickle it!
# TODO: docstringificate
def q2_output(q_values, filename):
    outfile = open(filename, "w")
    trigrams = list(q_values.keys())
    trigrams.sort()
    for trigram in trigrams:
        output = " ".join(['TRIGRAM']+ list(trigram)+ [str(q_values[trigram])]])
        outfile.write(output + '\n')
    outfile.close()

# brown_words is a python list where every element is a python list of the
# words of a particular sentence.
def calculate_known(words):
    """
    Takes the words from the training data and returns a set of all of the words
    that occur more than RARE_MAX_FREQ.

    Parameters
    ----------
        words : list of list of str
            Each element of sentence_words is a list with str words of a
            particular sentence enclosed with STAR and STOP symbols.       

    Returns
    -------
        known_words : set of str
            Set of known words.

    """
    words_count = Counter([word for sentence in words for word in sentence])
    known_words = set([word for word,count in words_count.items() \
            if count > RARE_MAX_FREQ])
    return known_words

# Takes the words from the training data and a set of words that should not be
# replaced for '_RARE_'
# Returns the equivalent to brown_words but replacing the unknown words by
# '_RARE_' (use RARE constant)
def replace_rare(brown_words, known_words):
    brown_words_rare = [[word in known_words and word or RARE for word in sentence] for sentence in brown_words]
    return brown_words_rare

# This function takes the ouput from replace_rare and outputs it to a file
def q3_output(rare, filename):
    outfile = open(filename, 'w')
    for sentence in rare:
        outfile.write(' '.join(sentence[2:-1]) + '\n')
    outfile.close()


# Calculates emission probabilities and creates a set of all possible tags
# The first return value is a python dictionary where each key is a tuple in
# which the first element is a word
# and the second is a tag, and the value is the log probability of the emission
# of the word given the tag
# The second return value is a set of all possible tags for this data set
def calc_emission(brown_words_rare, brown_tags):
    tags_flat = [tag for sentence in brown_tags for tag in sentence]
    words_flat = [word for sentence in brown_words_rare for word in sentence]
    assert len(tags_flat) == len(words_flat)
    tags_c = Counter(tags_flat)
    word_tag = zip(words_flat, tags_flat)
    word_tag_c = Counter(word_tag)
    e_values = {k: log(float(c),2)-log(float(tags_c[k[1]]),2) \
            for k,c in word_tag_c.items()}
    taglist = set(tags_flat)
    return e_values, taglist

# This function takes the output from calc_emissions() and outputs it
def q4_output(e_values, filename):
    outfile = open(filename, "w")
    emissions = list(e_values.keys())
    emissions.sort()
    for item in emissions:
        output = " ".join([item[0], item[1], str(e_values[item])])
        outfile.write(output + '\n')
    outfile.close()


# This function takes data to tag (brown_dev_words), a set of all possible tags
# (taglist), a set of all known words (known_words),
# trigram probabilities (q_values) and emission probabilities (e_values) and
# outputs a list where every element is a tagged sentence
# (in the WORD/TAG format, separated by spaces and with a newline in the end,
# just like our input tagged data)
# brown_dev_words is a python list where every element is a python list of the
# words of a particular sentence.
# taglist is a set of all possible tags
# known_words is a set of all known words
# q_values is from the return of calculate_q()
# e_values is from the return of calc_emissions()
# The return value is a list of tagged sentences in the format "WORD/TAG",
# separated by spaces. Each sentence is a string with a
# terminal newline, not a list of tokens. Remember also that the output should
# not contain the "_RARE_" symbol, but rather the
# original words of the sentence!
def viterbi(brown_dev_words, taglist, known_words, q_values, e_values):
    tagged = []
    tags = taglist.difference({STAR,STOP})
    def S(n):
        if n < 2:
            return [STAR]
        elif n == T+2:
            return [STOP]
        else:
            return tags
    N = len(brown_dev_words)
    i = 0
    for sentence in brown_dev_words:
        i += 1
        T = len(sentence)
        pi = [{STAR: {STAR: 0.0}}]
        bp = [None]
        for k in range(2,T+2):
            pi.append({})
            bp.append({})
            for u in S(k-1):
                pi[k-1][u] = {}
                bp[k-1][u] = {}
                for v in S(k):
                    pi_max = float('-inf')
                    w_max = None
                    for w in pi[k-2]:
                        #if not w in pi[k-2] or not u in pi[k-2][w]:
                        #    continue
                        q = q_values.get((w,u,v),LOG_OF_ZERO)
                        if q == LOG_OF_ZERO:
                            s = q
                        else:
                            p = pi[k-2][w][u]
                            e_word = sentence[k-2]
                            if not e_word in known_words:
                                e_word = RARE
                            if not (e_word,v) in e_values:
                                s = LOG_OF_ZERO
                            else:
                                e = e_values[e_word,v]
                                s = p + q + e
                        if s > pi_max:
                            pi_max = s
                            w_max = w
                    if not w_max:
                        continue
                    pi[k-1][u][v] = pi_max
                    bp[k-1][u][v] = w_max
        uv = None
        pi_max = float('-inf')
        for u in S(T):
            for v in S(T+1):
                q = q_values.get((u,v,STOP),LOG_OF_ZERO)
                if q == LOG_OF_ZERO:
                    s = q
                else:
                    s = pi[T][u][v] + q
                if s > pi_max:
                    pi_max = s
                    uv = (u,v)
        y = ['X']*(T+2)
        y[T] = uv[0]
        y[T+1] = uv[1]
        for k in reversed(range(T)):
            y[k] = bp[k+1][y[k+1]][y[k+2]]
        tagged.append(" ".join(["{0}/{1}".format(*pair) \
                for pair in zip(sentence,y[2:])])+" \n")
    return tagged

# This function takes the output of viterbi() and outputs it to file
def q5_output(tagged, filename):
    outfile = open(filename, 'w')
    for sentence in tagged:
        outfile.write(sentence)
    outfile.close()

# This function uses nltk to create the taggers described in question 6
# brown_words and brown_tags is the data to be used in training
# brown_dev_words is the data that should be tagged
# The return value is a list of tagged sentences in the format "WORD/TAG",
# separated by spaces. Each sentence is a string with a
# terminal newline, not a list of tokens.
# FIXME: this one is broken in python 3
def nltk_tagger(brown_words, brown_tags, brown_dev_words):
    assert(len(brown_words)==len(brown_tags))
    training = [zip(brown_words[i], brown_tags[i]) \
            for i in range(len(brown_words))]
    print([list(z) for z in training])
    patterns = [(r'.*(ing|ed|es)$', 'VERB'),(r'.*(est|ous)$', 'ADJ')]
    default_tagger = nltk.DefaultTagger('NOUN')
    regexp_tagger = nltk.RegexpTagger(patterns, backoff=default_tagger)
    bigram_tagger = nltk.BigramTagger(training, backoff=regexp_tagger)
    trigram_tagger = nltk.TrigramTagger(training, backoff=bigram_tagger)
    tagged = [trigram_tagger.tag(tokens) for tokens in brown_dev_words]
    tagged = [" ".join(["{0}/{1}".format(*pair) for pair in tokens]) + ' \n' \
            for tokens in tagged]
    return tagged

# This function takes the output of nltk_tagger() and outputs it to file
def q6_output(tagged, filename):
    outfile = open(filename, 'w')
    for sentence in tagged:
        outfile.write(sentence)
    outfile.close()

DATA_PATH = 'data/'
OUTPUT_PATH = 'output/'

def load_data(name):
    infile = open(DATA_PATH + name + ".txt", "r")
    data = infile.readlines()
    infile.close()
    return data

def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)

def main():
    clock()

    brown_train = load_data('Brown_tagged_train')
    brown_words, brown_tags = split_wordtags(brown_train)
    q_values = calculate_q(brown_tags)
    save_object(q_values, 'objects/q_values.pkl')
    q2_output(q_values, OUTPUT_PATH + 'B2.txt')

    known_words = calculate_known(brown_words)
    save_object(known_words, 'objects/known_words.pkl')
    brown_words_rare = replace_rare(brown_words, known_words)
    q3_output(brown_words_rare, OUTPUT_PATH + "B3.txt")

    e_values, taglist = calc_emission(brown_words_rare, brown_tags)
    save_object(e_values, 'objects/e_values.pkl')
    save_object(taglist, 'objects/taglist.pkl')
    q4_output(e_values, OUTPUT_PATH + "B4.txt")

    del brown_train
    del brown_words_rare

    brown_dev = load_data('Brown_dev')
    brown_dev_words = []
    for sentence in brown_dev:
        brown_dev_words.append(sentence.split(" ")[:-1])
    viterbi_tagged = viterbi(brown_dev_words, taglist, known_words, \
            q_values, e_values)
    q5_output(viterbi_tagged, OUTPUT_PATH + 'B5.txt')

    #nltk_tagged = nltk_tagger(brown_words, brown_tags, brown_dev_words)
    #q6_output(nltk_tagged, OUTPUT_PATH + 'B6.txt')

    print("Ellapsed time: " + str(clock()) + ' sec')

if __name__ == "__main__": main()
