"""
HW2
In this assignment, you will implement the SON algorithm to solve all tasks (Task 1 and 2) on top of Apache Spark Framework. You need to find all the possible combinations of the frequent itemsets in any given input file within the required time. You can refer to the Chapter 6 from the Mining of Massive Datasets book and concentrate on section 6.4 – Limited-Pass Algorithms. You need to use A-Priori algorithm to process each chunk of the data.
"""

"""
To run code: 
spark-submit hw2/minh_tran_task2.py 20 50 hw2/ta_feng_all_months_merged.csv minh_tran_task2.txt
spark-submit hw2/minh_tran_task2.py 20 50 hw2/input2.csv minh_tran_task2.txt
"""

"""
Task 2: Ta Feng data (4 pts)
In task 2, you will explore the Ta Feng dataset to find the frequent itemsets (only case 1). You will use data found here from Kaggle (https://bit.ly/2miWqFS) to find product IDs associated with a given customer ID each day. Assume that customers make no more than 1 purchase a day. N.B.: Be careful when reading the csv file, as spark can read the product id numbers with leading zeros. You can manually format Column F (PRODUCT_ID) to numbers (with zero decimal places) in the csv file before reading it using spark.
"""

"""
(1) Data preprocessing
You need to generate a dataset from the Ta Feng dataset with following steps:
1. Find the date of the purchase (column TRANSACTION_DT), such as December 1, 2000 (12/1/00)
2. At each date, select “CUSTOMER_ID” and “PRODUCT_ID”.
3. We want to consider all items bought by a consumer each day as a separate transaction (i.e., “baskets”).
For example, if consumer 1, 2, and 3 each bought oranges December 2, 2000, and consumer 2 also bought
celery on December 3, 2000, we would consider that to be 4 separate transactions. An easy way to do this
is to rename each CUSTOMER_ID as “DATE-CUSTOMER_ID”. For example, if COSTOMER_ID is 12321, and
this customer bought apples November 14, 2000, then their new ID is “11/14/00-12321”
4. Make sure each line in the CSV file is “DATE-CUSTOMER_ID1, PRODUCT_ID1”.
5. The header of CSV file should be “DATE-CUSTOMER_ID, PRODUCT_ID”
You need to save the dataset in CSV format. Figure 3 shows an example of the output file
"""

"""
(2) Apply SON Algorithm
The requirements for task 2 are similar to task 1. However, you will test your implementation with the
large dataset you just generated. For this purpose, you need to report the total execution time. For this
execution time, we take into account also the time from reading the file till writing the results to the
output file. You are asked to find the frequent itemsets (only case 1) from the file you just generated. The
following are the steps you need to do:
1. Reading the customer_product CSV file in to RDD and then build the case 1 market-basket model;
2. Find out qualified customers who purchased more than k items. (k is the filter threshold);
3. Apply the SON Algorithm code to the filtered market-basket model;
"""

import sys
from pyspark import SparkContext
from operator import add
import time
import datetime
import csv
import itertools

from itertools import islice
from itertools import permutations, combinations
# Function to read, modify and output a new csv file
def csvProcessor(csvInputFilePath, csvOutputFilePath):
    with open(csvOutputFilePath, 'w',newline='') as csvFileOut, open(csvInputFilePath, 'r') as csvFileIn:
        next(csvFileIn)
        writer = csv.writer(csvFileOut)
        reader = csv.reader(csvFileIn, delimiter=',')
        writer.writerow(['DATE-CUSTOMER_ID', 'PRODUCT_ID'])
        for row in reader:
            # print(row)
            dt = datetime.datetime.strptime(row[0], '%m/%d/%Y')
            dateCustomerTD = str('{0}/{1}/{2:02}'.format(dt.month, dt.day, dt.year % 100) + '-' + row[4])
            productID = str(row[5])
            writer.writerow([dateCustomerTD, productID])

def writeCSV(file):
# dt = datetime.datetime.strptime(textSet[0], '%m/%d/%Y')
# dtStr = '{0}/{1}/{2:02}'.format(dt.month, dt.day, dt.year % 100)
    with open(file, 'w') as csvFile:
        csvWriter = csv.writer(csvFile, delimiter= ',')
        csvWriter.writerow()

# Function to read each text item after reading csv
def readText(text):
    # split the text string of each item by delimiter
    textSet = text.split(',')

    # if the file is small1.csv then return user_id, business_id
    return (textSet[0], textSet[1])

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
    return {a}


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
        # print("transactions[0]: ", frequentItemsets[0])
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
    # candidates = {a.union(b) for a in frequentItemsets for b in frequentItemsets if len(a.union(b)) == size}

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
    percentagePartition = len(trans) / originalNumFiles

    # adjust support threshold for fraction of data
    support_par = support * percentagePartition

    # extract singleton itemsets
    # print("trans: ", trans)
    cand = getSingletons(trans)
    print("Finish obtaining singletons")

    # looping until no more candidate is feasible
    while len(cand) != 0 and size < 4:
        # finding frequent items
        freq_items = getFreqItemsets(trans, cand, support_par)
        print("Finish obtaining frequent itemset of size: ", size)

        # increase the size
        size += 1
        # print("current candidates: ", cand)
        # looping among frequent items to update the answer
        for x in freq_items:
            ans.append((x, size - 1))

        if len(freq_items) != 0:
            cand = getNonSingletons(list(freq_items), size)
            print("Finish obtaining candidates of bigger size itemset", size)
            # cand = construct(list(freq_items), size)
        else:
            print("no more candidate")
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

    # print("start importing data")
    # specify case number
    filterThreshold = float(sys.argv[1])

    # specify support threshold
    support = float(sys.argv[2])

    # specify file paths
    inputFilePath = sys.argv[3]
    outputFilePath = sys.argv[4]

    # print("end importing data")

    print("start processing csv")
    # pre-process csv
    outputCsvFilePath = 'hw2/minh_tran_preprocessed.csv'
    csvProcessor(inputFilePath, outputCsvFilePath)
    print("Finish processing csv ")

    # initialize spark
    sc = SparkContext("local[*]")

    # Create a dictionary with keys are user_id and values are list of business_id
    # Filter the headline, then read the files (extract user_id and business_id)
    # print("start filter and readText data")
    data = sc.textFile(outputCsvFilePath).filter(lambda x: x != "DATE-CUSTOMER_ID,PRODUCT_ID").map(lambda x: readText(x))

    # use this if input file is raw: remove the header
    # data = sc.textFile(inputFilePath).mapPartitionsWithIndex(lambda idx, it: islice(it, 1, None) if idx == 0 else it).map(lambda x: readRawText(x))

    # print("data: ", data.collect())
    print("finishing data: remove headline and read text")

    # Combine by same key (user_id)
    # combineByKey: Generic function to combine the elements for each key using a custom set of aggregation functions.
    # first convert to dict, then add a single item, then add a set??
    # print("start trans: combining items shared by same user and day")
    trans = data.combineByKey(lambda x: to_dict(x), lambda a, b: addItem(a, b), lambda a, b: addSet(a, b)).filter(lambda x: len(x[1])>filterThreshold).persist().map(lambda x: (x[0], set(x[1])))
    # print('trans: ', trans.collect())
    print("finishing trans: combine items to basket of the same user in one day, filtering by threshold")

    # Total number of trans
    num_users = trans.count()
    print("Total number of user_id: ", num_users)

    # Break original rdd to multiple chunks, and perform apriori on each chunk, then collect based on key
    # mapPartition: Return a new RDD by applying a function to each partition of this RDD, pass in the whole rdd and need to know the length of rdd assigned in each chunk to know the partition percentage
    print("start apriori")
    freqItemsPass1 = trans.mapPartitions(lambda x: apriori(x, float(support), num_users),preservesPartitioning=True).collect()
    print("end apriori")
    print("Pass 1 - List of Candidates: ", freqItemsPass1)

    ## phase 2: counting the frequency of the itemsets in pass 1, making sure no false positive in partition
    # even though a partition may indicate a frequent itemset, still need to sum up all partition and make sure the total support threshold is exceeded
    print("start counting of candidates")
    freqItemsPass2 = trans.mapPartitions(lambda x: freq_count(x, freqItemsPass1)).reduceByKey(add).filter(lambda x: x[1] >= support).collect()
    print("end counting of candidates")
    print("Pass 2 - Frequent Itemsets: ", freqItemsPass2)

    # Write out results
    print("start writting output")
    with open(outputFilePath, 'w') as fileOut:
        # (1) Intermediate result:
        out = "Candidates: \n"

        k = 0
        pass1Dict = dict()  # {1:[[itemset1], [itemset2]...], 2:...}

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
                    out += "('" + str(tuple(x)[0]) + "'),"
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
                    out += "('" + str(tuple(x)[0]) + "'),"
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
