f1 = frozenset({'100', '101'})
f2 = frozenset({'101', '102','100'})

if f1.issubset(f2):
    print('ok')
else:
    print('no')