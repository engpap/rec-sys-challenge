# Import recommenders
from Recommenders.KNN.ItemKNNCFRecommender import ItemKNNCFRecommender
from Recommenders.BaseRecommender import BaseRecommender
from Recommenders.SLIM.SLIMElasticNetRecommender import *
from Recommenders.SLIM.Cython.SLIM_BPR_Cython import SLIM_BPR_Cython

# Import libraries
from tqdm import tqdm
import numpy as np
from numpy import linalg as LA


class HybridRecommender(BaseRecommender):

    RECOMMENDER_NAME = "Hybrid_Recommender"

    def __init__(self, URM_train):
        super(HybridRecommender, self).__init__(URM_train)

    def fit(self):
        #self.ItemCF = ItemKNNCFRecommender(self.URM_train)
        #self.ItemCF.fit(10, 2000)
        self.SLIM_ElasticNet = SLIMElasticNetRecommender(self.URM_train)
        #self.SLIM_BPR_Cython = SLIM_BPR_Cython(self.URM_train)
        #self.ItemCF.fit(10, 2000)
        self.SLIM_ElasticNet.fit(l1_ratio=0.08265567841287592, alpha = 0.003054760282977481, positive_only=True, topK = 586) #orginal topk was 183
        #self.SLIM_BPR_Cython.fit(topK=200)

    def _compute_item_score(self, user_id_array, items_to_compute=None):

        num_items = 24507
        #num_items = 27968 # with powerful_urm
        item_weights = np.empty([len(user_id_array), num_items])

        for i in tqdm(range(len(user_id_array))):
            '''
            w1 = self.ItemCF._compute_item_score(user_id_array[i], items_to_compute)
            w1 /= LA.norm(w1, 2)
            w2 = self.SLIM_ElasticNet._compute_item_score(user_id_array[i], items_to_compute)
            w2 /= LA.norm(w2, 2)
            w = w1 + w2 
            '''
            #w = self.ItemCF._compute_item_score(user_id_array[i], items_to_compute)
            w = self.SLIM_ElasticNet._compute_item_score(user_id_array[i], items_to_compute)
            #w = self.SLIM_BPR_Cython._compute_item_score(user_id_array[i], items_to_compute)

            # In the i-th array of item_weights we assign the w array
            item_weights[i, :] = w

        return item_weights
