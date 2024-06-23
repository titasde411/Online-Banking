from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.http import HttpResponse
from .forms import *
from .forms import MyForm
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages, auth
from captcha.helpers import captcha_image_url
from datetime import datetime, timedelta, date
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .helpers import send_otp_to_phone
import random
from twilio.rest import Client
from django.urls import reverse
from django.views.decorators.cache import cache_control
# Import PDF Stuff
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from .extra_views import *
from .ml import *
import requests
# Create your views here.


def home_view(request):
    queryset = Scheme.objects.all()
    cap = ['Scheme1', 'Scheme2', 'Scheme3', 'Scheme4']
    l = []
    for i in range(0, len(queryset)):
        l.append(i)
    context = {
        'schemes': queryset,
        'cap': cap,
        'length': l
    }
    return render(request, 'home.html', context)


def reg_view(request):
    form = Photo(request.POST, request.FILES)
    username = ""
    f = 0
    ms = False
    if request.method == "POST":
        name = request.POST['name']
        Date_of_birth = request.POST['Date_of_birth']
        marital_status = request.POST.get('marital_status')
        Address = request.POST['Address']
        aadhar = request.POST['aadhar']
        username = request.POST['username']
        password = make_password(request.POST['password'])
        secret_question = request.POST['secret_question']
        email = request.POST['email']
        Mobile_number = request.POST['Mobile_number']
        img = request.FILES.get('img')
        otp = random.randint(1000, 9999)
        form = Photo(request.POST, request.FILES)
        queryset = Accounts_list.objects.all()
        if marital_status == "on":
            ms = True
        for instance in queryset:
            if username == instance.username:
                f = 1

                break
        if f == 1:
            return HttpResponse("username already exists")

        else:
            checkpassword = check_password(request.POST['password'], password)
            resp=requests.get('http://127.0.0.1:8000/aadharaadhar/').json()
            ch=False
            print(resp['data'][0])
            for i in resp['data']:
                 if i['attributes']['aadhar_no']==aadhar:
                      if i['attributes']['name']==name and i['attributes']['address']==Address:
                           ch=True
            if ch==False:
                 return HttpResponse('aadhar details are wrong')  
            else:             
                data = Accounts_list(name=name, Date_of_birth=Date_of_birth, marital_status=ms, Address=Address, aadhar=aadhar, username=username, password=password,
                    secret_question=secret_question, email=email, Mobile_number=Mobile_number, otp=str(otp), image=img,last_login_date=datetime.now(),is_aadhar_verified=True)
                data.save()
                data.accounts.create(account_type="Savings", username=username, creation_date=str(
                    datetime.now()), last_t_date=str(datetime.now()), interest_rate=3)
                data.save()
            print(checkpassword)

    if form.is_valid():
        pass
    else:
        form = Photo(request.POST, request.FILES)
    context = {
        'form': form
    }
    return render(request, 'reg.html', {})
# @cache_control(no_cache=True, must_revalidate=True ,no_store=True)


def login_view(request):
        queryset = Accounts_list.objects.all()
        form = MyForm(request.POST)
        un = []
        human = False
        global uname
        uname = ""
        pass1 = ""
        k = 0
        speed=0
        neg=False
        f=False
        for instance in queryset:
            un.append(instance.username)

        if request.method == "POST":
            uname = request.POST['username']
            pass1 = request.POST['password']
            speed=request.POST.get('count')
            if form.is_valid():
                human = True
                print("success")
            else:
                form = MyForm(request.POST)
                print("fail")
        if uname in un and form.is_valid():
            k = 1
            print(uname)
            obj = Accounts_list.objects.get(username=uname)
            checkpassword = check_password(pass1, obj.password)
            if obj.is_phone_verified == False:
                return redirect('verify')
            if obj.is_fraud:
                 return HttpResponse("account deactivated")
            elif obj.is_phone_verified == True:
                if checkpassword and not obj.is_fraud:
                    # messages.error(request, "login unsuccessful" )
                        request.session["uid"] = request.POST["username"]
                        obj.typing_speed=float(speed or 0)
                        obj.save()
                        context = {
                    "user": obj,
                    "neg":neg,
                    "f":f
                            }
                        # for fixed deposit account being matured
                        accset = obj.accounts.all()
                        query = obj.accounts.get(account_type="Savings")
                        sb=float(query.balance or 0)
                        print(query.creation_date)
                        #counting login_counts
                        hd=calculate_day(str(obj.last_login_date))
                        if hd>=1:
                             obj.login_count=0
                             obj.last_login_date=datetime.now()
                             obj.save()
                        elif hd<1:
                             obj.login_count=int(obj.login_count or 0)+1
                             obj.save()     
                        for i in range(0, len(accset)):
                            if accset[i].account_type == "Fixed-Deposit" or accset[i].account_type == "Recurring":
                                dob = str(accset[i].creation_date)
                                dd = dob.split("-")
                                year = int(dd[0])
                                month = int(dd[1])
                                day = int(dd[2][:2])
                                dif = calculateAge(date(year, month, day))
                                fine=0
                                resi=0
                                if dif>=float(accset[i].Duration or 0):
                                                if accset[i].account_type == "Recurring": #calculating fine and residual amount for rd
                                                     c_no_deposit=int(accset[i].Duration or 0)*12
                                                     if c_no_deposit>int(accset[i].total_no_deposit or 0):
                                                        k=c_no_deposit-int(accset[i].total_no_deposit or 0)
                                                        fine=1.5*(float(accset[i].og_balance or 0)/100)*k
                                                        resi=float(accset[i].og_balance or 0)*k
                                                        accset[i].fine=fine
                                                        accset[i].resi=resi
                                                        accset[i].save()
                                                if (fine+resi)>float(sb or 0) and not accset[i].is_matured and not accset[i].is_deleted:
                                                    accset[i].is_stuck=True
                                                    accset[i].save()
                                                if (fine+resi)<=float(sb or 0)and not accset[i].is_matured and not accset[i].is_deleted:    
                                                     accset[i].is_matured=True
                                                     accset[i].save()                          
                                                if not accset[i].is_added_to_savings and accset[i].is_stuck!=True and not accset[i].is_deleted:
                                                    f_b=float(query.balance or 0)+float(accset[i].Maturity_amount or 0)-fine-resi
                                                    query.balance=f_b
                                                    query.transactions.create(transaction_type="Credit",amount=accset[i].Maturity_amount,Date_time=datetime.now(),oppo_acc=accset[i].account_no)
                                                    accset[i].is_added_to_savings=True
                                                    accset[i].save( )
                                                    dob1=str(query.last_t_date)
                                                    i_p=sv_interest(dob1,sb)
                                                    query.interest=float(query.interest or 0)+i_p
                                                    query.balance=float(query.balance or 0)+i_p
                                                    query.transactions.create(transaction_type="interest credited",amount=i_p,Date_time=datetime.now(),oppo_acc=query.account_no)
                                                    if fine>0:
                                                         query.transactions.create(transaction_type="dedit",amount=fine,Date_time=datetime.now(),oppo_acc=accset[i].account_no)
                                                    if resi>0:
                                                         query.transactions.create(transaction_type="dedit",amount=resi,Date_time=datetime.now(),oppo_acc=accset[i].account_no)
                                                    accset[i].is_added_to_savings=True     
                                                    query.save()
                                # for recurring depositing after every two hours                    
                                elif dif<float(accset[i].Duration or 0) and  accset[i].account_type=="Recurring":
                                       if not accset[i].is_stuck and not accset[i].is_deleted:
                                            da=str(accset[i].last_deposit_time)
                                            dd=da.split("-")
                                            y=int(dd[0])
                                            m=int(dd[1]) 
                                            dy=int(dd[2][:2])
                                            h=int(dd[2][3:5])
                                            mi=int(dd[2][6:8])
                                            se= int(dd[2][9:11])
                                            th=calculateHour(datetime(y,m,dy,h,mi,se))
                                            inter=0
                                            unit=int(th/2)
                                            am=float(accset[i].og_balance or 0)*unit
                                            nunit=unit
                                            if unit>=1 and unit<2:
                                                        if float(query.balance or 0)>am and accset[i].first_one_paid!=True:
                                                            accset[i].balance=float(accset[i].balance or 0)+am
                                                            accset[i].first_one_paid=True 
                                                            accset[i].total_no_deposit=float(accset[i].total_no_deposit or 0)+nunit
                                                            accset[i].save()
                                                            ldd=str(query.last_t_date)
                                                            i_p=sv_interest(ldd,float(query.balance or 0))
                                                            query.balance=float(query.balance or 0)-am+i_p
                                                            query.interest=float(query.interest or 0)+i_p
                                                            query.transactions.create(transaction_type="interest credited",amount=i_p,Date_time=datetime.now(),oppo_acc=query.account_no)
                                                            query.transactions.create(transaction_type="dedit",amount=am,Date_time=datetime.now(),oppo_acc=accset[i].account_no)
                                                            query.last_t_date=datetime.now()
                                                            query.save()
                                            elif unit<3 and unit>1:
                                                        if accset[i].first_one_paid==True:
                                                            am=am-float(accset[i].og_balance or 0)
                                                            nunit=nunit-1
                                                        if float(query.balance or 0) >=am and accset[i].first_quarter_paid!=True:    
                                                            accset[i].balance=float(accset[i].balance or 0)+am
                                                            accset[i].first_quarter_paid=True 
                                                            accset[i].total_no_deposit=float(accset[i].total_no_deposit or 0)+nunit
                                                            accset[i].save() 
                                                            ldd=str(query.last_t_date)
                                                            i_p=sv_interest(ldd,float(query.balance or 0))
                                                            query.balance=float(query.balance or 0)-am+i_p
                                                            query.interest=float(query.interest or 0)+i_p
                                                            query.transactions.create(transaction_type="interest credited",amount=i_p,Date_time=datetime.now(),oppo_acc=query.account_no)
                                                            query.transactions.create(transaction_type="debit",amount=am,Date_time=datetime.now(),oppo_acc=accset[i].account_no)
                                                            query.last_t_date=datetime.now()
                                                            query.save()                                                                                                                                                   
                                            elif unit>=3:
                                                    if accset[i].first_quarter_paid:
                                                            am=am-2*float(accset[i].og_balance or 0)  
                                                            nunit=nunit-2 
                                                    inter=rec_interest_cal(int(accset[i].og_balance),str(accset[i].creation_date),float(accset[i].interest_rate))['t_i']
                                                    accset[i].interest=inter
                                                    if float(query.balance or 0)>am:  
                                                            accset[i].total_no_deposit=float(accset[i].total_no_deposit or 0)+nunit
                                                            accset[i].balance=float(accset[i].balance or 0)+am
                                                            accset[i].last_deposit_time=datetime.now()
                                                            accset[i].first_one_paid=False
                                                            accset[i].first_quarter_paid=False
                                                            accset[i].save()  
                                                            ldd=str(query.last_t_date)
                                                            i_p=sv_interest(ldd,float(query.balance or 0))
                                                            query.balance=float(query.balance or 0)-am+i_p
                                                            query.interest=float(query.interest or 0)+i_p
                                                            query.transactions.create(transaction_type="interest credited",amount=i_p,Date_time=datetime.now(),oppo_acc=query.account_no)
                                                            query.transactions.create(transaction_type="debit",amount=am,Date_time=datetime.now(),oppo_acc=accset[i].account_no)
                                                            query.last_t_date=datetime.now()
                                                            query.save()                                                                                          
                        return redirect('profile',context)
                

        # # elif k!=1:
        # #      messages.error(request, "username does not exist" )
        
        
        return render(request,'login.html',{"f":f,"form":form})
def profile_view(request,my_id):
    my_id=uname
    obj=Accounts_list.objects.get(username=my_id)
    query=obj.accounts.get(account_type="Savings")
    ac=obj.accounts.all()
    fd=[]
    fdb=0
    savings=[]
    sb=0
    rd=[]
    rdb=0
    for ins in ac:
        if ins.account_type=="Fixed-Deposit":
            fd.append(ins)
            if  not ins.is_matured and not ins.is_deleted:
                fdb+=int(ins.balance or 0)
        if ins.account_type=="Savings":
            savings.append(ins) 
            sb+=int(ins.balance or 0)
        if ins.account_type=="Recurring":
            rd.append(ins)
            if not ins.is_matured and not ins.is_deleted and not ins.is_stuck:
                rdb+=int(ins.balance or 0)
            if float(ins.resi or 0)+float(ins.fine or 0) < float(query.balance or 0) and ins.is_stuck==True:
                 i_p=sv_interest(str(query.last_t_date),float(query.balance or 0)) 
                 query.balance=float(query.balance or 0)-float(ins.resi or 0)-float(ins.fine or 0)+i_p
                 query.transactions.create(transaction_type="interest credited",amount=i_p,Date_time=datetime.now(),oppo_acc=query.account_no)
                 query.transactions.create(transaction_type="debit",amount=float(ins.resi or 0)+float(ins.fine or 0),Date_time=datetime.now(),oppo_acc=ins.account_no)
                 query.save()
                 ins.is_stuck=False
                 ins.fine=0
                 ins.resi=0
                 ins.save()
                 if ins.is_deleted and not ins.is_added_to_savings:
                           ins.is_added_to_savings=True
                           query.balance=float(query.balance or 0)+float(ins.delete_ma or 0)
                           query.transactions.create(transaction_type="credit",amount=float(ins.delete_ma or 0),Date_time=datetime.now(),oppo_acc=ins.account_no)
                           ins.save()
                           query.save()                      
                 dob = str(ins.creation_date)
                 dd = dob.split("-")
                 year = int(dd[0])
                 month = int(dd[1])
                 day = int(dd[2][:2])
                 dif = calculateAge(date(year, month, day))
                 if dif>float(ins.Duration or 0):
                      if not ins.is_deleted and not ins.is_added_to_savings:
                           ins.is_matured=True
                           ins.is_added_to_savings=True
                           query.balance=float(query.balance or 0)+float(ins.Maturity_amount or 0)
                           query.transactions.create(transaction_type="credit",amount=float(ins.Maturity_amount or 0),Date_time=datetime.now(),oppo_acc=ins.account_no)
                           ins.save()
                           query.save()

                                

    # accs=[]
    # for instance in obj.accounts:
    #     accs.append(instance)
    queryset=obj.accounts.all()
    query=obj.accounts.get(account_type="Savings")
   # print(query.account_no)
    context={
        'obj':obj,
        'accs':queryset,
        'uname':obj.username,
        'savings':savings,
        'fd':fd,
        'rd':rd,
        'fdb':fdb,
        'rdb':rdb,
        'sb':sb,
    }
    return render(request,'profile.html',context)
def withdraw_view(request,my_acc):
    withdraw = 0
    racc=my_acc
    rttype="Credit"
    gttype="Debit"
    receipt=""
    dic=""
    dt=datetime.now()
    obj1=Accounts_list.objects.get(username=uname)
    context={}
    if request.method=="POST":
        withdraw=request.POST['withdraw']
        racc=request.POST['racc']
        receipt=request.POST.get('receipt')
        dic=str(racc)+" "+str(withdraw)+" "+str(dt)
        context={'dic':str(racc)+" "+str(withdraw)+" "+str(datetime.now()),
                 'acc':racc,
                 'amount':withdraw,
                 'time':datetime.now(),
                 'name':uname,
                 
                 }    
    query=Accounts.objects.get(account_no=my_acc)
    query1=Accounts.objects.get(account_no=racc)
    hd=calculate_day(str(obj1.last_login_date))
    if query1.account_type!="Savings":
        return HttpResponse("Money can only be sent to another savings account")
    b=int(query.balance)
    b1=int(query1.balance)
    print(query.creation_date)
    if b< float(withdraw):
        return HttpResponse("Not enough balance") 
    elif fraud(uname,obj1.login_count,obj1.transac_count,obj1.transac_amount,obj1.typing_speed):
         print(fraud(uname,obj1.login_count,obj1.transac_count,obj1.transac_amount,obj1.typing_speed))
         obj1.is_fraud=True
         obj1.save()
         return redirect('fraud')
    elif hd>=1 and not obj1.is_fraud:
         obj1.transac_count=0
         obj1.transac_amount=0
         obj1.save()
    elif hd<1 and not obj1.is_fraud:
         obj1.transac_count=int(obj1.transac_count)+1
         obj1.transac_amount=int(obj1.transac_amount)+int(withdraw)
         obj1.save()   
    
    if float(withdraw)>0:
            dob=str(query.last_t_date)
            i_p=sv_interest(dob,b)
            dob1=str(query1.last_t_date)
            i_p1=sv_interest(dob1,b1)
            b=b-int(withdraw)
            query.balance=b
            b1=b1+int(withdraw)
            query1.balance=b1
            query.balance=float(query.balance or 0)+i_p
            query.interest=float(query.interest or 0)+i_p
            query1.interest=float(query1.interest or 0)+i_p1
            query1.balance=float(query1.balance or 0)+i_p1
            query.transactions.create(transaction_type="interest credited",amount=i_p,Date_time=dt,oppo_acc=query.account_no)
            query.transactions.create(transaction_type=gttype,amount=float(withdraw),Date_time=dt,oppo_acc=racc)
            query1.transactions.create(transaction_type="interest credited",amount=i_p1,Date_time=dt,oppo_acc=query1.account_no)
            query1.transactions.create(transaction_type=rttype,amount=float(withdraw),Date_time=dt,oppo_acc=my_acc)
            query.last_t_date=datetime.now()
            query1.last_t_date=datetime.now()
            query.save()
            query1.save()
            
            context['account']=query
    if receipt=="Yes":
        return redirect(reverse('receipt',kwargs={'my_dic':dic}))
    return render(request,'withdraw.html',{'acc':my_acc,'account':query,'name':uname})
def receipt_view(request,my_dic):
        det=my_dic.split(" ")
        query=Accounts.objects.get(account_no=det[0])
        tquery=query.transactions.all()
        id=tquery.last().id
        print(tquery.last().id)
    # print(my_dic)
        # Create Bytestream buffer
        buf = io.BytesIO()
        # Create a canvas
        c = canvas.Canvas(buf, pagesize=letter, bottomup=0)
        
        c.drawString(50,750,'Payment Receipt') 
        # Create a text object
        textob = c.beginText()
        textob.setTextOrigin(inch, inch)
        textob.setFont("Helvetica", 14)
        # Create blank list
        lines = [
            "Transaction id: "+str(id),
            "amount: "+str(det[1]),
            "to account no "+str(det[0]),
            "date: "+str(det[2]),
            "at "+str(det[3][:5])
        ]
        for line in lines:
                textob.textLine(line)
                        
        c.drawText(textob)
        c.showPage()
        c.save()
        buf.seek(0)

        return FileResponse(buf, filename='receipt.pdf')
def deposit_view(request,my_acc):
    query=Accounts.objects.get(account_no=my_acc)
    deposit = 0
    if request.method=="POST":
        deposit=request.POST.get('deposit')
    if deposit:
        dob=str(query.last_t_date)
        i_p=sv_interest(dob,float(query.balance or 0))
        query.interest=float(query.interest or 0)+i_p
        query.balance=float(query.balance or 0)+i_p
        query.balance=float(query.balance or 0)+float(deposit or 0)
        query.last_t_date=datetime.now()
        query.transactions.create(transaction_type="interest credited",amount=i_p,Date_time=datetime.now(),oppo_acc=my_acc)
        query.transactions.create(transaction_type="Credit",amount=float(deposit),Date_time=datetime.now(),oppo_acc=my_acc)
        query.save()  
    return render(request,'deposit.html',{'name':uname,'balance':query.balance})

def delete_view(request,my_acc):
    obj=Accounts.objects.get(account_no=my_acc)
    query=Accounts_list.objects.get(username=uname)
    queryset=query.accounts.all()
    dob=str(obj.creation_date)
    dd=dob.split("-")
    year=int(dd[0])
    month=int(dd[1])
    day=int(dd[2][:2])
    fd=False
    rd=False
    t=[]
    for instance in queryset:
        if instance.account_type=="Savings":
            t.append(instance)
    dif=calculateAge(date(year,month,day))
    penalty=0
    i_p_y=0
    interest=0
    if obj.account_type=="Fixed-Deposit":
        i_p_y=(float(obj.interest_rate)/100)*float(obj.balance)
        interest=i_p_y*dif
        fd=True
        if dif<float(obj.Duration or 0):
            penalty=interest/100
            acc_val=float(obj.balance)+interest-penalty        
    elif obj.account_type=="Recurring": 
        rd=True 
        interest=rec_interest_cal(int(obj.og_balance or 0),str(obj.creation_date),float(obj.interest_rate or 0))['t_i'] 
        k=rec_interest_cal(int(obj.og_balance or 0),str(obj.creation_date),float(obj.interest_rate or 0))['maturity'] 
        if dif<float(obj.Duration)*365.24:
            penalty=interest/100
            acc_val=k-penalty
    da = str( obj.creation_date)
    dd=da.split("-")
    y=int(dd[0])
    m=int(dd[1]) 
    dy=int(dd[2][:2])
    h=int(dd[2][3:5])
    mi=int(dd[2][6:8])
    se= int(dd[2][9:11])
    th=calculateHour(datetime(y,m,dy,h,mi,se))
    fine=0
    resi=0
    k=0
    c_no_deposit=int(th/2)
    if c_no_deposit>int(obj.total_no_deposit or 0) and obj.account_type=="Recurring":
                    k=c_no_deposit-int(obj.total_no_deposit or 0)
                    fine=1.5*(float(obj.og_balance or 0)/100)*k
                    resi=float(obj.og_balance or 0)*k 
                    acc_val=acc_val-fine 
                    obj.fine=fine
                    obj.resi=resi
                    obj.save()      
    ans=""
    if request.method=="POST":
        ans=request.POST.get('ans')
    context={
            'acc':my_acc,
            'name':uname,
            'penalty':penalty,
            'acc_val':acc_val,
            'interest':float(obj.interest_rate),
            'balance':obj.balance,
            'ma':obj.Maturity_amount,
            'dura':obj.Duration,
            'cd':obj.creation_date,
            'md':str(obj.creation_date+timedelta(days=(int(obj.Duration))))[:10], 
            'k' :k,
            'fine' :fine,
            'resi' :resi,
            'fd'    :fd,
            'rd' :rd  ,
            'og':obj.og_balance
            
        }
    print(t[0].account_type)
    if ans=="Yes":
        dob1=str(t[0].last_t_date)
        i_p=sv_interest(dob1,float(t[0].balance or 0))
        if resi>float(t[0].balance or 0):
             obj.is_stuck=True
             obj.delete_ma=acc_val
             obj.save()
        obj.is_deleted=True
        obj.delete_ma=acc_val
        obj.save()
        if not obj.is_stuck:
            t[0].interest=float(t[0].interest or 0)+i_p
            t[0].balance=float(t[0].balance or 0)+i_p
            t[0].balance=float(t[0].balance)+acc_val-fine-resi
            t[0].transactions.create(transaction_type="Credit",amount=acc_val,Date_time=datetime.now(),oppo_acc=my_acc)
            t[0].transactions.create(transaction_type="interest credited",amount=i_p,Date_time=datetime.now(),oppo_acc=t[0].account_no)
            if fine>0 or resi>0:
                if fine>0:
                    t[0].transactions.create(transaction_type="dedit",amount=fine,Date_time=datetime.now(),oppo_acc=my_acc)
                if resi>0:
                    t[0].transactions.create(transaction_type="debit",amount=acc_val,Date_time=datetime.now(),oppo_acc=my_acc)     
            t[0].last_t_date=str(datetime.now())        
            t[0].save()
            obj.is_added_to_savings=True
            obj.save()
        hd=calculate_day(str(query.last_login_date))
        if hd<1:
             query.transac_count=int(query.transac_count or 0)+1
             query.save()  
        return redirect("delete_sure")
    return render(request,'delete.html',context)
def create_account_view(request):
    duration=0
    balance=0
    query=Accounts_list.objects.get(username=uname)
    queryset=query.accounts.all() 
    t=[]
    maturity=0
    for instance in queryset:
        if instance.account_type=="Savings":
            t.append(instance)       
    account_type=""
    if request.method=="POST":
        account_type=request.POST['account_type']
        balance=request.POST['balance']
        duration=request.POST['duration']
    interest=0
    if int(duration)<=3 and int(duration)>=1:
        interest=6 
    elif int(duration)<=5 and int(duration)>3:
        interest=7 
    elif int(duration)<=10 and int(duration)>5:
        interest=7.5             
    creation_date=datetime.now()
    if account_type=="Fixed-Deposit":
        i_p_y=(float(interest)/100)*float(balance or 0)
        maturity=round(int(balance or 0)+i_p_y*(float(duration or 0)+1),2)
    elif account_type=="Recurring" :
        p=int(balance)
        n=int(duration)
        for i in range(0,n*4):
            mp=p
            pqi=0
            for j in range(0,3):
                pqi=pqi+((mp*interest)/1200)
                mp=mp+int(balance)
            p=mp+pqi
        maturity=p-int(balance)       
    username=uname
    #data=Accounts(account_type=account_type,balance=balance,duration=duration,creation_date=creation_date,interest=interest,maturity=maturity,username=username)
    if float(balance or 0)>float(t[0].balance or 0):
        return HttpResponse("Not enough balance")
    if float(balance or 0)>0:
        obj=Accounts_list.objects.get(username=uname)
        obj.accounts.create(account_type=account_type,balance=balance,Duration=duration,creation_date=creation_date,interest_rate=interest,Maturity_amount=maturity,username=username,og_balance=balance,last_deposit_time=creation_date)
        obj.save()
        an=Accounts.objects.get(creation_date=creation_date)
        dob1=str(t[0].last_t_date) 
        i_p=sv_interest(dob1,float(t[0].balance or 0))
        if i_p>0:
            t[0].interest=float(t[0].interest or 0)+i_p
            t[0].balance=float(t[0].balance or 0)+i_p                        
        t[0].last_t_date=creation_date
        t[0].balance=float(t[0].balance or 0)-float(balance or 0)
        t[0].transactions.create(transaction_type="interest credited",amount=i_p,Date_time=datetime.now(),oppo_acc=t[0].account_no)
        t[0].transactions.create(transaction_type="Debit",amount=balance,Date_time=datetime.now(),oppo_acc=an.account_no)
        t[0].save()
        
    return render(request,'create_account.html',{'name':uname})
def view_account_view(request,my_acc):
    sv=False
    rd=False
    fd=False
    fine=0
    resi=0
    k=0    
    delete=False
    ob=Accounts.objects.get(account_no=my_acc)
    d=int(ob.Duration)
    if str(ob.account_type)=="Savings":
        sv=True
    elif str(ob.account_type)=="Fixed-Deposit":
        fd=True
    elif str(ob.account_type)=="Recurring":
        k=0
        dob = str(ob.creation_date)
        dd1 = dob.split("-")
        year = int(dd1[0])
        month = int(dd1[1])
        day = int(dd1[2][:2])
        dif = calculateAge(date(year, month, day))
        rd=True
        if dif>= float(ob.Duration or 0):
             k= float(ob.Duration or 0)*12- float(ob.total_no_deposit or 0)
        else:     
            da = str( ob.creation_date)
            dd=da.split("-")
            y=int(dd[0])
            m=int(dd[1]) 
            dy=int(dd[2][:2])
            h=int(dd[2][3:5])
            mi=int(dd[2][6:8])
            se= int(dd[2][9:11])
            th=calculateHour(datetime(y,m,dy,h,mi,se))
            c_no_deposit=int(th/2)    
            if c_no_deposit>int(ob.total_no_deposit or 0):
                        k=c_no_deposit-int(ob.total_no_deposit or 0)
                        fine=1.5*(float(ob.og_balance or 0)/100)*k         
    if ob.is_deleted:
         delete=True          
    context={
        'acc_no':ob.account_no,
        'acc_tp':ob.account_type,
        'balance':ob.balance,
        'interest':float(ob.interest_rate or 0),
        'ma':ob.Maturity_amount,
        'dura':ob.Duration,
        'cd':ob.creation_date,
        'name':uname,
        'sv':sv,
        'rd':rd,
        'fd':fd,
        'inter':ob.interest,
        'ltd':ob.last_t_date,
        'md':str(ob.creation_date+timedelta(days=(int(ob.Duration))))[:10],
        'og':ob.og_balance,
        'k':k,
        'fine':ob.fine,
        'delete_ma':ob.delete_ma,
        'delete':delete
    }
    # if ob.Duration:
    #     context['md']=str(ob.creation_date+timedelta(days=d))[:10],
    return render(request,'view_account.html',context)
def update_profile_view(request):
    obj=Accounts_list.objects.get(username=uname)
    form=Photo(request.POST,request.FILES)
    context={
        'name':obj.name,
        'dob':obj.Date_of_birth,
        'ms':obj.marital_status,
        'address':obj.Address,
        'aadhar':obj.aadhar,
        'sq':obj.secret_question,
        'email':obj.email,
        'contact':obj.Mobile_number
    }  
    name=""
    Date_of_birth= ""
    marital_status=None
    marital_status1=None
    Address= ""
    aadhar=0
    secret_question=""
    email=""
    Mobile_number=0
    image=""
    if request.method=="POST":
        name=request.POST['name']
        Date_of_birth= request.POST['Date_of_birth']
        marital_status=request.POST.get('marital_status')
        marital_status1=request.POST.get('marital_status1')
        Address= request.POST['Address']
        aadhar=request.POST['aadhar']
        secret_question=request.POST['secret_question']
        email=request.POST['email']
        Mobile_number=request.POST['Mobile_number']
        image=request.FILES.get('img')
        form=Photo(request.POST,request.FILES)
    if name:
        obj.name=name
    if Date_of_birth:
        obj.Date_of_birth=Date_of_birth
    if marital_status=="on":
        obj.marital_status=True
    if marital_status1=="on":
        obj.marital_status=False      
    if Address:
        obj.Address=Address
    if aadhar:
        obj.aadhar=aadhar
    if secret_question:
        obj.secret_question=secret_question
    if email:
        obj.email=email
    if Mobile_number:
        obj.Mobile_number=Mobile_number
    if image:
        obj.image=image
    obj.save() 
    if form.is_valid() :   
        form.save()  
    else:
        form=Photo(request.POST,request.FILES)            
    return render(request,'update_profile.html',context)
def transaction_view(request,my_acc):
    query=Accounts.objects.get(account_no=my_acc)
    context={
        'tr':query.transactions.all(),
        'name':uname
    }
    return render(request,'transaction.html',context)
def verify_view(request):
    ans=""
    if request.method=="POST":
        ans=request.POST['ans']
    if ans=="yes" :
        query=Accounts_list.objects.get(username=uname)
        ootp=query.otp
        mm_no=query.Mobile_number
        account_sid = "ACe1fb1198bf26799435ffc7d6166f545c"
        auth_token = "8f36db75c101fb804c61f0d9d5a6ec56"
        client = Client(account_sid, auth_token)
        message = client.messages.create(
         body="Hello from spit bank and your one time password for account verification is "+str(ootp),
         from_="+15856394846",
         to="+91"+str(mm_no)
            )
        print("message sent successfully")
        return redirect('verification')   
    return render(request,'verify.html',{})
def verification_view(request):
    gotp=""

    if request.method=="POST":
        gotp=request.POST.get('otp1', False)
    query=Accounts_list.objects.get(username=uname)
    if gotp==query.otp:
        query.is_phone_verified=True
        query.save()
        return HttpResponse('Phone number is verified')    
    return render(request,'verification.html',{})
def scheme1_view(request):
    return render(request,'scheme.html',{})
def fp1_view(request):
         em=""
         global f_em
         f_em=""
         queryset=Accounts_list.objects.all()
         em_list=[]
         for instance in queryset:
            em_list.append(instance.email)
         if request.method=="POST":
            em=request.POST.get('email')
         if em in em_list:
              f_em=em 
              context={
                  'em':f_em
              }
              return redirect('fp2')
         return render(request,'fp1.html',{})   
def fp2_view(request):
     my_em=f_em
     ob=Accounts_list.objects.get(email=my_em)
     context={
         'name':ob.name,
         'img':ob.image
     }
     ans=""
     if request.method=="POST":
         ans=request.POST.get('ans1')
         print(ans)
     if ans=="on" :
         return redirect('ask_sq')   
     return render(request,'fp2.html',context) 
def ask_sq_view(request) :
     my_em=f_em
     ob=Accounts_list.objects.get(email=my_em)
     sq=""
     if request.method=="POST":
         sq=request.POST.get('sq')
         if sq==ob.secret_question:
             return redirect('update-password')
     return render(request,'ask_sq.html',{})
def update_password_view(request):
     my_em=f_em
     ob=Accounts_list.objects.get(email=my_em)
     if request.method=="POST":
         password=make_password(request.POST['password'])
         ob.password=password
         ob.save()
         return redirect('login')
     return render(request,'update-password.html',{})  
def apply_scheme_view(request):
     obj=Accounts_list.objects.get(username=uname)
     queryset=obj.scheme_count.all()
     num=False
     
     if len(queryset)<1:
          num=True
     if num==False:     
        for ob in queryset: 
             u=0
             dd=str(ob.creation_date).split('-') 
             y=int(dd[0])
             m=int(dd[1])
             dy=int(dd[2][:2])
             h=int(dd[2][3:5])
             mi=int(dd[2][6:8])
             se=int(dd[2][9:11])
             th=calculateHour(datetime(y,m,dy,h,m,se))
             u=int(th/2) 
             print(u)
             if(u+1>float(ob.prem_pay_count or 0) and u>=1):
                  ob.rest_count=u-float(ob.prem_pay_count or 0) 
                  ob.save()
     age=Age_year(str(obj.Date_of_birth))
     bmi=0
     num_smoker=""
     noc=0
     charges=0
     g=-1
     ans=""
     if request.method=="POST":
          bmi=request.POST.get('bmi')
          num_smoker=request.POST.get('num_smoker')
          noc=request.POST.get('noc')
          charges=request.POST.get('charges')
          ans=request.POST.get('ans')
     if num_smoker=="yes":
        num_smoker=1    
     else:
          num_smoker=0
     rrx=[age,float(bmi or 0),num_smoker,int(noc or 0),float(charges or 0)]
     c=[[ 5.12976190e+01,  3.10891667e+01,  5.65476190e-02,
         1.13392857e+00,  1.14335135e+04],
       [ 4.03577982e+01,  3.51214679e+01,  9.81651376e-01,
         1.09174312e+00,  4.14598015e+04],
       [ 2.92750583e+01,  3.03575175e+01, -1.94289029e-16,
         1.01165501e+00,  4.22414208e+03],
       [ 4.30238095e+01,  2.83000397e+01,  5.55555556e-01,
         1.15873016e+00,  2.30382542e+04]]    
     g=find_group(rrx,c)['group']+1
     print('the group is ',g)
     context={
          'name':uname,
          'age':age,
          'num':num,
          'ins':queryset
     }
     if ans=="yes":
         return redirect(reverse('rec_scheme',kwargs={'scheme':g}))
     return render(request,'apply-scheme.html',context)
def rec_scheme_view(request,scheme):
     ob=Scheme.objects.get(id=scheme)
     query=Accounts_list.objects.get(username=uname)
     sch="Star-care"
     ans=""
     if request.method=="POST":
          sch=request.POST.get('ins')
          ans=request.POST.get('ans')
     obs=Scheme.objects.get(name=sch)
     creation_date=datetime.now()
     if ans=="Yes":
          query.scheme_count.create(name=sch,prem_pay_count=1,creation_date=creation_date,prem=obs.Annual_premium,last_prem_pay=creation_date)
          squery=query.scheme_count.get(creation_date=creation_date)
          acc=query.accounts.get(account_type="Savings")
          i_p=sv_interest(str(acc.last_t_date),float(acc.balance or 0))
          acc.balance=float(acc.balance or 0)+i_p-float(obs.Annual_premium or 0)
          acc.transactions.create(transaction_type="interest credited",amount=i_p,Date_time=datetime.now(),oppo_acc=acc.account_no)
          acc.transactions.create(transaction_type=obs.name,amount=obs.Annual_premium,Date_time=datetime.now(),oppo_acc=squery.id)
          acc.save()
          query.save()
     context={
          'schemes':ob,
          'name':uname
     }
     return render(request,'rec_scheme.html',context)
def summary_scheme_view(request,schid):
     sch=Scheme_count.objects.get(id=schid)
     scheme=Scheme.objects.get(name=sch.name)
     context={
          'scheme':sch,
          'name':uname,
          'sch_n':scheme
     }
     return render(request,'summary_scheme.html',context)
def pay_scheme_view(request,schid):
     sch=Scheme_count.objects.get(id=schid)
     ans=""
     sch_n=Scheme.objects.get(name=sch.name)
     obj=Accounts_list.objects.get(username=uname)
     acc=obj.accounts.get(account_type="Savings")
     if request.method=="POST":
          ans=request.POST.get('ans')
     if ans=="yes":
          k=float(sch.rest_count or 0)*float(sch_n.Annual_premium or 0)
          if k > float(acc.balance or 0):
               return HttpResponse('not enough balance') 
          else:
               sch.prem_pay_count=float(sch.prem_pay_count or 0)+float(sch.rest_count or 0)
               sch.rest_count=0
               sch.last_prem_pay=datetime.now()
               sch.save()
               i_p=sv_interest(str(acc.last_t_date),float(acc.balance or 0))  
               acc.transactions.create(transaction_type="interest credited",amount=i_p,Date_time=datetime.now(),oppo_acc=acc.account_no)
               acc.transactions.create(transaction_type=sch.name,amount=k,Date_time=datetime.now(),oppo_acc=sch.id)
               acc.balance=float(acc.balance or 0)+i_p
               acc.save()               
     context={
          'scheme':sch,
          'name':uname
     }
     return render(request,'pay_scheme.html',context)
def req_invite_view(request):
     
     login= "uname" in globals()
     emid=""     
     if not login:
          return redirect('login')
     context={
          'name':uname
     }
     if request.method=="POST":
          emid=request.POST.get('email')
     subject='S.P.I.T net banking invitation' 
     recipient_list=[str(emid)]
     url1='http://127.0.0.1:8000/reg'
     message=f'{uname} wants to invite you to register at S.P.I.T net banking,follow the link {url1}'  
     email_from=settings.EMAIL_HOST_USER  
     send_mail(subject,message,email_from,recipient_list)
     return render(request,'req_invite.html',context)  
def fraud_view(request):
     
     return render(request,'fraud.html',{})   
def delete_sure_view(request):
     return render(request,'delete_sure.html',{'name':uname})