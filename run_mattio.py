from hybrid import *
from Data_Handler.DataReader import DataReader
from Data_manager.split_functions.split_train_validation_random_holdout import split_train_in_two_percentage_global_sample
from tqdm import tqdm
from evaluator import evaluate
from HyperparameterTuning.run_hyperparameter_search import runHyperparameterSearch_Collaborative
from Recommenders.SLIM.SLIMElasticNetRecommender import SLIMElasticNetRecommender
from Recommenders.KNN.ItemKNNCFRecommender import ItemKNNCFRecommender
from Recommenders.GraphBased.RP3betaRecommender import RP3betaRecommender
from Recommenders.GraphBased.P3alphaRecommender import P3alphaRecommender
from Recommenders.EASE_R.EASE_R_Recommender import EASE_R_Recommender
from Recommenders.KNN.UserKNN_CFCBF_Hybrid_Recommender import UserKNN_CFCBF_Hybrid_Recommender
from Recommenders.KNN.UserKNNCBFRecommender import UserKNNCBFRecommender
from Recommenders.KNN.ItemKNNCBFRecommender import ItemKNNCBFRecommender

from Evaluation.Evaluator import EvaluatorHoldout
from Recommenders.DataIO import DataIO
from HyperparameterTuning.SearchBayesianSkopt import SearchBayesianSkopt
from HyperparameterTuning.SearchAbstractClass import SearchInputRecommenderArgs
from skopt.space import Real, Integer, Categorical
import os


############################# READ & SPLIT DATA ##############################
dataReader = DataReader()

target = dataReader.load_target()

URM = dataReader.load_augmented_binary_urm()
URM_aug, ICM = dataReader.pad_with_zeros_ICMandURM(URM)

URM_train_aug, URM_validation = split_train_in_two_percentage_global_sample(
    URM_aug, train_percentage=0.9)
URM_train_pow = dataReader.stackMatrixes(URM_train_aug)
UCM = dataReader.load_aug_ucm()


evaluator_validation = EvaluatorHoldout(URM_validation, [10])


############################## FITTING ##########################################################

#UserKNNCB_Hybrid = UserKNN_CFCBF_Hybrid_Recommender(URM_train_aug,UCM)
#UserKNNCB_Hybrid.fit(UCM_weight = 0.030666039949562303, topK = 374, shrink = 44, normalize = True)


UserKNNCF = UserKNNCFRecommender(URM_train_aug)
UserKNNCF.fit()


RP3beta_aug = RP3betaRecommender(URM_train_aug)
RP3beta_aug.fit()


S_SLIM = SLIMElasticNetRecommender(URM_train_pow)
S_SLIM.fit()

EASE_R = EASE_R_Recommender(URM_train_aug)
EASE_R.fit()


##########################################################################################################

Hybrid_SSLIM_RP3B_aug = Hybrid_SSLIM_RP3B_aug(
    URM_train_aug, S_SLIM, RP3beta_aug)
Hybrid_SSLIM_RP3B_aug.fit(alpha = 0.7447123958484749)

Hybrid_006022 = Hybrid_006022(URM_train_aug, URM_train_pow, ICM, UCM, Hybrid_SSLIM_RP3B_aug, UserKNNCF, EASE_R)
Hybrid_006022.fit(Hybrid_1_tier1_weight= 0.4730071105820606, Hybrid_2_tier1_weight= 1.0, Hybrid_1_tier2_weight= 1.0, Hybrid_2_tier2_weight= 1.0, Hybrid_1_tier3_weight=1.0, Hybrid_2_tier3_weight=  0.0)

##########################################################################################################

recommender = Linear_Hybrid(URM_train_aug, Hybrid_006022, EASE_R)
recommender.fit(norm = 2, alpha = 0.8391405305123323)

########################## CREATE CSV FOR SUBMISISON ##########################
f = open("submission.csv", "w+")
f.write("user_id,item_list\n")
recommended_items_for_each_user = {}
for user_id in tqdm(target):
    recommended_items = recommender.recommend(
        user_id, cutoff=10, remove_seen_flag=True)
    # recommended_items=impressions.update_ranking(user_id,recommended_items,dataReader)
    recommended_items_for_each_user[int(user_id)] = recommended_items
    well_formatted = " ".join([str(x) for x in recommended_items])
    f.write(f"{user_id}, {well_formatted}\n")

# Evaluate recommended items
map = evaluate(recommended_items_for_each_user, URM_validation, target)
print('MAP score: {}'.format(map))

