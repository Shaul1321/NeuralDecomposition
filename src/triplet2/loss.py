import torch
import numpy as np
import copy
import torch.nn.functional as F
from torch import nn
import random

class HardNegativeSampler(object):

    def __init__(self, k = 5):

        self.k = k

    def _get_mask(self, labels, positive = True):

        diffs =  labels[None, :] - (labels[None, :]).T

        if positive:

            mask = diffs == 0

        else:

            mask = diffs != 0

        if positive:
            mask[range(len(mask)), range(len(mask))] = 0
        return mask

    def get_distances(self, labels, dists):

        mask_anchor_positive = self._get_mask(labels, positive = True)
        mask_anchor_negative = self._get_mask(labels, positive = False)
        anchor_positive_dist = mask_anchor_positive * dists
        hardest_positive_idx = np.argmax(anchor_positive_dist, axis=1)
        max_anchor_negative_dist = np.max(dists, axis=1, keepdims=True)

        anchor_negative_dist = dists + max_anchor_negative_dist * (1 - mask_anchor_negative)
        k = int(np.random.choice(range(1, self.k + 1)))
        hardest_negatives_idx = np.argpartition(anchor_negative_dist, k, axis = 1)[:,k]

        return hardest_positive_idx, hardest_negatives_idx


def pairwise_distances(x, y=None):
    '''
    Input: x is a Nxd matrix
           y is an optional Mxd matirx
    Output: dist is a NxM matrix where dist[i,j] is the square norm between x[i,:] and y[j,:]
            if y is not given then use 'y=x'.
    i.e. dist[i,j] = ||x[i,:]-y[j,:]||^2
    '''
    x_norm = (x ** 2).sum(1).view(-1, 1)
    if y is not None:
        y_t = torch.transpose(y, 0, 1)
        y_norm = (y ** 2).sum(1).view(1, -1)
    else:
        y_t = torch.transpose(x, 0, 1)
        y_norm = x_norm.view(1, -1)

    dist = x_norm + y_norm - 2.0 * torch.mm(x, y_t)
    # Ensure diagonal is zero if x=y
    # if y is None:
    #     dist = dist - torch.diag(dist.diag)
    dist[dist != dist] = 0  # replace nan values with 0
    return torch.clamp(dist, 0.0, np.inf)



class BatchHardTripletLoss2(torch.nn.Module):

    def __init__(self, p = 2, alpha = 0.1, normalize = False, mode = "euc", final = "softplus", k = 5):

        super(BatchHardTripletLoss2, self).__init__()
        self.p = p
        self.alpha = alpha
        self.normalize = normalize
        self.mode = mode
        self.final = final
        self.sampler = HardNegativeSampler(k = k)
        self.k = k

    def get_mask(self, labels, positive = True):

        diffs =  labels[None, :] - torch.t(labels[None, :])

        if positive:

            mask = diffs == 0

        else:

            mask = diffs != 0

        if positive:
            mask[range(len(mask)), range(len(mask))] = 0
        return mask

    def forward(self, h1, h2, sent1, sent2, index, evaluation = False):

        if self.normalize or self.mode == "cosine":

            h1 = h1 / torch.norm(h1, dim = 1, p = self.p, keepdim = True)
            h2 = h2 / torch.norm(h2, dim = 1, p = self.p, keepdim = True)

        sent1, sent2 = np.array(sent1, dtype = object), np.array(sent2, dtype = object)
        labels = torch.arange(0, h1.shape[0])#.cuda()
        labels = torch.cat((labels, labels), dim = 0)
        batch = torch.cat((h1, h2), dim = 0)

        sents = np.concatenate((sent1, sent2), axis = 0)

        if self.mode == "euc":
            #dists = torch.norm((batch[:, None, :] - batch), dim = 2, p = self.p)
            dists = pairwise_distances(batch)
        elif self.mode == "cosine":
            dists = 1. - batch @ torch.t(batch)

        dists = torch.clamp(dists, min = 1e-7)

        try:

            hardest_positive_idx, hardest_negatives_idx = self.sampler.get_distances(labels.detach().cpu().numpy(), dists.detach().cpu().numpy())
            hardest_positive_idx, hardest_negatives_idx = torch.tensor(hardest_positive_idx).cuda(), torch.tensor(hardest_negatives_idx).cuda()

            hardest_negative_dist = dists.gather(1, hardest_negatives_idx.view(-1,1))
            hardest_positive_dist = dists.gather(1, hardest_positive_idx.view(-1,1))


            if evaluation and index == 0:

                hardest_negative_indices = hardest_negatives_idx.detach().cpu().numpy().squeeze()
                neg_sents = sents[hardest_negative_indices]
                with open("negatives.txt", "w") as f:
                    for (anchor_sent, hard_sent) in zip(sents, neg_sents):
                        f.write(anchor_sent + "\n")
                        f.write("-----------------------------------------\n")
                        f.write(hard_sent + "\n")
                        f.write("==========================================================\n")
        except Exception as e:
                print(e)
                print(self.k)
                print(h1.shape, h2.shape)
                print(labels.shape)
                print(batch.shape)
                print(dists.shape)
                print(mask_anchor_positive.shape)
                print(mask_anchor_negative.shape)
                print(anchor_positive_dist.shape)
                print(anchor_negative_dist.shape)
                exit()
        differences = hardest_positive_dist - hardest_negative_dist

        if self.final == "plus":
            triplet_loss = torch.max(differences + self.alpha, torch.zeros_like(differences))
        elif self.final == "softplus":
            triplet_loss = F.softplus(differences, beta = 3)
        elif self.final == "softmax":
            temp = 5 if self.mode != "cosine" else 1
            z = torch.max(hardest_positive_dist, hardest_negative_dist)
            pos = torch.exp((hardest_positive_dist - z)/temp)
            neg = torch.exp((hardest_negative_dist - z)/temp)
            triplet_loss = (pos / (pos + neg))**2
        else:
            triplet_loss = hardest_positive_dist - hardest_negative_dist

        relevant = triplet_loss[triplet_loss > 1e-5]
        good = (hardest_positive_dist < hardest_negative_dist).sum() #(triplet_loss < 1e-5).sum()
        bad = batch.shape[0] - good
        mean_norm_squared = torch.mean(torch.norm(batch, dim = 1)**2)

        return torch.mean(relevant), torch.mean(differences), good, bad, torch.sqrt(mean_norm_squared)









if __name__ == '__main__':

    pass