"""
HW2
In this assignment, you will implement the SON algorithm to solve all tasks (Task 1 and 2) on top of Apache Spark Framework. You need to find all the possible combinations of the frequent itemsets in any given input file within the required time. You freqItemsPass1 refer to the Chapter 6 from the Mining of Massive Datasets book and concentrate on section 6.4 – Limited-Pass Algorithms. You need to use A-Priori algorithm to process each chunk of the data.
"""

"""
To run code: 
spark-submit hw2/minh_tran_task1.py 1 4 hw2/small1.csv minh_tran_task1.txt
spark-submit hw2/minh_tran_task1.py 2 9 hw2/small2.csv minh_tran_task1.txt
"""

"""
WORKFLOW: 
read file --> obtain transactions [(user1, {business_id4,...}),(user3, {...},...]
--> partition --> run a-priori on each partition --> obtain frequent itemset
"""

"""
Task 1: Simulated data (6 pts)
There is a CSV file (test_data.csv) posted on the Blackboard. You freqItemsPass1 use this test file to debug your code. In this task, you need to build two kinds of market-basket model.
"""

"""
Case 1 (3 pts):
You will calculate the combinations of frequent businesses (as singletons, pairs, triples, etc.) that are qualified as frequent given a support threshold. You need to create a basket for each user containing the business ids reviewed by this user. If a business was reviewed more than once by a reviewer, we consider this product was rated only once. More specifically, the business ids within each basket are unique. The generated baskets are similar to:
user1: [business11, business12, business13, ...]
user2: [business21, business22, business23, ...]
user3: [business31, business32, business33, ...]
"""

"""
Case 2 (3 pts):
You will calculate the combinations of frequent trans (as singletons, pairs, triples, etc.) that are qualified as frequent given a support threshold. You need to create a basket for each business containing the user ids that commented on this business. Similar to case 1, the user ids within each basket are unique. The generated baskets are similar to:
business1:[user11,user12,user13,...] business2:[user21,user22,user23,...] business3:[user31, user32, user33, ...]
"""

import sys
from pyspark import SparkContext
from operator import add
import time
import itertools
from itertools import permutations, combinations

# Function to read each text item after reading csv
def readText(text, fileNum):
    # split the text string of each item by delimiter
    textSet = text.split(',')

    # if the file is small1.csv then return user_id, business_id
    if fileNum == 1:
        return (textSet[0], textSet[1])

    # if the file is small2.csv then return business_id, user_id
    elif fileNum == 2:
        return (textSet[1], textSet[0])
    else:
        print('Error: input file non-existent')
        exit(-1)

## Function to add an item to a set, if already exist then not executed
# add is faster for a single element because it is exactly for that purpose, adding a single element:
def addItem(existingSet, newItem):
    existingSet.add(newItem)
    return existingSet

## Function to add a set to a set, if already exist then not executed
def addSet(existingSet, newSet):
    existingSet.update(newSet)
    return existingSet

## Equivalent for list
def append(a, b):
    a.append(b)
    return a

def extend(a, b):
    a.extend(b)
    return a

## Auxillary function
def to_list(a):
    return [a]

def to_dict(a):
    return{a}



## this function is to collect all possible candidates in all baskets of 1 partition
# input are all transactions and the desired size of the candidate
# output is list of candidates with that size (each candidate is a frozen set)
def getSingletons(transactions):
    # initiate set of of candidates
    candidates = set()
    # print("transactions: ", transactions)
    # if singleton: use set operation to
    for tran in transactions:
        # union all the sets
        # candidates = rel[1] | candidates
        candidates.update(tran[1])

    # convert to fronzen set
    candidates = list({frozenset([cand]) for cand in candidates})
    # print("singleton candidates: ", candidates)
    return candidates

def getNonSingletons(frequentItemsets, size):
    # print("frequent Itemsets: ", frequentItemsets)
    candidates = set()

    # for pair, convert all input to frozen sets
    if isinstance(frequentItemsets[0], str):  # to verify
        print("transactions[0]: ", frequentItemsets[0])
        # extract all items of smaller size to a set
        frequentItemsets = {frozenset([freqItemset]) for freqItemset in frequentItemsets}

    # print("size: ", size)
    # obtain the candidates by
    #  performing unionization
    # because of monotonicity property: bigger frequent itemsets are built on top of smaller ones
    for set1 in frequentItemsets:
        for set2 in frequentItemsets:
            if len(set1.union(set2)) == size:
                candidates.update({set1.union(set2)})

    # because of monotonicity property: bigger frequent itemsets are built on top of smaller ones
    # candidates = list({a.union(b) for a in frequentItemsets for b in frequentItemsets if len(a.union(b)) == size})

    # print("candidates: ", candidates)
    return list(candidates)

## this function is to remove all itemsets with counts less than threshold
# output is a list of itemset that satisfy the given support
def getFreqItemsets(transactions, itemsets, support):
    # initialize flag table with key as itemset and zero flag for each item
    countTable = {}
    # print('transactions: ', transactions)
    # print('itemsets: ', itemsets)

    for itemset in itemsets:
        countTable[itemset] = 0

    for tran in transactions:
        for itemset in countTable:
            basket = set(tran[1])
            # check for each itemset if it is a sub-set of the basket
            if itemset.issubset(basket):  # change to a mutable set
                countTable[itemset] += 1

    # return the answer
    freqItemset = []
    for itemset in countTable:
        if countTable[itemset] >= support:
            freqItemset.append(itemset)
    return freqItemset

## Apriori algorithm
# input is all transactions, support threshold and number of [k v] pairs
# apriori_algo(x, float(support), num_users)
def apriori(transRDD, support, originalNumFiles):
    ans = []
    size = 1
    # print("before", trans)

    # convert chain objects (due to partition and map) to list for easier manipulation
    trans = []
    for tran in transRDD:
        trans.append(tran)
    # print("after", trans)
    
    # percentage of original data that is partitioned
    percentagePartition = len(trans)/originalNumFiles

    # adjust support threshold for fraction of data
    support_par = support * percentagePartition

    # extract singleton itemsets
    # print("trans: ", trans)
    cand = getSingletons(trans)

    # looping until no more candidate is feasible
    while len(cand) != 0:
        # finding frequent items
        freq_items = getFreqItemsets(trans, cand, support_par)

        # increase the size
        size += 1

        # looping among frequent items to update the answer
        for x in freq_items:
            ans.append((x, size - 1))

        #
        if len(freq_items) != 0:
            cand = getNonSingletons(list(freq_items), size)
        else:
            break
    return ans

## Function to flag frequency given input: [(user_id,{business_id1...}) and list of itemsets [(
# freq_count(x, freqItemsPass1)
# This step is to calculate
def freq_count(transactions, freq_items):
    # print("pass1", freq_items)
    countTable = {}

    # initiate initial flag
    for item in freq_items:
        countTable[item[0]] = 0

    # convert rdd object
    trans = []
    for t in transactions:
        trans.append(t)

    # loop each transaction and each frequent item
    for tran in trans:
        for freq_item in freq_items:
            if freq_item[0].issubset(tran[1]):
                countTable[freq_item[0]] += 1

     # extract the desired results
    ans = []
    for item in countTable:
        ans.append((item, countTable[item]))
    return ans

if __name__ == "__main__":
    # check number of input
    if len(sys.argv) != 5:
        print('Error: spark-submit hw2/minh_tran_task1.py 1 4 hw2/small1.csv minh_tran_task1.txt')
        exit(-1)

    # start timer
    start = time.time()

    # specify case number
    caseNum = int(sys.argv[1])

    # specify support threshold
    support = float(sys.argv[2])

    # specify file paths
    inputFilePath = sys.argv[3]
    outputFilePath = sys.argv[4]

    # initialize spark
    sc = SparkContext("local[*]")

    # Create a dictionary with keys are user_id and values are list of business_id
    # Filter the headline, then read the files (extract user_id and business_id)
    data = sc.textFile(inputFilePath).filter(lambda x: x != "user_id,business_id").map(
        lambda x: readText(x, caseNum))

    # Combine by same key (user_id)
    # combineByKey: Generic function to combine the elements for each key using a custom set of aggregation functions.
    # first convert to dict, then add a single item, then add a set??
    trans = data.combineByKey(lambda x: to_dict(x), lambda a, b: addItem(a, b), lambda a, b: addSet(a, b)).persist()

    # print('trans: ', trans.collect())
    # print(sc.textFile(inputFilePath).filter(lambda x: x != "user_id,business_id").collect())
    # print(sc.textFile(inputFilePath).filter(lambda x: x != "user_id,business_id").map(
    #     lambda x: readText(x, caseNum)).collect())

    # Total number of trans
    num_users = trans.count()
    # print("Total number of user_id: ", num_users)

    # Break original rdd to multiple chunks, and perform apriori on each chunk, then collect based on key
    # mapPartition: Return a new RDD by applying a function to each partition of this RDD, pass in the whole rdd and need to know the length of rdd assigned in each chunk to know the partition percentage
    freqItemsPass1 = trans.mapPartitions(lambda x: apriori(x, float(support), num_users), preservesPartitioning=True).distinct().collect()
    # print("Pass 1 - List of Candidates: ", freqItemsPass1)

    ## phase 2: counting the frequency of the itemsets in pass 1, making sure no false positive in partition
    # even though a partition may indicate a frequent itemset, still need to sum up all partition and make sure the total support threshold is exceeded
    freqItemsPass2 = trans.mapPartitions(lambda x: freq_count(x, freqItemsPass1)).reduceByKey(add).filter(lambda x: x[1]>= support).collect()
    # print("Pass 2 - Frequent Itemsets: ", freqItemsPass2)

    # Write out results
    with open(outputFilePath, 'w') as fileOut:
        # (1) Intermediate result:
        out = "Candidates: \n"

        k = 0
        pass1Dict = dict() # {1:[[itemset1], [itemset2]...], 2:...}

        # rearrange results in terms of size of itemsets
        # looping through all itemsets in pass 1:
        for item in freqItemsPass1:
            # if size is not in the Dict
            if item[1] not in pass1Dict:
                pass1Dict[item[1]] = [item[0]]
            else:
                pass1Dict[item[1]].append(item[0])

        # print("Pass 1 Dict: ", pass1Dict)

        # sorting the dict by size of itemsets
        for size in sorted(pass1Dict.keys()):
            # sorting the item in itemset lexicographically
            pass1Dict[size] = [sorted(x) for x in pass1Dict[size]]

            # sorting the itemsets by 1st element lexicographically
            pass1Dict[size] = sorted(pass1Dict[size])

            for x in pass1Dict[size]:
                # single tuple has annoying ,
                if len(tuple(x)) == 1:
                    out += "('" + str(tuple(x)[0])+ "'),"
                    # [0:len(str(tuple(x))) - 2] + "),"
                else:
                    out += str(tuple(x)) + ","

            # remove redundant sign (comma at the end)
            out = out[0:len(out) - 1]

            # provide spacing
            out += "\n\n"

        # print("Pass 1 Dict After-Sort: ", pass1Dict)

        # remove redundant sign (comma at the end)
        out = out[0:len(out) - 1]

        # (2) Final result
        out += "\nFrequent Itemsets:\n"

        k = 0
        pass2Dict = dict()

        for itemset in freqItemsPass2:
            size = len(itemset[0])
            if size not in pass2Dict:
                pass2Dict[size] = list([itemset[0]])
            else:
                pass2Dict[size].append(itemset[0])

        # print("Pass 2 Dict Pre-Sort: ", pass2Dict)
        for k in sorted(pass2Dict.keys()):
            pass2Dict[k] = [sorted(x) for x in pass2Dict[k]]
            pass2Dict[k] = sorted(pass2Dict[k])
            for x in pass2Dict[k]:
                # single tuple has annoying ,
                if len(tuple(x)) == 1:
                    out += "('" + str(tuple(x)[0])+ "'),"
                else:
                    out += str(tuple(x)) + ","
            out = out[0:len(out) - 1]
            out += "\n\n"

        # remove redundant spacing at the end
        out = out[0:len(out) - 2]

        # Write out results
        fileOut.write(out)

    # end timer
    end = time.time()

    # print the runtime in the console
    print("Duration:", end - start)
