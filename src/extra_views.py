from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.http import Http404, HttpResponse
from .forms import *
from .forms import MyForm
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from captcha.helpers import captcha_image_url
from datetime import datetime, date
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .helpers import send_otp_to_phone
import random
from twilio.rest import Client
import statistics
from pytz import timezone
import numpy as np
import pandas as pd
import math
from .models import *
from .serializers import *
from rest_framework import viewsets
# create views here

class AadharViewSet(viewsets.ModelViewSet):
    queryset = Aadhar.objects.all()
    serializer_class = AadharSerializer
def base_view(request):
    return render(request, 'base.html', {})


def base2_view(request):
    return render(request, 'base2.html', {})

def base1_view(request):
    return render(request, 'base1.html', {})


def contact_view(request):
    return render(request, 'contact.html', {})


def about_view(request):
    return render(request, 'about.html', {})


def calculateAge(dob):
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) <
                                   (dob.month, dob.day))
    m = today.month-dob.month
    d = today.day-dob.day
    finn_m = float(m*30.5)
    if today.month < dob.month:
        finn_m = finn_m*(-1)
    y = float(age*365.24)
    return y+finn_m+d

def Age_year(dob):
    dd=dob.split("-")
    dy=int(dd[0])
    dm=int(dd[1])
    ddy=int(dd[2][0:2])
    today = date.today()
    age = today.year - dy - ((today.month, today.day) <
                                   (dm, ddy))
    return age


def calculateMinute(ldd):
    dd=ldd.split("-")
    y=int(dd[0])
    m=int(dd[1]) 
    dy=int(dd[2][:2])
    h=int(dd[2][3:5])
    mi=int(dd[2][6:8])
    se= int(dd[2][9:11])
    dob=datetime(y,m,dy,h,mi,se)
    rn = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Kolkata'))
    yr = rn.year-dob.year
    mr = abs(rn.month-dob.month)
    dr = abs(rn.day-dob.day)
    hr = abs(rn.hour-dob.hour)
    mir=abs(rn.minute-dob.minute)
    return yr*365.24*24*60+mr*30.5*24*60+dr*24*60+hr*60+mir
def sv_interest(ldd,b):
    dif=calculateMinute(ldd)
    fin_dif=float(dif/4 or 0)
    interest=b*.03*(fin_dif/360) 
    return round(float(interest or 0),2)
def calculateHour(dob):
    rn = datetime.now(timezone('UTC')).astimezone(timezone('Asia/Kolkata'))
    y = rn.year-dob.year
    m = abs(rn.month-dob.month)
    d = abs(rn.day-dob.day)
    h = (rn.hour-dob.hour)
    return y*365.24*24+m*30.5*24+d*24+h


def rec_interest_cal(og, ldd, interest):
    dd = ldd.split("-")
    y = int(dd[0])
    m = int(dd[1])
    dy = int(dd[2][:2])
    h = int(dd[2][3:5])
    mi = int(dd[2][6:8])
    se = int(dd[2][9:11])
    th = calculateHour(datetime(y, m, dy, h, mi, se))
    unit = int(th/2)
    quart = int(unit/3)
    p=og
    inter=0
    for i in range(0, quart):
        pqi = 0
        mp = p
        for j in range(0, 3):
                pqi = pqi+((mp*interest)/1200)
                mp = mp+og
        p=mp+pqi-og
        inter=inter+pqi
        #inter=inter+pqi
    if quart<1 and unit>1:
        maturity=og*(unit+1) 
    elif unit==1:
        maturity=og+og     
    else:      
        maturity=inter+og*(unit+1)            
    return {'t_i':inter,'maturity':maturity}
# fraud detection

def fraud(username,login1,trans1,am1,typs1):
    typs2=int(float(typs1 or 0)* 1000)
    queryset=Accounts_list.objects.all()
    login=[]
    ts=[]
    transac=[]
    trans_am=[]
    for ins in queryset:
        if not ins.username==username and  float(ins.login_count or 0)>2 and float(ins.transac_count or 0)>6 and float(ins.transac_amount or 0)>7000:
            login.append(int(ins.login_count or 0))
            ts.append(int(float(ins.typing_speed or 0)* 1000))
            transac.append(int(ins.transac_count or 0))
            trans_am.append(int(ins.transac_amount or 0))       
    dic={'login':login,'trans':transac,'amount':trans_am,'ts':ts}
    x_train=pd.DataFrame(dic)
    pval=norm_prob(x_train,estimate_mean_var(x_train)['mu'],estimate_mean_var(x_train)['stdev'])
    #selecting threshold
    pval.sort()
    ep=[]
    for i in pval:
        ep.append(int(str(i).split('e')[1][1:]))
    em=int(str(min(pval)).split('e')[1][1:])
    threshold=threshold=math.pow(10,em*(-1))
    
    curr_p=cal_prob(int(login1 or 0),int(trans1 or 0),int(am1 or 0),typs2,estimate_mean_var(x_train)['mu'],estimate_mean_var(x_train)['stdev'])
    print(curr_p)
    print(threshold)
    if curr_p<threshold:
        return True
    return False

def estimate_mean_var(x):
  mu=1/x.shape[0]*np.sum(x,axis=0)
  var=(1 / x.shape[0]) * np.sum((x - mu) ** 2, axis = 0)
  stdev=np.sqrt(var)
  return {'mu':mu,'var':var,'stdev':stdev}
# calculating probability for all rows
def norm_prob(x,mu,stdev):
  p=[]
  t=x.columns
  for i in range(0,x.shape[0]):
    prob=1
    for j in range(0,len(t)):
      norm=(1/(1.414*1.772*stdev[j]))*math.exp((((x.iloc[i][t[j]]-mu[j])/stdev[j])**2)*.5*(-1))
      prob=prob*norm
    p.append(prob)
  return p  

# calculating probability for one row
def cal_prob(login,trans,amount,typs,mu,stdev):
    l=[login,trans,amount,typs] 
    prob=1
    for j in range(0,len(l)):
      norm=(1/(1.414*1.772*stdev[j]))*math.exp((((l[j]-mu[j])/stdev[j])**2)*.5*(-1))
      prob=prob*norm
    return prob    
# end of fraud detection for now
def calculate_day(ldd):
    dd = ldd.split("-")
    y = int(dd[0])
    m = int(dd[1])
    dy = int(dd[2][:2])
    today = date.today()
    dob=date(y,m,dy)
    age = today.year - dob.year
    m = today.month-dob.month
    d = abs(today.day-dob.day)
    finn_m = float(m*30.5)
    if today.month < dob.month:
        finn_m = finn_m*(-1)      
    y = float(age*365.24)
    return y+finn_m+d
def scheme_view(request):
        queryset=Scheme.objects.all()
        context={
            "schemes":queryset
        }
        return render(request,'scheme.html',context)
def scheme_detail_view(request,scheme):
        query=Scheme.objects.get(id=scheme)
        context={
            "schemes":query
        }
        return render(request,'scheme-detail.html',context)