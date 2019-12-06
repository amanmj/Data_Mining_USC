from functools import reduce
from pyspark.sql.functions import col, lit, when
from graphframes import *
from pyspark.sql import SQLContext
import sys
from pyspark import SparkContext
from operator import add,itemgetter
import time
from itertools import combinations
from IPython.display import display
import pandas as pd

"""
To run code:
spark-submit --packages graphframes:graphframes:0.6.0-spark2.3-s_2.11 graphFrameTutorial.py
spark-submit --packages graphframes:graphframes:0.6.0-spark2.3-s_2.11 firstname_lastname_task1.py
<input_file_path> <community_output_file_path>
"""

"""
Creating GraphFrames
Users can create GraphFrames from vertex and edge DataFrames.

Vertex DataFrame: A vertex DataFrame should contain a special column named "id" which specifies unique IDs for each vertex in the graph.
Edge DataFrame: An edge DataFrame should contain two special columns: "src" (source vertex ID of edge) and "dst" (destination vertex ID of edge).
Both DataFrames can have arbitrary other columns. Those columns can represent vertex and edge attributes.
"""

sc = SparkContext("local[*]")
sqlContext = SQLContext(sc)

# create vertices
vertices = sqlContext.createDataFrame([
  ("a", "Alice", 34),
  ("b", "Bob", 36),
  ("c", "Charlie", 30),
  ("d", "David", 29),
  ("e", "Esther", 32),
  ("f", "Fanny", 36),
  ("g", "Gabby", 60)],
  ["id", "name", "age"])

# edges
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

# Let's create a graph from these vertices and these edges:
g = GraphFrame(vertices, edges)
display("a graph example", g)

# # This example graph also comes with the GraphFrames package.
# from graphframes.examples import Graphs
# same_g = Graphs(sqlContext).friends()
# display("a graph example",same_g)
#
# """
# Basic graph and DataFrame queries
# GraphFrames provide several simple graph queries, such as node degree.
#
# Also, since GraphFrames represent graphs as pairs of vertex and edge DataFrames, it is easy to make powerful queries directly on the vertex and edge DataFrames. Those DataFrames are made available as vertices and edges fields in the GraphFrame.
# """
#
# # display
# display("vertices:")
# g.vertices.show()
#
# display("edges:")
# g.edges.show()
#
# # The incoming degree of the vertices:
# g.inDegrees.show()
# g.outDegrees.show()
# g.degrees.show()
#
# # find the age of the youngest person in the graph
# youngest = g.vertices.groupBy().min("age")
# print("the age of the youngest person:", youngest.show())
#
#
# # count the number of 'follow' relationships in the graph:
# numFollows = g.edges.filter("relationship = 'follow'").count()
# print("The number of follow edges is: ", numFollows)
#
# """
# Motif finding
# Using motifs you can build more complex relationships involving edges and vertices. The following cell finds the pairs of vertices with edges in both directions between them. The result is a DataFrame, in which the column names are given by the motif keys.
# """
# # Search for pairs of vertices with edges in both directions between them.
# motifs = g.find("(a)-[e]->(b); (b)-[e2]->(a)")
# print("pairs of vertices with edges in both directions between them:\n")
# motifs.show()
#
# # find all the reciprocal relationships in which one person is older than 30
# filtered = motifs.filter("b.age > 30 or a.age > 30")
# print(" all the reciprocal relationships in which one person is older than 30:\n")
# filtered.show()
#
# """
# Stateful queries ??
# Most motif queries are stateless and simple to express, as in the examples above. The next example demonstrates a more complex query that carries state along a path in the motif. Such queries can be expressed by combining GraphFrame motif finding with filters on the result where the filters use sequence operations to operate over DataFrame columns.
#
# For example, suppose you want to identify a chain of 4 vertices with some property defined by a sequence of functions. That is, among chains of 4 vertices a->b->c->d, identify the subset of chains matching this complex filter:
#
# Initialize state on path.
# Update state based on vertex a.
# Update state based on vertex b.
# Etc. for c and d.
# If final state matches some condition, then the filter accepts the chain. The below code snippets demonstrate this process, where we identify chains of 4 vertices such that at least 2 of the 3 edges are “friend” relationships. In this example, the state is the current count of “friend” edges; in general, it could be any DataFrame Column.
#
# """
#
# # identify chains of 4 vertices such that at least 2 of the 3 edges are “friend” relationships.
# # In this example, the state is the current count of “friend” edges; in general, it could be any DataFrame Column
#
# # Find chains of 4 vertices.
# chain4 = g.find("(a)-[ab]->(b); (b)-[bc]->(c); (c)-[cd]->(d)")
#
# # Query on sequence, with state (cnt)
# #  (a) Define method for updating state given the next element of the motif.
# def cumFriends(cnt, edge):
#   relationship = col(edge)["relationship"]
#   return when(relationship == "friend", cnt + 1).otherwise(cnt)
#
#
# #  (b) Use sequence operation to apply method to sequence of elements in motif.
# #   In this case, the elements are the 3 edges.
# edges = ["ab", "bc", "cd"]
# numFriends = reduce(cumFriends, edges, lit(0))
#
# chainWith2Friends2 = chain4.withColumn("num_friends", numFriends).where(numFriends >= 2)
# print("chain of 4 vertices such that at least 2 of the 3 edges are “friend” relationships:\n")
# chainWith2Friends2.show()
#
# """
# Subgraphs
# GraphFrames provides APIs for building subgraphs by filtering on edges and vertices. These filters can be composed together,
# """
#
# # for example the following subgraph only includes people who are more than 30 years old and have friends who are more than 30 years old.
# g2 = g.filterEdges("relationship = 'friend'").filterVertices("age > 30").dropIsolatedVertices()
# print("people who are more than 30 years old and have friends who are more than 30 years old:\n")
# g2.vertices.show()
# g2.edges.show()
#
# """
# Standard graph algorithms
# GraphFrames comes with a number of standard graph algorithms built in:
#
# Breadth-first search (BFS)
# Connected components
# Strongly connected components
# Label Propagation Algorithm (LPA)
# PageRank (regular and personalized)
# Shortest paths
# Triangle count
# """
#
# # Breadth-first search (BFS)
# # Search from "Esther" for users of age < 32.
# paths = g.bfs("name = 'Esther'", "age < 32")
# display("BFS from \"Esther\" for users of age < 32")
# paths.show()
#
# # path that has end points less than 32 yrs old and all edges are not friends
# filteredPaths = g.bfs(
#   fromExpr = "name = 'Esther'",
#   toExpr = "age < 32",
#   edgeFilter = "relationship != 'friend'",
#   maxPathLength = 3)
# display("filtered Paths: \n")
# filteredPaths.show()
#
# # Connected components
# # Compute the connected component membership of each vertex and return a DataFrame with each vertex assigned a component ID. The GraphFrames connected components implementation can take advantage of checkpointing to improve performance.
#
# sc.setCheckpointDir("/tmp/graphframes-example-connected-components")
# result = g.connectedComponents()
# display("connected components:\n")
# result.show()
#
#
# # Strongly connected components
# # Compute the strongly connected component (SCC) of each vertex and return a DataFrame with each vertex assigned to the SCC containing that vertex.
# result = g.stronglyConnectedComponents(maxIter=10)
# display("Strongly connected components:\n")
# result.show()

"""
Label Propagation
Run static Label Propagation Algorithm for detecting communities in networks.

Each node in the network is initially assigned to its own community. At every superstep, nodes send their community affiliation to all neighbors and update their state to the most frequent community affiliation of incoming messages.

LPA is a standard community detection algorithm for graphs. It is very inexpensive computationally, although (1) convergence is not guaranteed and (2) one can end up with trivial solutions (all nodes are identified into a single community).
"""
result = g.labelPropagation(maxIter=20)
display("Label Propagation Algorithm for detecting communities\n")
result.show()


"""
PageRank
Identify important vertices in a graph based on connections.
"""
results = g.pageRank(resetProbability=0.15, tol=0.01)
display("vertice pagerank: \n")
results.vertices.show()

display("edge pagerank: \n")
results.edges.show()

# Run PageRank for a fixed number of iterations.
g.pageRank(resetProbability=0.15, maxIter=10)

# Run PageRank personalized for vertex "a"
g.pageRank(resetProbability=0.15, maxIter=10, sourceId="a")

"""
Shortest paths
Computes shortest paths to the given set of landmark vertices, where landmarks are specified by vertex ID.
"""
results = g.shortestPaths(landmarks=["a", "d"])
display("shortest path to set (a,d):")
results.show()

"""
Triangle count
Computes the number of triangles passing through each vertex.
"""
results = g.triangleCount()
display("triangle count")
results.show()