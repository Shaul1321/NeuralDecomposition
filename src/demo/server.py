#!/usr/bin/python

import logging
from datetime import datetime

from flask import Flask, request
from flask_cors import CORS, cross_origin

import spacy
import pickle
import sys
from tqdm import tqdm

sys.path.append('src/analysis/')
from evaluate import get_closest_sentence_demo, get_closest_word_demo, get_sentence_representations, Sentence_vector, \
    sentences2words
from embedder import EmbedElmo, EmbedBert
import syntactic_extractor
import copy

app = Flask(__name__)
CORS(app)

nlp = spacy.load('en_core_web_sm')

with open("/home/nlp/lazary/workspace/thesis/NeuralDecomposition/data/interim/encoded_elmo.pickle", "rb") as f:
    data = pickle.load(f)
# sentence_reprs = get_sentence_representations(data)
# with open("sent_rep.pickle", "wb") as f:
#    pickle.dump(sentence_reprs, f)
with open("sent_rep.pickle", "rb") as f:
    sentence_reprs = pickle.load(f)
cca_sentence_reprs = []

elmo_folder = 'data/external/'
options = {'elmo_options_path': elmo_folder + '/elmo_2x4096_512_2048cnn_2xhighway_options.json',
           'elmo_weights_path': elmo_folder + '/elmo_2x4096_512_2048cnn_2xhighway_weights.hdf5'}
embedder = EmbedElmo(options, device=-1)

extractor_path = '/home/nlp/ravfogs/neural_decomposition/src/linear_decomposition/models/cca.perform-pca:False.cca-dim:60.symmetry:False.method:sklearn.pickle'

extractor = syntactic_extractor.CCASyntacticExtractor(extractor_path, numpy=False)

for i, sent in enumerate(tqdm(sentence_reprs)):
    x = Sentence_vector(extractor.extract(sent.sent_vectors), sent.sent_str, sent.doc)
    cca_sentence_reprs.append(x)

words_reprs = sentences2words(sentence_reprs, num_words=50000,
                              ignore_function_words=True)
cca_word_reprs = []
for i, word in enumerate(tqdm(words_reprs)):
    cca_word_reprs.append(extractor.extract(word.word_vector).reshape(-1))



# sent_vecs = extractor.extract(sent_vecs)


def get_logger(model_dir):
    time = str(datetime.now()).replace(' ', '-')
    logger = logging.getLogger(time)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    # create file handler which logs even debug messages
    fh = logging.FileHandler(model_dir + '/' + time + '.log')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


logger = get_logger('./logs/')


def get_token_for_char(doc, char_idx):
    """
    Convert between the characted index to the nlp token index
    :param doc:
    :param char_idx:
    :return:
    """
    for i, token in enumerate(doc):
        if char_idx > token.idx:
            continue
        if char_idx == token.idx:
            return i
        if char_idx < token.idx:
            return i - 1


def get_nearest_sentence(text):
    # text_split = text.split('*')
    # ind = len(text_split[0]) + 1

    # doc = nlp(''.join(text_split))
    # token_ind = get_token_for_char(doc, ind)
    doc = nlp(text)

    closest_sents_syntax = get_closest_sentence_demo(cca_sentence_reprs, doc, embedder, extractor=extractor, k=5,
                                                     method='l2')
    closest_str_syntax = [x.doc.text for x in closest_sents_syntax]

    closest_sents_baseline = get_closest_sentence_demo(sentence_reprs, doc, embedder, extractor=None, k=5, method='l2')
    closest_str_baseline = [x.doc.text for x in closest_sents_baseline]

    return {'syntax': '<br/>'.join(closest_str_syntax), 'baseline': '<br/>'.join(closest_str_baseline)}


def word_vector_to_text(word_vector):
    ind = word_vector.index
    doc = word_vector.doc

    text = doc[:ind].text_with_ws + '*' + doc[ind] + '*'
    if ind + 1 < len(doc):
        text += doc[ind + 1:].text_with_ws
    return text


def get_nearest_word(text):
    text_split = text.split('*')
    ind = len(text_split[0]) + 1

    doc = nlp(''.join(text_split))
    token_ind = get_token_for_char(doc, ind)
    doc = nlp(text)

    closest_words_syntax = get_closest_word_demo(words_reprs, doc, token_ind, embedder, extractor=extractor, k=5,
                                                 method='l2')
    closest_str_syntax = [word_vector_to_text(x) for x in closest_words_syntax]

    closest_word_baseline = get_closest_sentence_demo(cca_word_reprs, doc, embedder, extractor=None, k=5, method='l2')
    closest_str_baseline = [word_vector_to_text(x) for x in closest_word_baseline]

    return {'syntax': '<br/>'.join(closest_str_syntax), 'baseline': '<br/>'.join(closest_str_baseline)}


@app.route('/syntax_extractor/', methods=['GET'])
@cross_origin()
def serve():
    text = request.args.get('text')
    logger.info('request: ' + text)

    if text.strip() == '':
        return ''

    # try:
    # doc = nlp(text)

    if bool(request.args.get('sentence_based')):
        nearest = get_nearest_sentence(text)
    else:
        nearest = get_nearest_word(text)

    logger.info('ans: ' + str(nearest))
    html = nearest

    # except Exception as e:
    #    logger.info('error. ' + str(e))
    #    html = 'some error occurred while trying to find the NFH'

    return html
