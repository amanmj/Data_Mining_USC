from functools import reduce
from graphframes import *
from pyspark.sql.functions import first, collect_list, mean, size, udf, sort_array
import pandas as pd
from IPython.display import display
import os
import sys
import time
from pyspark import SparkContext
from itertools import combinations
from pyspark.sql import SQLContext
from graphframes import GraphFrame
from graphframes.examples import Graphs

# graphframe environment
os.environ["PYSPARK_SUBMIT_ARGS"] = ("--packages graphframes:graphframes:0.6.0-spark2.3-s_2.11")
# os.environ["PYSPARK_SUBMIT_ARGS"] = ("--packages graphframes:graphframes:0.6.0-spark2.3-s_2.11 pyspark-shell")

sc = SparkContext("local[2]")
sqlContext = SQLContext(sc)

vertices = sqlContext.createDataFrame([
  ("a", "Alice", 34),
  ("b", "Bob", 36),
  ("c", "Charlie", 30),
  ("d", "David", 29),
  ("e", "Esther", 32),
  ("f", "Fanny", 36),
  ("g", "Gabby", 60)], ["id", "name", "age"])
edges = sqlContext.createDataFrame([
  ("a", "b", "friend"),
  ("b", "c", "follow"),
  ("c", "b", "follow"),
  ("f", "c", "follow"),
  ("e", "f", "follow"),
  ("e", "d", "friend"),
  ("d", "a", "friend"),
  ("a", "e", "friend")
], ["src", "dst", "relationship"])
g = GraphFrame(vertices, edges)
print(g)
del vertices, edges

print("start label propagation")
result = g.labelPropagation(maxIter=5)
display(result)
result.select("id", "label").show()