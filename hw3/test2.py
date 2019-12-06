total_hashes = 100
ret = [float('Inf') for i in range(0,total_hashes)]
print(ret)

key = frozenset({"minh", "linh"})
keySorted = [sorted(tuple(key))]
print(keySorted)


def dict_update(acc,n):
    # update if acc
    if not isinstance(acc,dict):
        return n
    else:
        acc.update(n)
        return acc

c = [{'thai': 3}, {'thai': 4},{'vietnam': 2}]
for item in c:
    dict_update()