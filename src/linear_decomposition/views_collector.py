import h5py
import typing
from typing import Dict, Tuple, List
import numpy as np
import tqdm
import pickle

Equivalent_sentences_group = typing.NamedTuple("equivalent_sentences",
                                    [('vecs', np.ndarray), ('sents', List[List[str]]),
                                     ("content_indices", List[int])])
                                     
class CollectorBase(object):

        def __init__(self, path, view_size, output_filename, exclude_function_words = True):
        
                """
                Parameters
                -------------------------
                Path: str, required.
                      The path to the dataset that contain equivalent sentences.
                      The file is HDF5 format. Each group (listed by a string index) is one set of equivalent sentences, and contains datasets "vecs" (ELMO representations of the words), "sents" and "content indices" (indices of content words)
                     (The foramt is described above in 'Equivalent_sentences_group'")
                """
        
                self.path = path
                self.f = h5py.File(path, 'r')
                self.view_size = view_size
                self.output_filename = output_filename
                self.exclude_function_words = exclude_function_words
        
        def read_one_group(equivalent_sentences: Equivalent_sentences_group) -> List[Tuple[np.ndarray, np.ndarray, int]]:
        
                """
                Parameters
                -----------------------
                equivalent_sentences: Equivalent_sentences_group, requiered.
                ----------------------
                Return
                        A list of tuples extracted from this group.
                        each tuples contains (view1_instance, view2_instance, index_in_the_sentence)
                """
        
                raise NotImplementedError
        
        def collect_views(self):
        
                pbar = tqdm.tqdm(total = self.view_size)
                views = []
                i = 0
                
                print("Collecting views...")
                
                while len(views) < self.view_size:
               
                        group = self.f[str(i)] # group has the same interface as Equivalent_sentences_group
                        vecs, sents, content_idx = group["vecs"], group["sents"], group["content_indices"] 
                        group_size, sent_len = group.attrs["group_size"], group.attrs["sent_length"]
                        group_data = self.read_one_group(vecs, sents, content_idx, sent_len, group_size)
                        views.extend(group_data)
                        pbar.update(1)
                        i += 1
               
                print("Collected {} instances from {} sentences".format(len(views), i))
                
                with open("output_filename", "wb") as f:
                
                        pickle.dump(views, f)
                
        def close_file(self):
        
                self.f.close()





class SimpleCollector(CollectorBase):

        def __init__(self, path, view_size, output_filename, exclude_function_words=True):
        
        
                super(SimpleCollector, self).__init__(path, view_size, output_filename, exclude_function_words)
                
        def read_one_group(self, vecs: np.ndarray, sents: np.ndarray, content_idx: np.ndarray, sent_len: int, group_size: int) -> List[Tuple[np.ndarray, np.ndarray, int]]:
                                
                view1 = vecs[::1,:, :]  #(num sents/2+-1, num_indices, 2048)
                view2 = vecs[1::1,:, :] # (num_sents/2+-1, num_indices, 2048)
                view1_words = sents[::1,:] #(num_sents/2+-1, sent_length)
                view2_words = sents[1::1,:] # (num_sents/2+-1, sent_length
                
                data = []
                
                for word_index in range(sent_len):
                
                        if word_index not in content_idx: continue
                        
                        view1_vecs = view1[:, word_index, :]
                        view2_vecs = view2[:, word_index, :]
                        view1_words_at_index = view1_words[:, word_index]
                        view2_words_at_index = view2_words[:, word_index]
                        idx = [word_index] * min(view1_vecs.shape[0], view2_vecs.shape[0])
                        examples = list(zip(view1_vecs, view2_vecs, view1_words_at_index, view2_words_at_index, idx))
                        data.extend(examples)
                
                return data
                      
                                
                      
        
        
        
        
        
class AveragedCollector(CollectorBase):

        def __init__(self, path, view_size, output_filename, exclude_function_words=True):
        
        
                super(AveragedCollector, self).__init__(path, view_size, output_filename, exclude_function_words)
                
        def read_one_group(self, vecs: np.ndarray, sents: np.ndarray, content_idx: np.ndarray, sent_len: int, group_size: int) -> List[Tuple[np.ndarray, np.ndarray, int]]:
                                
                view1 = vecs[::1,:, :]  #(num sents/2+-1, num_indices, 2048)
                view2 = vecs[1::1,:, :] # (num_sents/2+-1, num_indices, 2048)
                view1_words = sents[::1,:] #(num_sents/2+-1, sent_length)
                view2_words = sents[1::1,:] # (num_sents/2+-1, sent_length
                
                data = []
                
                for word_index in range(sent_len):
                
                        if word_index not in content_idx: continue
                        
                        view1_vecs = view1[:, word_index, :]
                        view2_vecs = view2[:, word_index, :]
                        
                        m1 = np.mean(view1_vecs, axis = 0)[None, :]
                        m2 = np.mean(view2_vecs, axis = 0)[None, :]

                        data.append((m1, m2, word_index))
                
                return data
                               
        
        
        
        
        
        
        
                
               