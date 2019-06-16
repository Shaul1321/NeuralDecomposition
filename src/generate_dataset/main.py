import generators
import argparse
import model
from model_runner import ModelRunner
import pickle

pos_tags_to_replace = ["NN", "NNS", "NNP", "NNPS", "PRP$", "JJ", "CD", "VB", "VBD", "VBG", "VBN",
                       "VBP", "VBZ"]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Equivalent sentences generator',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--input-wiki', dest='input_wiki', type=str,
                        default='../data/external/wikipedia.sample.tokenized',
                        help='name of the source wikipedia text file')
    parser.add_argument('--w2v-file', dest='w2v_file', type=str,
                        default='../data/external/GoogleNews-vectors-negative300.bin',
                        help='name of the source wikipedia text file')
    parser.add_argument('--output-data', dest='output_data', type=str,
                        default='../data/interim/emb_data.txt',
                        help='name of the output file')
    parser.add_argument('--output-sentences', dest='output_sentences', type=str,
                        default='../data/interim/emb_sents.pickle',
                        help='name of the output file')
    parser.add_argument('--pos-tags-to-replace', dest='pos_tags_to_replace', type=list,
                        default=pos_tags_to_replace, help='which POS tags to replace')
    parser.add_argument('--pos2words-file', dest='pos2words_file', type=str,
                        default='../data/external/pos2words.pickle',
                        help='name of the output file')
    parser.add_argument('--num-sentences', dest='num_sentences', type=int, default=20,
                        help='Number of equivalent sentences to generate from each sentence.')
    parser.add_argument('--substitutions-type', dest='substitution_type', type=str,
                        default='embeddings')
    parser.add_argument('--substitutions-file', dest='substitution_file', type=str,
                        default='')
    parser.add_argument('--cuda-device', dest='cuda_device', type=int, default=0,
                        help='cuda device to run the LM on')

    args = parser.parse_args()

    # If no substitution file is provided, need to build these
    if args.substitution_file == '':

        # Reading the type of substitution technique
        if args.substitution_type == 'embeddings':
            generator = generators.EmbeddingBasedGenerator(args.input_wiki, args.output_sentences,
                                                           args.num_sentences,
                                                           args.w2v_file, 12)
        else:  # if args.substitution_type == 'pos'
            generator = generators.POSBasedEGenerator(args.input_wiki, args.output_sentences,
                                                      args.pos_tags_to_replace, args.num_sentences,
                                                      args.pos2words_file)

        equivalent_sentences = generator.generate()
    # otherwise, reading that file
    else:
        with open(args.substitution_file, "rb") as f:
            equivalent_sentences = pickle.load(f)

    model = model.Elmo('../data/external/elmo_2x4096_512_2048cnn_2xhighway_options.json',
                       '../data/external/elmo_2x4096_512_2048cnn_2xhighway_weights.hdf5',
                       args.cuda_device)
    model_runner = ModelRunner(model, equivalent_sentences, args.output_data, persist=True)
    model_runner.run()
