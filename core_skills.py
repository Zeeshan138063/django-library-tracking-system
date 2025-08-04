import random
# rand_list =

# list_comprehension_below_10 =

# list_comprehension_below_10 =

"""
Create a list of 10 random numbers between 1 and 20.
Filter Numbers Below 10 (List Comprehension)
Filter Numbers Below 10 (Using filter)
"""
rand_list=[]
for i in range(10):
    rand_list.append(random.randint(1, 20))

print(rand_list)

# step 2
num_below_10 = [i for i in rand_list if i < 10]
print(num_below_10)

# step 3
filtered_list = list(filter( lambda x:x < 10, rand_list))
print(filtered_list)

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""