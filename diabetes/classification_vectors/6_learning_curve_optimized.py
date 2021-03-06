import datetime
import logging
import os

import dill
import numpy as np
from xgboost.sklearn import XGBClassifier
from sklearn.metrics import log_loss, roc_auc_score

np.random.seed(1)
TRAINING_SAMPLE_SIZES = [10, 50, 100, 250, 500, 750, 1000, 1500, 2000, 3000, 4000]
TRAINING_FOR_EACH_SIZE = 10
MONTHS = 12

DATA_FILE = '../data/final/vectors/vectors_patient2vec_pvdbow_hs_win-30_emb-100.dill'
LOG_FILE = '../log/diabetes_vectors_monthly_optimized_learning_curves.log'
N_JOBS = 30

rand_search = dill.load(open('../log/diabetes_vectors_parameter_monthly_optim_xgb.dill', 'rb'))

# Logging setup
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(message)s')

# Loading data
data = dill.load(open(DATA_FILE, 'rb'))
train_x = data[MONTHS]["TRAIN"]["X"]
train_y = data[MONTHS]["TRAIN"]["y"]
test_x = data[MONTHS]["TEST"]["X"]
test_y = data[MONTHS]["TEST"]["y"]


def draw_samples(number):
    # Generates a balanced dataset of given size from training data
    # (sampling without replacement)
    positive_to_negetive= train_y.sum()/len(train_y)
    positive_no = int(np.floor(positive_to_negetive*number))
    negative_no = number-positive_no
    all_negative_indexes = np.where(train_y == 0)[0]
    all_positive_indexes = np.where(train_y == 1)[0]
    negative_indexes = np.random.choice(all_negative_indexes, size=negative_no,
                                        replace=False)
    positive_indexes = np.random.choice(all_positive_indexes, size=positive_no,
                                        replace=False)
    indexes = np.concatenate((negative_indexes, positive_indexes))
    np.random.shuffle(indexes)
    return train_x[indexes], train_y[indexes]


for training_sample_size in TRAINING_SAMPLE_SIZES:
    for _ in range(TRAINING_FOR_EACH_SIZE):
        sampled_x, sampled_y = draw_samples(training_sample_size)

        best_params = rand_search['vectors_patient2vec_pvdbow_hs_win-30_emb-100.dill'][MONTHS].best_params_
        best_params['random_state'] = 1
        best_params['n_jobs'] = N_JOBS

        clf = XGBClassifier(**best_params)
        clf.fit(sampled_x, sampled_y, verbose=True)
        pred_y = clf.predict_proba(test_x)

        auc_score = roc_auc_score(test_y, pred_y[:,1])
        log_score = log_loss(test_y, pred_y)

        logging.info('{}, {}, {}'.format(training_sample_size, auc_score, log_score))
