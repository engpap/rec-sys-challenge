from Data_Handler.DataReader import DataReader
from Data_manager.split_functions.split_train_validation_random_holdout import split_train_in_two_percentage_global_sample
from hybrid import HybridRecommender
from Recommenders.SLIM.SLIMElasticNetRecommender import SLIMElasticNetRecommender
from tqdm import tqdm
from evaluator import evaluate
from Evaluation.Evaluator import EvaluatorHoldout

# Read & split data
dataReader = DataReader()
#urm = dataReader.load_urm()
#urm = dataReader.load_binary_urm()
#urm = dataReader.load_augmented_binary_urm()
#urm_df=dataReader.load_powerful_binary_urm_df()
#urm = dataReader.load_powerful_binary_urm()
urm = dataReader.load_augmented_binary_urm_less_items()
target = dataReader.load_target()
# dataReader.print_statistics(target)

'''
URM_train, URM_test = split_train_in_two_percentage_global_sample(urm, train_percentage = 0.8)
URM_train, URM_validation = split_train_in_two_percentage_global_sample(URM_train, train_percentage = 0.8)
'''

URM_train, URM_validation = split_train_in_two_percentage_global_sample(
    urm, train_percentage=0.9)


# Instantiate and fit hybrid recommender
recommender = SLIMElasticNetRecommender(URM_train)
recommender.fit(l1_ratio = 0.05220125019731136, alpha = 0.0013922898354140408, positive_only=True, topK = 245)

# evaluator=EvaluatorHoldout(URM_train)
# evaluator.evaluateRecommender(recommender)

# Create CSV for submission
f = open("submission.csv", "w+")
f.write("user_id,item_list\n")
recommended_items_for_each_user = {}
for user_id in tqdm(target):
    recommended_items = recommender.recommend(user_id, cutoff=10, remove_seen_flag=True)
    recommended_items_for_each_user[int(user_id)] = recommended_items
    well_formatted = " ".join([str(x) for x in recommended_items])
    f.write(f"{user_id}, {well_formatted}\n")

'''
map=evaluate(recommended_items_for_each_user,URM_test,target)
'''

map = evaluate(recommended_items_for_each_user, URM_validation, target)
# evaluator.evaluateRecommender(recommender)
print('MAP score: {}'.format(map))
