import numpy as n
import random as r
import string as s
i=j=0
mat1=([1],[1],[1])
f=[]
maty=([])  




O= list(s.ascii_lowercase)#  alphabets list
O.insert(0,' ')# adding space in list
# print(O)
m=input("letters: ").lower() # user writes the statement and the func lowers it to standardize case of letters
# print(m)
m=list(m) # listing letters of sentence
# print(m)

try:# past key method setup

    with open("hello.txt", "r") as past:
        # Read the past key or default to 0 if the file is empty or invalid
        content = past.read().strip()
        pasta = int(content) if content.isdigit() else 0
except FileNotFoundError:
    pasta = 0




for j in range(len(m)) : #each letter transform into the index of it in the O function of alphabet and goes through 3 operations making a 3-vector representing each letter and collected in a matrix
    for i in range(len(O)):
     if O[i] in m[j]:
      A=[i
         ,2*i+j+pasta
       ,2*i+2*j]
      maty.append(A)
      
      i=i+1
   
      
    j=j+1 
# print(maty)
i=0




  
res=n.dot(maty,mat1) # adding rows which represent each letter to reduce to n*1 matrix each row for coloumn
# print(res)

L= res.tolist()# matrix are arrays in lists so we need to transform to a list of lists

for sublist in L:  # transforming inner lists to normal list 
    f.extend(sublist)  
# print(f) 
H=[]
for i in range(len(f)):# dividing by number of alphabets to minimize numbers bigger than 26 so 27=1
   
   H.append(f[i]//26)
   f[i]=f[i]%26
   i=i+1
   
# print(f)   
i=j=0
F=[]


for i in range(len(f)):# converting numbers back to letters
 for j in range(len(O)):  
     if f[i]==j:
      F.extend(O[j])
      j=j+1
i=i+1   


new_key = str(f[0]) if f else "0"  # Use the first value of f or default to "0"
with open("hello.txt", "w") as past:
    past.write(new_key)
 

# print(F) 
# print(len(F))  
F=''.join(F)# joining list of letters to sentence
# F=F+" kk"
print ("encrypted:_",F)
print("new key is :",f[0])
print("past key :",pasta)
print(H)




# n2=int(input("number of rows"))
# n1=int(input(" mat2 rows :"))

# for i in range(n2):
#  a=input("gimme row %i :").split()
#  a= [int(a[j]) for j in range(len(a))]
 
#  mat1.append(a)
 


# for i in range(n1):
#   b=input("gimme row"  ).split()
#   b=[int(b[j]) for j in range(len(b))]
  
#   mat2.append(b)