#
"""
HW3
"""
"""
In this task, you are going to build different types of recommendation systems using the
yelp_train.csv to predict for the ratings/stars for given user ids and business ids. You can make
any improvement to your recommendation system in terms of the running time and accuracy. You
can use the validation dataset (yelp_val.csv) to evaluate the accuracy of your recommendation
systems.
You CANNOT use the ratings in the testing datasets to train your recommendation system. You
can use the testing data as your ground truth to evaluate the accuracy of your recommendation
system.
There are two options to evaluate your recommendation systems. You can compare your results to
the corresponding ground truth and compute the absolute differences. You can divide the absolute
differences into 5 levels and count the number for each level as the following chart:
>=0 and <1: 12345
>=1 and <2: 123
>=2 and <3: 1234
>=3 and <4: 1234
>=4: 12
This means that there are 12345 predictions with < 1 difference from the ground truth. This way
you will be able to know the error distribution of your predictions and to improve the performance
of your recommendation systems.
Additionally, you can compute the RMSE (Root Mean Squared Error) by using the following
formula:
Where Predi is the prediction for business i and Ratei is the true rating for business i. n is the total
number of the business you are predicting.
"""

"""
In task 2, you are required to implement:
1. Model-based CF recommendation system by using Spark MLlib. (20%)
You can only use Scala to implement this task. You can learn more about Spark MLlib by
this link: http://spark.apache.org/docs/latest/mllib-collaborative-filtering.html
We will grade on this task based on your accuracy. If your RMSE is greater than the baseline
showing in the table below, there will be 20% penalty.
RMSE 1.30
Time(sec) 50s
2. User-based CF recommendation system by yourself. (30%)
Below is the baseline for user-based CF. Both accuracy and time is measured. If your RMSE
or run time is greater than the baseline, there’ll be 20% penalty each.
RMSE 1.18
Time (sec) 180s
3. Item-based CF integrating LSH result you got from task 1. (Bonus points: 10%)
In task 1, you’ve already found all the similar products pairs in the dataset. You need to use
them to implement an item-based CF. Also measure the performance of it as previous one
does.
Comparing the result with CF without LSH and answering how LSH could affect the
recommendation system? No baseline requirement for this one. If you successfully
implement it and have reasonable answer to the question, you can get the bonus points.
"""

"""

"""


"""
To run code: 
spark-submit minh_tran_competition.py Competition/ Competition/yelp_val.csv minh_tran_output.txt
"""
import sys
from pyspark import SparkContext
from operator import add
import time
from collections import defaultdict
from itertools import combinations
from pyspark.mllib.recommendation import ALS, MatrixFactorizationModel, Rating

# Function to read the given csv file
def csvReader(csvFile):
    return csvFile.split(',')

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

# receive tons of dictionaries and process
def updateDict(old,new):
    # if dict not exist yet
    if not isinstance(old,dict):
        return new
    else:
        # add elements to the existing dictionary
        old.update(new)
        return old

def writeFile(outputFilePath, predictions, idUserDict, idBusinessDict):
    out = "user_id, business_id, prediction\n"
    for x in predictions.map(lambda x: (x[0][0], x[0][1], x[1])).collect():
        out += idUserDict[x[0]] + "," + idBusinessDict[x[1]] + "," + str(x[2]) + "\n"
    with open(outputFilePath, "w") as f:
        f.write(out)
        f.close()

def writeTxt(outputFilePath, errorDist, rmse, time):
    # out = "Minh Tran - INF 553 - Competition Description"

    out = "Method Description:\n"
    out += "The model follows closely the guidance in HW3. User-based collaborative filtering is utilized. To predict a rating of a business B by user U, gather similar users to U based on how they rate businesses in general; then evaluate that set of users how they rate business B and deduce how U might rate B. Ratings are normalized by the average. Exception for pair of (user U, business B) is handled as followed: \n if B has not been rated by any user and U have not rated any business, assign 3.0. \n if B has not been rated by any user, assign rating of average rating of user U \n if U has not rated any business, assign rating of average rating of business B. \n"
    out += "\nError Distribution:\n"

    keySorted = []
    for key in errorDist.keys():
        # append value of similarity
        keySorted.append(key)
    keySorted = sorted(keySorted)

    for key in keySorted:
        out += key + ": " + str(errorDist[key])+"\n"

    out += "\nRMSE:\n" + str(rmse)+"\n"
    out += "\nExecution Time:\n" + time

    with open(outputFilePath, "w") as f:
        f.write(out)
        f.close()

# function to calculate root mean square error
# input: (user,business), (actual rating, predicted rating)
def calRSME(validation):
    MSE = validation.map(lambda x: (x[1][0] - x[1][1])**2).mean()
    RMSE = pow(MSE,1/2)
    # print("RMSE = ",str(RMSE))
    return RMSE

def calError(validation):
    errorDist = {}
    bin01Key = '>=0 and <1'
    bin12Key = '>=1 and <2'
    bin23Key = '>=2 and <3'
    bin34Key = '>=3 and <4'
    bin45Key = '>=4'

    bin01 = validation.map(lambda x: abs(x[1][0] - x[1][1])).filter(lambda x : x >= 0 and x<1).count()
    bin12 = validation.map(lambda x: abs(x[1][0] - x[1][1])).filter(lambda x: x >= 1 and x < 2).count()
    bin23 = validation.map(lambda x: abs(x[1][0] - x[1][1])).filter(lambda x: x >= 2 and x < 3).count()
    bin34 = validation.map(lambda x: abs(x[1][0] - x[1][1])).filter(lambda x: x >= 3 and x < 4).count()
    bin45 = validation.map(lambda x: abs(x[1][0] - x[1][1])).filter(lambda x: x >= 4).count()

    errorDist[bin01Key] = bin01
    errorDist[bin12Key] = bin12
    errorDist[bin23Key] = bin23
    errorDist[bin34Key] = bin34
    errorDist[bin45Key] = bin45
    return errorDist

"""
CASE 1
"""
SEED = 7
RANK = 2  # number of latent factors
numIterations = 5  # number of iterations of ALS to run <20

'''
Function to handle exceptions
Input is pair (user, business) and dict sumUserRating, dict of avg_businesses
'''
def handleExceptions(pair, meanUsersRating, meanBusinessesRating):
    # if user not rating and business not rated:
    if pair[0] not in meanUsersRating and pair[1] not in meanBusinessesRating:
        return (pair, DEFAULT_RATING)
    
    # if U has not rated any business, give (U,I) the average rating by all other users
    elif pair[0] not in meanUsersRating:
        return (pair, meanBusinessesRating[pair[1]])

    # if I has not been rated by any user, give (U,I) the average rating of U for all other businesses
    elif pair[1] not in meanBusinessesRating:
        return (pair, meanUsersRating[pair[0]])

    else:
        pass

"""
CASE 2
"""
DEFAULT_WEIGHT = 0.2
DEFAULT_RATING = 3.0
'''
function to assign weights between 2 user
INPUT
user1: new user_id
user2: existing user id 
setBusiness1: set of items rated by user 1
setBusiness2: set of items rated by user 2
ratings1: dict {item_id:rating} of user 1
ratings2: dict {item_id:rating} of user 2
'''
# slide 11 recommenderSystemsPart2
# calcWeightUserBased(userU,user,userBusinessDict[userU], userBusinessDict[user], userBusinessRatingDict[userU], userBusinessRatingDict[user])
def calcWeightUserBased(user1,user2, userBusinessDict, userBusinessRatingDict):
    
    # obtain business rated by each user
    setBusiness1 = userBusinessDict[user1]
    setBusiness2 = userBusinessDict[user2]
    
    # set of items that are rated by both users
    coratedBusiness = list(setBusiness1.intersection(setBusiness2))

    # ?? if 2 users don't rate any item in common, assign weight 0.2
    if len(coratedBusiness)==0:
        return DEFAULT_WEIGHT
    
    # obtain business rating of each user
    ratings1 = userBusinessRatingDict[user1]
    ratings2 = userBusinessRatingDict[user2]

    # get all ratings of each user to all items corated by both
    ratingsForCorated1 = []
    ratingsForCorated2 = []
    for business in coratedBusiness:
        ratingsForCorated1.append(ratings1[business])
        ratingsForCorated2.append(ratings2[business])

    # get average rating of user 1 to all items corated by both
    avgRating1 = sum(ratingsForCorated1)/len(ratingsForCorated1)
    avgRating2 = sum(ratingsForCorated2)/len(ratingsForCorated2)

    # calculate cosine distance between 2 users with ratings normalized by the average
    sumU1DotU2 = 0 # numerator
    sumU1  = 0 # denominator term 1
    sumU2  = 0 # denominator term 2

    for business in coratedBusiness:
        sumU1DotU2 += (ratings1[business]-avgRating1)*(ratings2[business]-avgRating2)
        sumU1 += (ratings1[business]-avgRating1)**2
        sumU2 += (ratings2[business]-avgRating2)**2

    # default value
    if sumU1DotU2==0:
        return DEFAULT_WEIGHT
    
    return sumU1DotU2/((sumU1**0.5)*(sumU2**0.5))

# function to check rating anomaly
def checkRating(rating):
    if rating < 1:
        rating = 1.0
    if rating > 5:
        rating = 5.0


'''
This function is to calculate unknown rating given by an user to a business USER-BASED
INPUT:
userU : user who we want to find out his/her rating
businessB : business who we want to know its rating
userBusinessRatingDict: rating of all users dict {user_id:{item_id:rating}}
userBusinessDict  : dict of {user_id: {item_ids}}
avgBusinessRating   : dict of {item_id: avg rating of item}
avgUserRating   : dict of {user_id: (sum(ratings),len(ratings))}
businessUserDict  : dict of {item_id: {user_ids}}
'''
def predictRatingUserBased(userU, businessB, userBusinessRatingDict, userBusinessDict, avgBusinessRating, sumUserRating,businessUserDict, avgUserRating):
    # exception handle
    # handleExceptions2(userU, businessB, avgUserRating, avgBusinessRating)
    if userU not in avgUserRating and businessB not in avgBusinessRating:
        return ((userU, businessB), DEFAULT_RATING)

    # if new user have not rated any business, no way to find similar users, give rating as the average of ratings for that item
    elif userU not in avgUserRating:
        value = avgBusinessRating[businessB]
        checkRating(value)
        return ((userU, businessB), value)

    # if new item has not been rated by any user, give the rating as the average of the given users
    elif businessB not in avgBusinessRating:
        value = avgUserRating[userU]
        checkRating(value)
        return ((userU, businessB), value)
    else:

        # ALL OTHER CASES: business B have been rated or user U has rated
        numerator = 0
        weight = 0
        sumAbs = 0
        weights = dict()

        # extract who are users that have rated new item
        usersSet = businessUserDict[businessB]

        # loop through user that have rated new item
        for user in usersSet:
            # calculate weights of that user in rating the new item
            weight = calcWeightUserBased(userU,user,userBusinessDict, userBusinessRatingDict)

            # update weights of that user for the new item
            weights[user] = weight

            # calculate average rating of user for all OTHER rated items
            avgRatingUserExclude = (sumUserRating[user][0] - userBusinessRatingDict[user][businessB])/(sumUserRating[user][1]-1)
            # avgRatingUserExclude = sumUserRating[user][0] / sumUserRating[user][1]

            # ?? should it be consistently abs(weight)
            numerator += (weight*(userBusinessRatingDict[user][businessB] - avgRatingUserExclude))
            sumAbs += abs(weight)

        # average rating of user U on all OTHER rated items
        # ra = (sumUserRating[userU][0] - float(userBusinessRatingDict[userU][businessB]))/(sumUserRating[userU][1]-1)
        ra = float((sumUserRating[userU][0]/sumUserRating[userU][1]))

        # ??
        if numerator == 0:
            return ((userU,businessB),DEFAULT_RATING)

        # calculate rating: slide 23 recommender system part 2
        finalRating = (ra + (numerator / sumAbs))
        checkRating(finalRating)
        # print(((userU,businessB), finalRating))
        return ((userU,businessB), finalRating)

"""
CASE 3 (WITHOUT USING LSH)
"""

'''
This function is to calculate unknown rating given by an user U to a business B USER-BASED
INPUT:
item_id1: int item id 
item_id2: int item id
userSet1: set of users who have rated item id 1
userSet2: set of users who have rated item id 2
ratings1: dictionary of ratings for item id 1 {user_id: rating}
ratings2: dictionary of ratings for item id 2 {user_id: rating}
'''
def calcWeightItemBased(business1, business2, businessUserDict, businessUserRatingDict):
    # get set of users that have rated these businesses
    userSet1 = businessUserDict[business1]
    userSet2 = businessUserDict[business2]
    
    # get set of users that rate both businesses
    corateUsers = userSet1.intersection(userSet2)
    if len(corateUsers) == 0:
        return DEFAULT_WEIGHT
    
    # get User and Rating of these businesses
    ratings1 = businessUserRatingDict[business1]
    ratings2 = businessUserRatingDict[business2]

    # get avg ratings of each business by only users in the co-rated set
    sum1 = 0
    sum2 = 0
    n = 0

    for user in corateUsers:
        sum1 += ratings1[user]
        sum2 += ratings2[user]
        n+=1
    avgRatings1 = sum1/n
    avgRatings2 = sum2/n
    
    # calculate cosine distance between 2 items with ratings normalized by the average
    sumI1DotI2 = 0
    sumI1 = 0
    sumI2 = 0

    for user in corateUsers:
        sumI1DotI2 += ((ratings1[user]- avgRatings1) * (ratings2[user] - avgRatings2))
        sumI1 += (ratings1[user]- avgRatings1)**2
        sumI2 += (ratings2[user] - avgRatings2)**2

    if sumI1DotI2==0:
        return DEFAULT_WEIGHT
    
    return sumI1DotI2/((sumI1**0.5)*(sumI2**0.5))

'''
This function is to calculate unknown rating given by an user to a business ITEM-BASED
item_id1: int item id 
item_id2: int item id
userSet1: set of users who have rated item id 1
userSet2: set of users who have rated item id 2
ratings1: dictionary of ratings for item id 1 {user_id: rating}
ratings2: dictionary of ratings for item id 2 {user_id: rating}
'''
def predictRatingItemBased(userU, businessB, userBusinessRatingList, businessUserRatingDict, businessUserDict,avgBusinessRating,avgUserRating):
    # handle exceptions
    if userU not in avgUserRating and businessB not in avgBusinessRating:
        return ((userU,businessB),DEFAULT_RATING)
    
    elif userU not in avgUserRating:
        return ((userU,businessB),avgBusinessRating[businessB])
    
    elif businessB not in avgBusinessRating:
        return ((userU,businessB),avgUserRating[userU])
    

    # calculate weights
    weights = []
    # all ratings by user U
    eachUserRatings = userBusinessRatingList[userU]
    for idx in range(0,len(eachUserRatings)):
        # calculate weights of how similar business B to all businesses rated by U
        business = eachUserRatings[idx][0]
        weightItemItem = calcWeightItemBased(businessB,business,businessUserDict, businessUserRatingDict)
        
        # it is ok for weight to be zero
        if weightItemItem ==0:
            continue

        # return the idx to keep track in the list of each user rating
        weights.append((weightItemItem,idx))

    # calculate final rating with normalized weights
    # weights = [(w1,idx1], (w2,idx2), ...]
    # eachUserRatings = [(b1,r1),(b2,r2),...]
    numerator = 0
    sumWeight = 0
    for i in weights:
        businessRatingPair = eachUserRatings[i[1]]
        rating = businessRatingPair[1]
        business = businessRatingPair[0]
        
        avgRating = avgBusinessRating[business]
        numerator += ( (rating - avgRating) * i[0])
        sumWeight += abs(i[0])

    if numerator ==0:
        return ((userU,businessB),DEFAULT_RATING)

    finalRating = float(avgBusinessRating[businessB] + numerator/sumWeight)
    return ((userU,businessB),finalRating)


"""
MAIN
"""
if __name__ == "__main__":
    if len(sys.argv)!=4:
        print("This function needs 3 input arguments <train_file_name> <test_file_name> <caseID> <outputFilePath>")
        exit(-1)

    # start timer
    start = time.time()

    # import data yelp_train.csv
    trainFileFolder = sys.argv[1]
    trainFilePath  = trainFileFolder + "yelp_train.csv"
    valFilePath    = sys.argv[2]
    # caseID         = int(sys.argv[3])
    outputFilePath = sys.argv[3]

    sc = SparkContext("local[*]")

    # import data (user, business, rating)
    trainRawData = sc.textFile(trainFilePath).filter(lambda x: x!="user_id, business_id, stars").map(lambda x: csvReader(x)).map(lambda x: (x[0],x[1],float(x[2]))).persist()
    valRawData = sc.textFile(valFilePath).filter(lambda x: x!="user_id, business_id, stars").map(lambda x: csvReader(x)).map(lambda x: (x[0],x[1],float(x[2]))).persist()
    # print("val data count = ",valRawData.count())

    # merge training and validation data:
    data = sc.union([trainRawData,valRawData])
    # print("data count = ",data.count())

    # obtain unique user ID
    userIDList = data.map(lambda x: (x[0],1)).reduceByKey(lambda old,new: new).map(lambda x: x[0]).collect()
    userIDList.sort()
    # print("len(uni_users) = ",len(userIDList))
    userIDDict, idUserDict = importToDict2(userIDList)

    # obtain unique business ID {business1:idx1,...} and {idx1:business1,...}
    businessIDList = data.map(lambda x: (x[1],1)).reduceByKey(lambda old,new: new).map(lambda x:x[0]).collect()
    # print("len(businessIDList)",len(businessIDList))
    businessIDList.sort()
    businessIDDict, idBusinessDict = importToDict2(businessIDList)

    # pre-process data -->  ((userIdx, businessIdx), star)
    trainData = trainRawData.map(lambda x: ((userIDDict[x[0]], businessIDDict[x[1]]), float(x[2]))).persist()
    valData   = valRawData.map(lambda x: ((userIDDict[x[0]], businessIDDict[x[1]]), float(x[2]))).persist()

    # (business, [rating]) -> reduceByKey -> (business, [rating1+rating2]) -> average out ->  (business, average rating)
    avgBusinessRating = trainData.map(lambda x: (x[0][1], [x[1]])).reduceByKey(lambda old, new: old + new).map(
        lambda x: (x[0], sum(x[1]) / len(x[1]))).collectAsMap()

    # (user, [rating]) -> reduceByKey -> (user, [rating1+rating2]) -> (user, avgRating)
    avgUserRating = trainData.map(lambda x: (x[0][0], [x[1]])).reduceByKey(lambda old, new: old + new).map(
         lambda x: (x[0], sum(x[1]) / len(x[1]))).collectAsMap()

    # (business, {user} -> reduceByKey (business) --> (business, {user1, user2,...})
    businessUserDict = trainData.map(lambda x: (x[0][1], {x[0][0]})).reduceByKey(
        lambda old, new: old.union(new)).collectAsMap()

    """
    MODEL-BASED CF:  spark.mllib currently supports model-based collaborative filtering, in which users and products are described by a small set of latent factors that can be used to predict missing entries. spark.mllib uses the alternating least squares (ALS) algorithm to learn these latent factors.
    """
    # if caseID ==1:
    #     # parse the training data ((userIdx, businessIdx), star) and Rating(userIdx, businessIdx, rating)
    #     # using persist() we can use various storage levels
    #     ratings      = trainData.map(lambda x: Rating(x[0][0], x[0][1], x[1]))
    #
    #     # Build the recommendation model using Alternating Least Squares
    #     model = ALS.train(ratings, RANK, numIterations,  nonnegative = True, seed = SEED) #default method which assumes ratings are explicit
    #
    #     # lambda_= 0.01 , blocks = 6,
    #
    #     # validation data with Rating(userIdx, businessIdx, rating) and without rating: (userIdx, businessIdx)
    #     valDataWithRating = valData.map(lambda x: Rating(x[0][0], x[0][1], x[1]))
    #     valDataWORating   = valDataWithRating.map(lambda x: (x[0],x[1]))
    #
    #     # userDataWORating = valDataWithRating.map(lambda x: x[0])
    #     # businessDataWORating = valDataWithRating.map(lambda x: x[1])
    #
    #     # Evaluate the model on validation data
    #     predictions = model.predictAll(valDataWORating).map(lambda x: ((x[0],x[1]),x[2]))
    #     # predictions = model.predict(userDataWORating, businessDataWORating).map(lambda x: ((x[0], x[1]), x[2]))
    #
    #     # evaluate exception size(true(userIdx, businessIdx)) - size(predicted(userIdx, businessIdx))
    #     exceptions = valRawData.map(lambda x: (userIDDict[x[0]],businessIDDict[x[1]])).subtract(predictions.map(lambda x: (x[0][0],x[0][1])))
    #
    #     # if there are items that are not predicted because of exception, handle them by exception function
    #     if exceptions.count()!=0:
    #         predictions = sc.union([predictions,exceptions.map(lambda x: handleExceptions(x,avgUserRating,avgBusinessRating))])
    #
    #     # join predicted rating with true rating ((user, business), (true rating, predicted rating))
    #     # validation = valDataWithRating.map(lambda x: ((x[0], x[1]), x[2])).join(predictions)
    #     # print("validation: ", validation)

    # USER-BASED CF: to rate a business, gather similar users based on how they rate business; then evaluate other users how they rate this business and deduce
    # # elif caseID==2:
    # # (user, {business: rating}) -> reduceByKey (user) --> (user, {{business1: rating1},...}
    # userBusinessRatingDict = trainData.map(lambda x: (x[0][0],{x[0][1]:x[1]})).reduceByKey(lambda old,new: updateDict(old,new)).collectAsMap()
    #
    # # (user, {business} -> reduceByKey (user) --> (user, {business1, business2,...})
    # userBusinessDict   = trainData.map(lambda x: (x[0][0],{x[0][1]})).reduceByKey(lambda old,new: old.union(new)).collectAsMap()
    #
    # # (user, [rating]) -> reduceByKey -> (user, [rating1+rating2]) -> (user, (sum(rating),  num(rating)))
    # sumUserRating = trainData.map(lambda x: (x[0][0], [x[1]])).reduceByKey(lambda old, new: old + new).map(
    #      lambda x: (x[0], (sum(x[1]), len(x[1])))).collectAsMap()
    #
    # # do prediction on validation data
    # predictions = valData.map(lambda x: predictRatingUserBased(x[0][0],x[0][1],userBusinessRatingDict,userBusinessDict,avgBusinessRating,sumUserRating,businessUserDict, avgUserRating))
    # # print("predictions: ", predictions.collect())
    # #
    # validation = predictions.join(valData)
    # # print("validation: ", validation.take(5))

    # ITEM-BASED CF: to rate a business, gather similar businesses based on how they are rated by users; then evaluate other businesses' ratings how they rate this business and deduce
    # elif caseID==3:
    # (business, {user: rating})
    businessUserRatingDict = trainData.map(lambda x: (x[0][1],{x[0][0]:x[1]})).reduceByKey(lambda old,new: updateDict(old,new)).collectAsMap()
    # print("businessUserRatingDict: ", businessUserRatingDict)

    # (user, [business, rating])
    userBusinessRatingList = trainData.map(lambda x: (x[0][0], [(x[0][1], x[1])])).reduceByKey(
        lambda old, new: old + new).collectAsMap()
    # print("userBusinessRatingList", userBusinessRatingList)

    predictions = valData.map(lambda x: predictRatingItemBased(x[0][0],x[0][1],userBusinessRatingList,businessUserRatingDict,businessUserDict,avgBusinessRating,avgUserRating))

    validation = predictions.join(valData)

    rmse = calRSME(validation)

    errorDist = calError(validation)
    # print('error: ', errorDist)
    # write output
    writeFile(outputFilePath, predictions, idUserDict, idBusinessDict)

    end = time.time()
    # write text
    writeTxt('minh_tran_description.txt', errorDist, rmse, str(end-start))

    # print("time: ",str(end-start))





