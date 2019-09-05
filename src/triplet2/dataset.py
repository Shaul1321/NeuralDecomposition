from torch.utils import data
import numpy as np
import torch
import pickle
import h5py


CUDA = False

class PadCollate:
    """
    a variant of callate_fn that pads according to the longest sequence in
    a batch of sequences
    """

    def __init__(self):

        pass

    def pad_collate(self, batch_data):
        """
        args:
            batch_data - list of (x: tensor, y: tensor, x_str: str, y_str: str, length: int)

        """
        X, Y, X_str, Y_str, lengths, sent_ids = list(zip(*batch_data))
        print(type(X))
        exit()
        X = X[:, :28]
        Y = Y[:, :28]
        lengths = torch.LongTensor(lengths)
        sent_ids = torch.LongTensor(sent_ids)

        if CUDA:
            lengths, sent_ids = lengths.cuda(), sent_ids.cuda()

        X_padded = torch.nn.utils.rnn.pad_sequence(X, batch_first = True)
        Y_padded = torch.nn.utils.rnn.pad_sequence(Y, batch_first = True)

        return (X_padded, Y_padded, np.array(X_str), np.array(Y_str), lengths, sent_ids)
        return {"X": X_padded, "Y": Y_padded, "X_str": X_str, "Y_str": Y_str, "lengths": lengths}

    def __call__(self, batch):
        return self.pad_collate(batch)




class Dataset(data.Dataset):
    def __init__(self, data_path):

        with open(data_path, "rb") as f:

            self.data = pickle.load(f)

        print("Dataset set size is {}".format(len(self.data)))


    def __len__(self):

        return len(self.data)

    def __getitem__(self, index):

        with torch.no_grad():

            instance = self.data[index]

            sent1_vecs, sent2_vecs = instance["vecs"]
            x,y = torch.from_numpy(sent1_vecs).float(), torch.from_numpy(sent2_vecs).float()
            if CUDA:
                x,y = x.cuda(), y.cuda()
            x_sent, y_sent = instance["sent1"], instance["sent2"]
            length = instance["sent_length"]
            sent_id = instance["sent_id"]

            return (x,y,x_sent,y_sent, length, sent_id)

if __name__ == '__main__':

    dataset = Dataset("sample.hdf5")
    for i in range(1000):
        dataset[i]
        print(i)