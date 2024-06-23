import numpy as np
import pandas as pd
import math
df=pd.read_csv('insurance.csv')
#print(df.columns)
nsmoker=[]
for i in range(0,df.shape[0]):
  if df.iloc[i]['smoker']=='yes':
        nsmoker.append(1)
  else:
    nsmoker.append(0)
df['num_smoker']=nsmoker
x=df[['age','bmi','num_smoker','children','charges']]
#print(x.columns)      
from sklearn.cluster import KMeans 
kmeans = KMeans(n_clusters=4, init='k-means++', random_state= 42)  
y_predict= kmeans.fit_predict(x.iloc[:1000]) 
c=kmeans.cluster_centers_
#print(round(c[0][0],2))

def caldist(x1,p):
    dist=0
    for i in range(0,5):
        dist=dist+pow((x1[i]-p[i]),2)
    return math.sqrt(dist)    
def find_group(rx,c):
    ans=0
    dist=pow(10,10)
    for i in range(0,4):
        ccd=caldist(rx,c[i])
        if ccd<dist:
          dist=ccd
          ans=i
    return {'centroid':ans+1,'group':ans}   
rrx=[60,31,0,0,5000]
print('The closest centroid is the centroid',find_group(rrx,c)['centroid'],' therefore this point belongs to group ',find_group(rrx,c)['group'])