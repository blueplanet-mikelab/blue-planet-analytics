from sklearn.metrics import accuracy_score, confusion_matrix, recall_score, precision_score


def prepareDataToNumber(inputList, categoryList):
    prepared = {}
    for cat in categoryList:
        prepared[cat] = 0
    return prepared

def accuracy(actual_values, predict_values):
    return accuracy_score(actual_values, predict_values) * 100


def find_TP(confus_result, idx): # belong to a, classified as a
    return int(confus_result[idx][idx])

def find_FN(confus_result, idx): # belong to a, classified as others
    return int(sum([pred[idx] for i, pred in enumerate(confus_result) if i != idx]))

def find_FP(confus_result, idx): # belong to others, classified as a
    return int(sum([num for i, num in enumerate(confus_result[idx]) if i != idx]))

def find_TN(confus_result, idx): # belong to others, classified as others
    return int(sum(sum(confus_result)) - (find_FP(confus_result, idx) + find_FN(confus_result, idx) + find_TP(confus_result, idx)))


def confusionMatrix(actual_values, predict_values):
    confus_result = confusion_matrix(actual_values, predict_values)
    n_category = len(confus_result)
    confus_table = [[int(cell) for cell in row] for row in confus_result.tolist()]
    scores = { "table": confus_table, "matrix":{}}
    for idx in range(n_category):
        scores["matrix"][idx] = {
            'TP': find_TP(confus_result, idx),
            'FN': find_FN(confus_result, idx),
            'FP': find_FP(confus_result, idx),
            'TN': find_TN(confus_result, idx)
        }
    return scores

def recallScore(actual_values, predict_values):
    return recall_score(actual_values, predict_values, average='macro')

def precisionScore(actual_values, predict_values):
    return precision_score(actual_values, predict_values, average='macro')