#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""template.py: Description of what the module does."""

from optparse import OptionParser
import logging
import json
from multiprocessing import Pool, cpu_count, Lock, Value
from nltk.tag import stanford
import senna
import nltk

__author__ = "Rami Al-Rfou"
__email__ = "rmyeid@gmail.com"

LOG_FORMAT = "%(asctime).19s %(levelname)s %(filename)s: %(lineno)s %(message)s"

#tagger = stanford.StanfordTagger('/media/data/NER/stanford/pos/models/left3words-wsj-0-18.tagger',
#                                 '/media/data/NER/stanford/pos/stanford-postagger.jar',
#                                 encoding='utf-8')
tagger = senna.SennaTagger('/media/petra/NER/senna-v2.0', encoding='utf-8')

i = 0
size = 0
samples = []
lock = Lock()

sent_tokenizer =  nltk.data.load('tokenizers/punkt/english.pickle')
tree_tokenizer = nltk.TreebankWordTokenizer()
word_punct_tokenizer = nltk.WordPunctTokenizer()
punkt_word_tokenizer = nltk.PunktWordTokenizer()
whitespace_tokenizer = nltk.WhitespaceTokenizer()

def tokenize(text):
  sentences = filter(lambda x: x , sent_tokenizer.tokenize(text.strip()))
  tokens = [punkt_word_tokenizer.tokenize(sentence) for sentence in sentences]
  return tokens

def process(labeled_comments):
  global i
  ids, comments, langs, users, page_ids, page_titles, times, levels = zip(*labeled_comments)
  tokenized_comments = [tokenize(comment) for comment in comments]
  tagged_comments = tagger.corpus_tag(tokenized_comments)
  results = zip(ids, tagged_comments, langs, users, page_ids, page_titles, times, levels)
  lock.acquire()
  i += len(ids)
  lock.release()
  percentage = '%.6f' % (i/float(len(samples)))
  print percentage
  return results

def clean_samples(labeled_samples):
  ids, comments, labels = zip(*labeled_samples)
  clean_comments = []
  for comment in comments:
    clean_comments.append(filter(lambda x:x, comment))
  clean_comments = filter(lambda x: x and len(x[0]) > 1, clean_comments)
  results = zip(clean_comments, labels)
  return results

def main(options, args):
  global samples
  samples = json.load(open(options.filename, 'r'))
  logging.info("Samples are loaded")
  p = Pool(cpu_count()-1)
  size = len(samples)/(15*cpu_count())
  splitted_samples = [samples[i:i+size] for i in range(0, len(samples), size)]
  results = []
  results = p.map(process, splitted_samples)
  logging.info("Results are computed, to be merged")
  results = [r for partial in results for r in partial]
  logging.info("Results are merged, to be dumped")
  json.dump(results, open(options.filename+'.pos', 'w'))


if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("-f", "--file", dest="filename", help="Input file")
  parser.add_option("-l", "--log", dest="log", help="log verbosity level",
                    default="INFO")
  (options, args) = parser.parse_args()

  numeric_level = getattr(logging, options.log.upper(), None)
  logging.basicConfig(level=numeric_level, format=LOG_FORMAT)
  main(options, args)

