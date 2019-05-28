import numpy as np
import torch
import torch.optim as optim
from allennlp.common.file_utils import cached_path
from allennlp.data.iterators import BasicIterator
from allennlp.data.vocabulary import Vocabulary
from allennlp.modules.feedforward import FeedForward
from allennlp.nn.activations import Activation
from allennlp.modules.seq2seq_encoders import PytorchSeq2SeqWrapper
from allennlp.modules.text_field_embedders import BasicTextFieldEmbedder
from allennlp.modules.token_embedders import Embedding
from allennlp.predictors import SentenceTaggerPredictor
from allennlp.training.trainer import Trainer
from allennlp.modules.matrix_attention.bilinear_matrix_attention import BilinearMatrixAttention
from framework.dataset_readers.data_reader import DataReader
# from framework.dataset_readers.nfh_reader_number_detector import NFHReader
# from framework.dataset_readers.nfh_reader_imp_ref_bin import NFHReader
# from framework.dataset_readers.hiding_anchor import NFHReader
# from framework.models.model_base import NfhDetector
# from framework.models.model_anch_dropout import NfhDetector
from framework.models.siamese_norm import SiameseModel
# from framework.models.model_nalu import NfhDetectorNalu
# from framework.models.model_imp_ref_bin import NfhDetector
# from framework.models.model_number_detector import NfhDetector
# from framework.models.model_missing_representation import NfhDetector
# from framework.models.model_self_attention import NfhDetector
# from framework.models.model_rank_loss import NfhDetector
# from framework.models.hidden_anchor_model import NfhDetector

torch.manual_seed(1)


reader = DataReader()
# augmented
# sample
dir_path = '/home/lazary/workspace/thesis/tree-extractor/data/'
train_dataset = reader.read(cached_path(dir_path + 'small_train'))
validation_dataset = reader.read(cached_path(dir_path + 'small_dev'))
vocab = Vocabulary.from_instances(train_dataset + validation_dataset)
EMBEDDING_DIM = 6
HIDDEN_DIM = 6
scorer = FeedForward(1024, num_layers=2,
                                  hidden_dims=[150, 2], activations=[Activation.by_name('tanh')(),
                                                                     Activation.by_name('linear')()],
                                  dropout=0.2)
representer = FeedForward(1024, num_layers=2,
                                  hidden_dims=[512, 1024], activations=[Activation.by_name('tanh')(),
                                                                     Activation.by_name('linear')()],
                                  dropout=0.2)
model = SiameseModel(representer)

optimizer = optim.Adam(model.parameters(), lr=0.0001)
iterator = BasicIterator(batch_size=2)
iterator.index_with(vocab)
trainer = Trainer(model=model,
                  optimizer=optimizer,
                  iterator=iterator,
                  train_dataset=train_dataset,
                  validation_dataset=validation_dataset,
                  patience=10,
                  num_epochs=1000)
trainer.train()
# predictor = SentenceTaggerPredictor(model, dataset_reader=reader)
# tag_logits = predictor.predict("The dog ate the apple")['tag_logits']
# tag_ids = np.argmax(tag_logits, axis=-1)
# print([model.vocab.get_token_from_index(i, 'label') for i in tag_ids])
# Here's how to save the model.
# with open("/tmp/model.th", 'wb') as f:
#     torch.save(model.state_dict(), f)
# vocab.save_to_files("/tmp/vocabulary")
# # And here's how to reload the model.
# vocab2 = Vocabulary.from_files("/tmp/vocabulary")
# model2 = LstmTagger(word_embeddings, lstm, vocab2)
# with open("/tmp/model.th", 'rb') as f:
#     model2.load_state_dict(torch.load(f))
# predictor2 = SentenceTaggerPredictor(model2, dataset_readers=reader)
# tag_logits2 = predictor2.predict("The dog ate the apple")['tag_logits']
# assert tag_logits2 == tag_logits