"""
HW3
This assignment contains two parts. First, you will implement an LSH algorithm, using both
Cosine and Jaccard similarity measurement, to find similar products. Second, you will implement
a collaborative-filtering recommendation system. The dataset you are going to use is Yelp dataset
( https://w ww.yelp. com/dataset ) . The task sections below explain the assignment instructions in
detail. The goal of the assignment is to make you understand how different types of
recommendation systems work and more importantly, try to find a way to improve the accuracy of
the recommendation system yourself. This assignment is the same as our Data Mining
Competition that will end on December 17th. You can continue to improve your recommendation
accuracy and submit your scores to compete.
"""

"""
To run code: 
spark-submit minh_tran_task1.py Data/yelp_train.csv jaccard Minh_Tran_SimilarProducts_Jaccard.txt
spark-submit minh_tran_task1.py Data/yelp_train.csv cosine Minh_Tran_SimilarProducts_Cosine.txt
"""

"""
YELP data
Yelp Data
We generated the following two datasets from the original Yelp review dataset with
some filters such as the condition: “state” == “CA”. We randomly took 60% of the data as
the training dataset, 20% of the data as the validation dataset, and 20% of the data as the
testing dataset.
A. yelp_train.csv: the training data, which only include the columns: user_id, business_id,
and stars.
B. yelp_val.csv: the validation data, which are in the same format as training data.
C. We do not share the testing dataset.
"""


"""
Task 1: LSH
LSH Algorithm
In this task, you will need to develop the LSH technique using the yelp_train.csv file. The goal of
this task is to find similar products according to the ratings of the users. In order to solve this
problem, you will need to read carefully through the sections 3.3 – 3.5 from Chapter 3 of the
Mining of Massive Datasets book.
In this task, we focus on the “0 or 1” ratings rather than the actual ratings/stars from the users.
Specifically, if a user has rated a business, the user’s contribution in the characteristic matrix is 1.
If the user hasn’t rated the business, the contribution is 0. You need to identify similar
businesses whose similarity >= 0.5.
"""

"""
(1) Task 1 part 1
1. Jaccard based LSH (30%)
Implementation Guidelines - Approach
The original characteristic matrix must be of size [users] x [products]. Each cell contains a 0 or 1
value depending on whether the user has rated the product or not. Once the matrix is built, you
are free to use any collection of hash functions that you think would result in a more consistent
permutation of the row entries of the characteristic matrix.
Some potential hash functions could be of type:
f(x)= (ax + b) % m or f(x) = ((ax + b) % p) % m
where p is any prime number and m is the number of bins .
You can use any value for the a, b, p or m parameters of your implementation.
Once you have computed all the required hash values, you must build the Signature Matrix. Once
the Signature Matrix is built, you must divide the Matrix into b bands with r rows each, where
bands x rows = n (n is the number of hash functions), in order to generate the candidate pairs.
Remember that in order for two products to be a candidate businessPair their signature must agree (i.e.,
be identical) with at least one band.
Once you have computed the candidate pairs, your final result will be the candidate pairs whose
Jaccard Similarity is greater than or equal to 0.5
The program that you will implement should take two parameters as input and generate one file as
an output. The first parameter must be the location of the ratings.csv file and the second one
must be the path to the output file followed by the name of the output file. The name of the
output file must be Firstname_Lastname_SimilarProducts_Jaccard.txt . The content of the
file must follow the same directions of question 1 in the Questions & Grades Breakdown
section below. If your program does not generate this file or it does not follow the specifications
as described in the following section, there would be a penalty of 50%.
"""

# import libraries
from pyspark import SparkContext
import sys
from itertools import combinations
import time

SEED = 77

"""
Function to generate signature for each business id
"""
def sigGen(businessID, userList, numHashes, numUsers):
    # hashes = [lambda x: ((x*random.randint(0,m)+ random.randint(0,m))%m) for _ in range(0,total_hashes)] ## takes too much time

    # make hash function: here rows are users, columns are businesses
    #hashes = lambda x,y: ((x*y)+(HASH_NUM*x))%m
    # hashFunc = lambda idx, val, seed: ((val * idx) + (seed*idx)) % numUsers
    hashFunc = lambda idx, user, seed: ((user * idx) + seed) % numUsers

    # initiate the matrix (actually just a column because we are handling with only 1 business at a time
    sig = [float('Inf') for idx in range(0, numHashes)]

    # minhashing algorithm
    # loop through each user in a business column
    for user in userList:
        # loop through hash function
        for hashIdx in range(0,numHashes):
            # calculate hash values given hash index, user's rating of that business
            #hash_func = hashes(h,row)
            hashVal = hashFunc(hashIdx, user, SEED)
            # print("hash_func", hash_func)

            # update if hash value is decreasing
            if hashVal < sig[hashIdx]:
                sig[hashIdx] = hashVal
    return (businessID, sig)

"""
Function to perform locality sensitive hashing
cand = cand.flatMap(lambda x: performLSH(x,b,r)).groupByKey().filter(lambda x: len(x[1])>1)
"""
def performLSH(row,numBands,numRows):
    ans = []

    # loop through bands
    for i in range(0,numBands):
        x = i*numRows
        y = (i+1)*numRows
        band = row[1][x:y] #.insert(0,i)
        band.insert(0,i) # just to seperate each bucket
        # print(band)
        ans.append((tuple(band),row[0]))
    return ans

"""
Function to calculate true jaccard similarity between two businesses
"""
def calJaccardSim(businessPair,charMatSet, threshold):
    ans = []

    # obtain the set of users who have rated these two businesses
    business1 = charMatSet[businessPair[0]]
    business2 = charMatSet[businessPair[1]]

    # calculate union intersection
    intersection = len(business1.intersection(business2))
    union = len(business1.union(business2))

    # calculate jaccard similariyy
    simVal = float(intersection)/float(union)

    # candidate pair only if jaccard similarity excceds 0.5, return the answer
    if simVal >= threshold:
        ans = (frozenset((businessPair[0],businessPair[1])),simVal)
    return ans

"""
Function to calculate true jaccard similarity between two businesses
"""
def calJaccardSimAux(businessPair,charMatSet, threshold):
    ans = []

    # obtain the set of users who have rated these two businesses
    business1 = charMatSet[businessPair[0]]
    business2 = charMatSet[businessPair[1]]

    # calculate union intersection
    intersection = len(business1.intersection(business2))
    union = len(business1.union(business2))

    # calculate jaccard similariyy
    simVal = float(intersection)/float(union)

    # candidate pair only if jaccard similarity excceds 0.5, return the answer
    if simVal >= threshold:
        ans = ((businessPair[0],businessPair[1]),simVal)
    return ans


"""
Function to calculate true jaccard similarity between two businesses
"""
def calCosineSim(businessPair,charMatSet, threshold):
    ans = []

    # obtain the set of users who have rated these two businesses
    business1 = charMatSet[businessPair[0]]
    business2 = charMatSet[businessPair[1]]

    # calculate union intersection
    intersection = len(business1.intersection(business2))
    union = len(business1.union(business2))

    # calculate jaccard similariyy
    simVal = float(intersection)/float(union)

    # candidate pair only if jaccard similarity excceds 0.5, return the answer
    if simVal >= threshold:
        ans = (frozenset((businessPair[0],businessPair[1])),simVal)
    return ans

# Function to read the given csv file
def csvReader(csvFile):
    return csvFile.split(',')


# utility functions
def append(a,b):
    a.append(b)
    return a

def extend(a,b):
    a.extend(b)
    return a

# function to import list data to dict
# input: data in the form of list
# output: dict in the form of {item1: 0, item1: 1...}
def importToDict(listData):
    dictData = {}
    idx = 0
    for item in listData:
        dictData[item] = idx
        idx += 1
    return dictData

# function to import list data to dict ( 2 version of outputs)
# input: data in the form of list
# output 1: dict in the form of {item1: 0, item2: 1...}
# output 2: dict in the form of {0: item1, 1: item2...}
def importToDict2(listData):
    # import user id into a dict {userID: numID} for hashing
    # output is {userID1:0 , userID2:1,...}
    dictData1 = {}
    dictData2 = {}
    idx = 0
    for item in listData:
        dictData1[item] = idx
        dictData2[idx] = item
        idx += 1
    return dictData1, dictData2

if __name__ == "__main__":
    # check input
    if len(sys.argv)!=4:
        print("This function needs 3 input arguments <input_file_name> <similarity method> <output_file_name>")
        exit(-1)
        
    # start timer
    start = time.time()
    
    # import input files
    inputFile = sys.argv[1]
    simMethod = sys.argv[2]
    outputFile = sys.argv[3]
    sc = SparkContext("local[*]")

    # read data: note that only users who have rated business provide
    # output is [[userID, businessID, rating],...]
    data = sc.textFile(inputFile).filter(lambda x: x!="user_id, business_id, stars").map(lambda x: csvReader(x)).persist()
    # print("data", data.take(5))

    # get unique list of user id. That's why reduceByKey overwrite value
    # output is: [userID1, userID2,...]
    userIDList = data.map(lambda x: (x[0],1)).reduceByKey(lambda old,new: new).map(lambda x: x[0]).collect()
    userIDList.sort() # sort user ID
    # print("(userIDList)", userIDList[0:4])

    # get number of users
    numUsers = len(userIDList)
    # print("number of unique user id", numUsers)

    # import user id into a dict {userID: numID} for hashing
    # output is {userID1:0 , userID2:1,...}
    userIDDict, idUserDict = importToDict2(userIDList)

    # get unique business id:
    businessIDList = data.map(lambda x: (x[1],1)).reduceByKey(lambda old,new: new).map(lambda x :x[0]).collect()
    businessIDList.sort()
    numBusinesses = len(businessIDList)
    # print("number of unique business id", numBusinesses)

    # import user id into a dict {userID: numID} for hashing
    # output is {userID1:0 , userID2:1,...} and {0: userID1,1:userID2...}
    businessIDDict, idBusinessDict = importToDict2(businessIDList)

    '''
    hashing parameters
    '''
    numHashes = 200  # number of hash functions
    numBands = 100 # number of bands
    numRows = numHashes//numBands  # number of rows in each band
    idealThreshold = (1/numBands) ** (1/numRows)
    threshold = 0.5
    # print("threshold: ", idealThreshold)

    # characteristic matrix
    # sequence: map to (businessID idx, userID idx), then combine all users that have rated that business
    # [(businessID1, [userID1, userID2...]),...] list of tuple of (business, users)
    charMatList = data.map(lambda x: (businessIDDict[x[1]],userIDDict[x[0]])).combineByKey(lambda x: [x], lambda a,b: append(a,b), lambda a,b: extend(a,b)).persist()
    # print("charMatList", charMatList.collect())

    # convert from list to set and dictionary
    # {businessID1: {userID1,userID2},...}
    charMatSet = charMatList.map(lambda x: (x[0],set(x[1]))).collectAsMap()
    # print("charMatSet", charMatSet)

    # make signature with input: businessID, list of userIDs that have rated that business, number of hash function, number of users
    # output is list of tuples: (businessID, [hashVal1,hashVal2...])
    cand = charMatList.map(lambda x: sigGen(x[0],x[1],numHashes,numUsers))
    # print("cand1", cand.take(5))

    # perform locality sensitive hashing with input: list of tuples, number of band and row
    # output is list of tuple of ??:
    cand = cand.flatMap(lambda x: performLSH(x,numBands,numRows)).groupByKey().filter(lambda x: len(x[1])>1)
    # print("cand2",cand.take(5))

    # obtain pair of candidates
    # output is a list of pair of candidates
    cand = cand.flatMap(lambda x: [y for y in combinations(x[1],2)]).distinct().persist()
    # print("cand3", cand.take(5))

    if simMethod == "jaccard":
        # obtain final answer by calculating jaccard similarity of the candidate businessPair
        # output is a dictionary of {frozenset1({business1, business2}): jaccard,...
        ans = cand.map(lambda x: calJaccardSim(x,charMatSet,threshold)).filter(lambda x: x!=[]).collectAsMap()
        # print(len(ans))
        # print("ans", ans)

        # get to the correct format to join with validation data
        # triplet = cand.map(lambda x: calJaccardSimAux(x,charMatSet,threshold)).filter(lambda x: x!=[])
        # print("triplet: ", triplet)

    elif simMethod == "cosine":
        ans = cand.map(lambda x: calCosineSim(x, charMatSet, threshold)).filter(lambda x: x != []).collectAsMap()


    # reorganize dictionary to sorted list
    ansList = []
    for key in ans.keys():
        # this key has 2 businesses, sort these two
        keySorted = [sorted(tuple(key))]

        # append value of similarity
        keySorted.append(ans[key])
        ansList.append(list(keySorted))
    ansListSorted = sorted(ansList)
    # print("ansList", ansListSorted)

    # write out
    out = "business_id_1, business_id_2, similarity\n"
    triplet = set()
    # out = ""
    # use dict to obtain business ID from business idx
    for pair in ansListSorted:
        out += idBusinessDict[pair[0][0]] + "," + idBusinessDict[pair[0][1]] + "," + str(pair[1])+"\n"
        triplet.add((idBusinessDict[pair[0][0]],idBusinessDict[pair[0][1]]))
    # print("triplet: ", triplet)

    # Validate with true results;
    valDataRaw = sc.textFile("Data/pure_jaccard_similarity.csv").filter(lambda x: x != "business_id_1, business_id_2, similarity").map(
         lambda x: csvReader(x)).map(lambda x: ((x[0], x[1]))).collect()
    valData = set(valDataRaw)
    # print("valData", valDataRaw)

    # calculate precision and recall
    tp = valData.intersection(triplet)
    fp = triplet - tp
    fn = valData - tp

    precision = len(tp)/(len(tp)+len(fp))
    recall = len(tp) / (len(tp) + len(fn))
    print("precision: ", precision)
    print("recall: ", recall )
    print("score:",(precision / 1.0) * 25 + (recall / 0.95) * 25 )

    with open(outputFile,"w") as file:
        file.write(out)
        file.close()
    
    # end timer and generate prompt
    end = time.time()
    print("time: ", str(end-start))