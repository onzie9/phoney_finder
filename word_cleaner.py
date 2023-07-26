import pickle

words = open("words.txt", 'r')
lines = words.readlines()

ls = []

for w in lines:
    x = w.split(" ")[0]
    ls.append(x)

with open('cleaned_words.pkl', 'wb') as f:
    pickle.dump(ls, f)

words.close()