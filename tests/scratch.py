#%%
def test():
    for frag1 in [[["a"], None]]:
        for frag2 in [[]]:
            yield frag1 + frag2

def test2():
    for frag1 in [[["a"], None]]:
        for frag2 in [[[], None]]:
            yield frag1

def test3():
    for frag1 in [[[], None]]:
        for frag2 in [[]]:
            yield frag1 + frag2

# %%
test()
for i in test():
    print(i)

# %%
test2()
for i in test2():
    print(i)

#%% 
test3()
for i in test3():
    print(i)


#%% 
def test4():
    for frag1 in [[["a"], None]]:
        for frag2 in [[]]:
            yield frag1
test4()
for i in test4():
    print(i)

# %%
print("hello")
# %%
[[]] == [[]]
# %%
for frag1 in [[["a"], None]]:
    for frag2 in [[]]:
        print(frag1 + frag2)
# %%
['a'] + ['b']
# %%
a = ['a']
