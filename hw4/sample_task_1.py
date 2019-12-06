import os
import sys
import time
from pyspark import SparkContext
from itertools import combinations
from pyspark.sql import SQLContext
from graphframes import GraphFrame

os.environ["PYSPARK_SUBMIT_ARGS"] = ("--packages graphframes:graphframes:0.6.0-spark2.3-s_2.11 pyspark-shell")

curr = time.time()
threshold = int(sys.argv[1])
input = sys.argv[2]
output = sys.argv[3]

sc = SparkContext(appName="LPA")
RawRDD = sc.textFile(input).map(lambda x: x.split(','))
header = RawRDD.first()
DataRDD = RawRDD.filter(lambda x: x != header)

dic = {}
for x in DataRDD.collect():
    if x[0] not in dic:
        dic[x[0]] = set()
    dic[x[0]].add(x[1])

edgelist = []
verticeSet = set()
for x in combinations(dic.keys(), 2):
    if len(dic[x[0]].intersection(dic[x[1]])) >= threshold:
        edgelist.append(x)
        edgelist.append((x[1], x[0]))
        verticeSet.add(x[0])
        verticeSet.add(x[1])

verticelist = list(combinations(verticeSet, 1))

sqlContext = SQLContext(sc)
vertices = sqlContext.createDataFrame(verticelist, ["id"])
edges = sqlContext.createDataFrame(edgelist, ["src", "dst"])
g = GraphFrame(vertices, edges)
labeled = g.labelPropagation(maxIter=5)
resRDD = labeled.rdd.map(lambda x: (x['label'], [x['id']]))\
    .reduceByKey(lambda x, y: x+y)\
    .map(lambda x: (len(x[1]), [sorted(x[1])]))\
    .reduceByKey(lambda x, y: x+y)\
    .map(lambda x: (x[0], sorted(x[1])))\
    .sortByKey()

f = open(output, "w")
for x in resRDD.collect():
    communities = x[1]
    for community in communities:
        f.write(str(community)[1:-1]+'\n')
f.close()

print("runtime", time.time()-curr, "s")