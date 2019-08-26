#!/usr/bin/python
# -*- coding: utf-8 -*-

from syntactic_extractor import SyntacticExtractor
from allennlp.commands.elmo import ElmoEmbedder
from typing import List, Tuple, Dict
import copy
import numpy as np
import random
from pytorch_pretrained_bert.modeling import BertConfig, BertModel

from allennlp.common.testing import ModelTestCase
from allennlp.data.dataset import Batch
from allennlp.data.fields import TextField, ListField
from allennlp.data.instance import Instance
from allennlp.data.token_indexers.wordpiece_indexer import PretrainedBertIndexer
from allennlp.data.tokenizers import WordTokenizer, Token
from allennlp.data.tokenizers.word_splitter import BertBasicWordSplitter
from allennlp.data.vocabulary import Vocabulary
from allennlp.modules.token_embedders.bert_token_embedder import BertEmbedder

random.seed(0)
from collections import Counter, defaultdict
from tqdm.auto import tqdm


class Embedder(object):
    def __init__(self, wiki_path: str, num_sents: int, params: Dict, device: int=0):
        self._sentences = self._load_sents(wiki_path, num_sents)
        self._devide = device

    def _load_sents(self, wiki_path, num_sents, max_length=35) -> List[List[str]]:

        print("Loading sentences...")

        with open(wiki_path, "r", encoding="utf8") as f:
            lines = f.readlines()
            lines = [line.strip().split(" ") for line in lines]

        if max_length is not None:
            lines = list(filter(lambda sentence: len(sentence) < max_length, lines))

        lines = lines[:num_sents]

        return lines

    def _embedder(self, sentence: List[str]) -> np.ndarray:
        raise NotImplementedError()

    def get_data(self) -> List[Tuple[List[np.ndarray], str]]:
        embeddings_and_sents = self._run_embedder(self._sentences)
        return embeddings_and_sents

    def _run_embedder(self, sentences: List[List[str]]) -> List[Tuple[List[np.ndarray], str]]:
        raise NotImplementedError()


class EmbedElmo(Embedder):

    def __init__(self, wiki_path: str, num_sents: int, params: Dict, device=0):

        Embedder.__init__(self, wiki_path, num_sents, {}, device)
        elmo_options_path = params['elmo_options_path']
        elmo_weights_path = params['elmo_weights_path']
        self.embedder = self._load_elmo(elmo_weights_path, elmo_options_path, device=device)

    def _load_elmo(self, elmo_weights_path, elmo_options_path, device=0):

        print("Loading ELMO...")
        return ElmoEmbedder(elmo_options_path, elmo_weights_path, cuda_device=device)

    def _run_embedder(self, sentences: List[List[str]]) -> List[Tuple[List[np.ndarray], str]]:

        print("Running ELMO...")

        elmo_embeddings = []

        for sent in tqdm(sentences, ascii=True):
            elmo_embeddings.append((self.embedder.embed_sentence(sent), sent))

        all_embeddings = []

        for (sent_emn, sent_str) in elmo_embeddings:
            last_layer = sent_emn[-1, :, :]
            second_layer = sent_emn[-2, :, :]
            concatenated = np.concatenate([second_layer, last_layer], axis=1)
            all_embeddings.append((concatenated, sent_str))

        return all_embeddings

    def _embedder(self, sentence):
        return self._embedder(sentence)


class EmbedBert(Embedder):
    def __init__(self, wiki_path: str, num_sents: int, params: Dict, device=0):

        Embedder.__init__(self, wiki_path, num_sents, params, device)
        config = BertConfig(vocab_size_or_config_json_file=30522)
        bert_model = BertModel(config)

        bert_name = 'bert-base-uncased'
        self.token_indexer = PretrainedBertIndexer(pretrained_model=bert_name, use_starting_offsets=True)
        self.vocab = Vocabulary()
        self.embedder = BertEmbedder(bert_model, top_layer_only=True)

    def _run_embedder(self, sentences: List[List[str]]) -> List[Tuple[List[np.ndarray], str]]:
        print("Running Bert...")

        bert_embeddings = []

        for sent in tqdm(sentences, ascii=True):
            bert_embeddings.append((self._embedder(sent), sent))

        return bert_embeddings


    def _embedder(self, sentence: List[str]) -> np.ndarray:
        toks = [Token(w) for w in sentence]

        instance = Instance({"tokens": TextField(toks, {"bert": self.token_indexer})})

        batch = Batch([instance])
        batch.index_instances(self.vocab)

        padding_lengths = batch.get_padding_lengths()
        tensor_dict = batch.as_tensor_dict(padding_lengths)
        tokens = tensor_dict["tokens"]

        bert_vectors = self.embedder(tokens["bert"], offsets=tokens["bert-offsets"])
        return bert_vectors.data.numpy()[0]