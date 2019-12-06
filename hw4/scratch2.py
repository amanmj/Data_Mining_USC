graph2 = {'A': ['B', 'C'],
         'B': ['A', 'D', 'C'],
         'C': ['A', 'B'],
         'D': ['B','E','F','G'],
         'E': ['D', 'F'],
         'F': ['D', 'E','G'],
         'G': ['D','F']}
print(graph2)

"""
For set
"""
def dfs(graph, start):
    visited, stack = set(), [start]
    while stack:
        vertex = stack.pop()
        if vertex not in visited:
            visited.add(vertex)
            stack.extend(graph[vertex] - visited)
    return visited

def dfs_paths(graph, start, goal, path=None):
    if path is None:
        path = [start]
    if start == goal:
        yield path
    for next in graph[start] - set(path):
        yield from dfs_paths(graph, next, goal, path + [next])

def bfs(graph, start):
    visited, queue = set(), [start]
    while queue:
        vertex = queue.pop(0)
        if vertex not in visited:
            visited.add(vertex)
            queue.extend(graph[vertex] - visited)
    return visited


def bfs_paths(graph, start, goal):
    queue = [(start, [start])]
    while queue:
        (vertex, path) = queue.pop(0)
        for next in graph[vertex] - set(path):
            if next == goal:
                yield path + [next]
            else:
                queue.append((next, path + [next]))

"""
FOR LIST
"""
def dfs2(graph, start):
    visited, stack = [], [start]
    while stack:
        vertex = stack.pop() # stack pop newest element
        if vertex not in visited:
            visited.append(vertex)
            stack.extend(Diff(graph[vertex], visited))
    return visited

def bfs2(graph, start):
    visited, queue = [], [start]
    while queue:
        vertex = queue.pop(0) # queue pop oldest element
        if vertex not in visited:
            visited.append(vertex)
            queue.extend(set(graph[vertex]) - set(visited))
    return visited

def dfs_paths2(graph, start, goal, path=None):
    if path is None:
        path = [start]
    if start == goal:
        yield path
    for next in set(graph[start])-set(path):
        yield from dfs_paths2(graph, next, goal, path + [next])

def bfs_paths2(graph, start, goal):
    queue = [(start, [start])]
    while queue:
        (vertex, path) = queue.pop(0)
        for next in set(graph[vertex]) - set(path):
            if next == goal:
                yield path + [next]
            else:
                queue.append((next, path + [next]))

def Diff(li1, li2):
    li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2]
    return li_dif

# print("bfs paths: ", list(bfs_paths(graph, 'A', 'F'))) # [['A', 'C', 'F'], ['A', 'B', 'E', 'F']]
print("bfs paths2: ", list(bfs_paths2(graph2, 'A', 'F'))) # [['A', 'C', 'F'], ['A', 'B', 'E', 'F']]

# print("dfs paths: ", list(dfs_paths(graph, 'B', 'F'))) # [['C', 'F'], ['C', 'A', 'B', 'E', 'F']]
print("dfs paths2: ", list(dfs_paths2(graph2, 'B', 'F'))) # [['C', 'F'], ['C', 'A', 'B', 'E', 'F']]

# print("bfs: ", bfs(graph, 'A')) # {'B', 'C', 'A', 'F', 'D', 'E'}
print("bfs2: ", bfs2(graph2, 'E')) # {'E', 'D', 'F', 'A', 'C', 'B'}

# print("dfs: ", dfs(graph, 'A')) # {'E', 'D', 'F', 'A', 'C', 'B'}
print("dfs2: ", dfs2(graph2, 'E')) # {'E', 'D', 'F', 'A', 'C', 'B'}

print({k: False for k in graph2})
