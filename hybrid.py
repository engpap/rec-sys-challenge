# Import recommenders
from Recommenders.BaseRecommender import BaseRecommender
from Recommenders.KNN.ItemKNNCFRecommender import ItemKNNCFRecommender
from Recommenders.KNN.UserKNNCFRecommender import UserKNNCFRecommender
from Recommenders.SLIM.SLIMElasticNetRecommender import *
from Recommenders.GraphBased.RP3betaRecommender import RP3betaRecommender
from Recommenders.KNN.ItemKNNCFRecommender import ItemKNNCFRecommender
#from Recommenders.FactorizationMachines.LightFMRecommender import LightFMItemHybridRecommender
from Data_Handler.DataReader import DataReader


# Import libraries
from tqdm import tqdm
import numpy as np
from numpy import linalg as LA
import scipy.sparse as sp
import pandas as pd


class HybridRecommender(BaseRecommender):

    RECOMMENDER_NAME = "Hybrid_Recommender"

    def __init__(self, URM_train, ICM, dataReader):
        self.URM_train_aug = URM_train
        self.ICM = ICM
        #self.URM_train_pow = self.stackMatrixes(dataReader, URM_train)
        # URM_train_aug_df=dataReader.csr_to_dataframe(URM_train)
        # self.URM_train_pow=dataReader.load_powerful_binary_urm_given_URM_train_df(URM_train_aug_df)

        super(HybridRecommender, self).__init__(URM_train)

    def fit(self):
        # Stack and normalize URM and ICM
        #URM_stacked = sps.vstack([self.URM_train, self.ICM.T])

        # Instantiate & fit the recommenders
        #self.ItemCF = ItemKNNCFRecommender(self.URM_train_pow)
        #self.ItemCF.fit(topK=1199, shrink=229.22107382005083,similarity='cosine', normalize=True, feature_weighting="TF-IDF")

        #self.SLIM_ElasticNet = SLIMElasticNetRecommender(self.URM_train)
        #self.SLIM_ElasticNet.fit(l1_ratio=0.008213119901673099,alpha=0.0046000272149077145, positive_only=True, topK=498)

        # self.LightFMItemHybridRecommender = LightFMItemHybridRecommender(self.URM_train, self.ICM)
        # self.LightFMItemHybridRecommender.fit(epochs = 10)

        self.RP3beta = RP3betaRecommender(self.URM_train_aug)
        self.RP3beta.fit(alpha=0.2686781702308662, beta=0.39113126168484014, topK=455, normalize_similarity=True)

    def _compute_item_score(self, user_id_array, items_to_compute=None):
        
        num_items = 24507
        # num_items = 27968
        # num_items=19630
        # num_items = len(self.items) # num_items changes based on used urm
        item_weights = np.empty([len(user_id_array), num_items])

        for i in tqdm(range(len(user_id_array))):

            '''
            w1 = self.ItemCF._compute_item_score(
                user_id_array[i], items_to_compute)
            w1 /= LA.norm(w1, 2)
            w2 = self.SLIM_ElasticNet._compute_item_score(
                user_id_array[i], items_to_compute)
            w2 /= LA.norm(w2, 2)
            w = w1 + w2
            '''

            #w = self.ItemCF._compute_item_score(user_id_array[i], items_to_compute)
            w = self.RP3beta._compute_item_score(user_id_array[i], items_to_compute)
            #w = self.SLIM_ElasticNet._compute_item_score(user_id_array[i], items_to_compute)
            # w = self.SLIM_BPR_Cython._compute_item_score(user_id_array[i], items_to_compute)
            # w = self.LightFMItemHybridRecommender._compute_item_score(user_id_array[i], items_to_compute)

            # In the i-th array of item_weights we assign the w array
            item_weights[i, :] = w

        return item_weights

    

'''-----------------------------------------------------------------------------------------------------------------------------'''


class HybridRecommender_2(BaseRecommender):

    RECOMMENDER_NAME = "Hybrid_Recommender_2"

    N_CONFIG = 0

    def __init__(self, URM_train, ICM):
        """ Constructor of Hybrid_Recommender_2
        Args:
            URM_train (csr): augmented matrix
            ICM (csr): icm
        """
        self.URM_train_aug = URM_train
        self.ICM = ICM
        self.URM_train_pow = DataReader().stackMatrixes(URM_train)
        super(HybridRecommender_2, self).__init__(URM_train)

        self.normalize = None
        self.recommenders = {}
        self.weights = {}

    def fit(self, RP3betaRecommenderWeight=0.5, SLIMElasticNetRecommenderWeight=0.5, normalize=False):
        """ Set the weights for every algorithm involved in the hybrid recommender """

        self.weights = {
            #ItemKNNCFRecommender: ItemKNNCFRecommenderWeight,
            SLIMElasticNetRecommender: SLIMElasticNetRecommenderWeight,
            RP3betaRecommender: RP3betaRecommenderWeight,
        }

        self.normalize = normalize

        for rec_class in self.weights.keys():
            if self.weights[rec_class] > 0.0:
                if rec_class not in self.recommenders:
                    #start = time.time()
                    if rec_class==SLIMElasticNetRecommender:
                        temp_rec = rec_class(self.URM_train_pow)
                    else:
                        temp_rec = rec_class(self.URM_train_aug)
                    temp_rec.fit()
                    self.recommenders[rec_class] = temp_rec
                    #end = time.time()
                    print("Fitted new instance of {}. Employed time: {} seconds".format(rec_class.__name__, end - start))

    def _compute_item_score(self, user_id_array, items_to_compute=None):

        num_items_aug=24507
        num_items_pow=27968
        item_weights = np.empty([len(user_id_array), num_items_pow])

        # w is predicted ratings array of a user
        for i in range(len(user_id_array)):
            for rec_class in self.recommenders.keys():
                if self.weights[rec_class] > 0.0:
                    w = self.recommenders[rec_class]._compute_item_score(user_id_array[i], items_to_compute)
                    if self.normalize:
                        w *= 1.0 / w.max()
                    if rec_class != SLIMElasticNetRecommender:  # since we are using augmented matrix, items are different
                        w=np.pad(w,((0,0),(0,num_items_pow-num_items_aug)))
                    w += np.multiply(w, self.weights[rec_class])
            item_weights[i, :] = w

        return item_weights

'''-----------------------------------------------------------------------------------------------------------------------------'''

class HybridRecommender_3(BaseRecommender):
    
    RECOMMENDER_NAME = "Hybrid_Recommender_3"
    def __init__(self, URM_train: sp.csr_matrix, ICM):
        self.URM_train_aug = URM_train
        self.ICM = ICM
        self.URM_train_pow = DataReader().stackMatrixes(URM_train)
        super(HybridRecommender_3, self).__init__(self.URM_train_pow)
    
    def fit(self):
        self.S_SLIM = SLIMElasticNetRecommender(self.URM_train_pow)
        self.RP3beta = RP3betaRecommender(self.URM_train_aug)
        #self.ItemKNNCF = ItemKNNCFRecommender(self.URM_train_aug)
        self.S_SLIM.fit(l1_ratio=0.007467817120176792,alpha=0.0016779515713674044, positive_only=True, topK=723)
        self.RP3beta.fit(alpha=0.2686781702308662, beta=0.39113126168484014, topK=455, normalize_similarity=True)
        #self.ItemKNNCF.fit(topK=1199, shrink=229.22107382005083,similarity='cosine', normalize=True, feature_weighting="TF-IDF")

    def _compute_item_score(self, user_id_array, items_to_compute=None):
         
        num_items_aug=24507
        num_items_pow=27968
        item_weights = np.empty([len(user_id_array), 27968])

        for i in tqdm(range(len(user_id_array))):

            interactions_aug = len(self.URM_train_aug[user_id_array[i],:].indices)
            '''
            if interactions < 17:
                w = self.ItemKNNCF._compute_item_score(user_id_array[i], items_to_compute) 
                w=np.pad(w,((0,0),(0,num_items_pow-num_items_aug)))
                item_weights[i,:] = w
            '''

            if interactions_aug >= 15 and interactions_aug < 24:
                w = self.RP3beta._compute_item_score(user_id_array[i], items_to_compute) 
                w=np.pad(w,((0,0),(0,num_items_pow-num_items_aug)))
                item_weights[i,:] = w 

            else:
                w = self.S_SLIM._compute_item_score(user_id_array[i], items_to_compute) 
                item_weights[i,:] = w 
            
        return item_weights



    
