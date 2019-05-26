import generator
import argparse

from utils import DEFAULT_PARAMS

if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='Equivalent sentences generator',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('--filename', dest='file_name', type=str, default=DEFAULT_PARAMS["file_name"],
                        help='name of the source text file')
	parser.add_argument('--pos-tags-to-replace', dest='pos_tags_to_replace', type=str, default=DEFAULT_PARAMS["pos_tags_to_replace"], help='which POS tags to replace')
	parser.add_argument('-num-sentences', dest='num_sentences', type=int, default=DEFAULT_PARAMS["num_sentences"], help='Number of equivalent sentences to generate from each sentence.')
	args = parser.parse_args()

	pos_generator = generator.POSBasedEGenerator(args.file_name, args.pos_tags_to_replace, args.num_sentences)
	pos_generator.generate()
