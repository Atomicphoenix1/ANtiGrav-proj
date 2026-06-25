import numpy as n
import random as r
import string as s
i=j=0
pasta=int(input("gimme ur pasta:"))
m=input("letters: ").lower()
H=input("gimme ur H crook with spaces: ").split()
for i in range(len(H)):
 H[i]=int(H[i])
m=list(m)
O= list(s.ascii_lowercase)
O.insert(0,' ')
A=[]
F=[]
for j in range(len(m)) : 
     for i in range(len(O)):
      if O[i] in m[j]:
       a=i+26*H[j]
       A.append(a)
      
      
      i=i+1
print(A)    
j=0  
for j in range(len(m)) : 
    
      jo=j
      f=(A[j]-3*jo-pasta)/5
      j=j+1
      F.append(f) 
print(F)
Fi=[]

for i in range(len(F)):
 for j in range(len(O)):  
     if F[i]==j:
      Fi.extend(O[j])
      j=j+1
i=i+1   
Fi=''.join(Fi)
print(Fi)

      
      
      
