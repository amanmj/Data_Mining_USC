from pyspark import SparkContext
import sys
from itertools import combinations
import time
import random

from pyspark.mllib.recommendation import ALS, MatrixFactorizationModel, Rating
sc = SparkContext("local[*]")

# Load and parse the data
data = sc.textFile("data/test.data")
print("data", data.take(5))
ratings = data.map(lambda l: l.split(',')).map(lambda l: Rating(int(l[0]), int(l[1]), float(l[2])))

# Build the recommendation model using Alternating Least Squares
rank = 10
numIterations = 10
model = ALS.train(ratings, rank, numIterations)

# Evaluate the model on training data
testdata = ratings.map(lambda p: (p[0], p[1]))
predictions = model.predictAll(testdata).map(lambda r: ((r[0], r[1]), r[2]))
ratesAndPreds = ratings.map(lambda r: ((r[0], r[1]), r[2])).join(predictions)
MSE = ratesAndPreds.map(lambda r: (r[1][0] - r[1][1])**2).mean()
print("Mean Squared Error = " + str(MSE))

# Save and load model
model.save(sc, "target/tmp/myCollaborativeFilter")
sameModel = MatrixFactorizationModel.load(sc, "target/tmp/myCollaborativeFilter")


x = sc.parallelize([("a", 1), ("b", 1), ("a", 1), ("a", 1),
                    ("b", 1), ("b", 1), ("b", 1), ("b", 1)],3)

# Applying reduceByKey operation on x
y = x.reduceByKey(lambda accum, n: n)
print(y.collect())


# [('b', 5), ('a', 3)]

# Define associative function separately
def sumFunc(accum, n):
    return accum + n


y = x.reduceByKey(sumFunc)
print(y.collect())
# [('b', 5), ('a', 3)]

total_hashes = 100
ret = [float('Inf') for i in range(0,total_hashes)]
print(ret)