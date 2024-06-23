from django.db import models
from django.contrib.auth.hashers import make_password
import uuid
#from djangotoolbox.fields import ListField
#from .forms import StringListField
# Create your models here.
# class accField(ListField):
#     def formfield(self, **kwargs):
#         return models.Field.formfield(self, StringListField, **kwargs)
class Transac(models.Model):
    transaction_type=models.CharField(max_length=120)
    amount=models.DecimalField(max_digits=22, decimal_places=2)
    Date_time=models.DateTimeField()
    oppo_acc=models.CharField(max_length=50,null=True,blank=True)
class Aadhar(models.Model):
    name=models.CharField(max_length=120)
    dob=models.DateTimeField()
    address=models.CharField(max_length=220)
    aadhar_no=models.DecimalField(max_digits=12, decimal_places=0,null=True,blank=True)
class Scheme_count(models.Model):
    name= models.CharField(max_length=120)
    prem_pay_count=models.DecimalField(max_digits=10, decimal_places=2) 
    creation_date=models.DateTimeField()
    prem=models.DecimalField(max_digits=10, decimal_places=2) 
    rest_count=models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True) 
    last_prem_pay=models.DateTimeField(null=True,blank=True)
class Accounts(models.Model) :
    account_type=models.CharField(max_length=120)
    account_no=models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transactions=models.ManyToManyField(Transac,blank=True,null=True)
    balance=models.DecimalField(max_digits=22, decimal_places=2,blank=True,null=True)
    creation_date=models.DateTimeField(blank=True,null=True)
    Maturity_amount=models.DecimalField(max_digits=22, decimal_places=2,blank=True,null=True)
    interest_rate=models.DecimalField(max_digits=3, decimal_places=2,blank=True,null=True)
    Duration=models.DecimalField(max_digits=3, decimal_places=2,blank=True,null=True,default=1)
    username=models.CharField(max_length=120,null=True,blank=True)
    last_t_date=models.DateTimeField(blank=True,null=True)
    interest=models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)
    is_matured=models.BooleanField(null=True,blank=True,default=False)
    is_added_to_savings=models.BooleanField(null=True,blank=True,default=False)
    #for recurring
    last_deposit_time=models.DateTimeField(blank=True,null=True)
    total_no_deposit=models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True,default=1.00)
    og_balance=models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)
    is_deleted=models.BooleanField(null=True,blank=True,default=False)
    first_quarter_paid=models.BooleanField(null=True,blank=True,default=False)
    first_one_paid=models.BooleanField(null=True,blank=True,default=False)
    is_stuck=models.BooleanField(null=True,blank=True,default=False)
    fine=models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)
    resi=models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)
    delete_ma=models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)
    def _str_(self) :
        return self.account_no  
class Scheme(models.Model):
    name= models.CharField(max_length=120)
    entry_age=models.DecimalField(max_digits=3, decimal_places=0,null=True)
    Annual_premium=models.DecimalField(max_digits=10, decimal_places=2,null=True)
    description=models.CharField(max_length=350)
    in_image = models.ImageField(upload_to='images',null=True,blank=True)
    sum_insured=models.CharField(max_length=120,null=True,blank=True)
    Maternity_expenses=models.CharField(max_length=120,null=True,blank=True)
    waiting_period=models.CharField(max_length=120,null=True,blank=True)
    disease_capping=models.CharField(max_length=120,null=True,blank=True)
    icu_charges=models.CharField(max_length=120,null=True,blank=True)
    health_checkups=models.CharField(max_length=120,null=True,blank=True)
    Immediate_family=models.CharField(max_length=120,null=True,blank=True)
class Accounts_list(models.Model):
    name= models.CharField(max_length=120)
    Date_of_birth= models.DateField(null=True)
    marital_status=models.BooleanField(null=True)
    Address=  models.CharField(max_length=500,null=True)
    aadhar=models.DecimalField(max_digits=12, decimal_places=0,unique=True,null=True)
    username=models.CharField(max_length=120,null=True)
    password=models.CharField(max_length=120,null=True)
    secret_question=models.CharField(max_length=120,null=True)
    accounts=models.ManyToManyField(Accounts,blank=True,null=True)
    email=models.EmailField(max_length=254,null=True)
    Mobile_number=models.BigIntegerField(null=True)
    is_phone_verified=models.BooleanField(default=False,null=True,blank=True)
    otp=models.CharField(max_length=6,null=True,blank=True)
    image = models.ImageField(upload_to='images',null=True,blank=True)
    schemes=models.ManyToManyField(Scheme,null=True,blank=True) 
    count=models.DecimalField(max_digits=10, decimal_places=0,default=0,null=True,blank=True)
    loan_paid=models.BooleanField(null=True,blank=True)
    typing_speed=models.DecimalField(max_digits=20, decimal_places=15,default=0,null=True,blank=True)
    login_count=models.DecimalField(max_digits=10, decimal_places=0,default=0,null=True,blank=True)
    transac_count=models.DecimalField(max_digits=10, decimal_places=0,default=0,null=True,blank=True)
    transac_amount=models.DecimalField(max_digits=10, decimal_places=4,default=0,null=True,blank=True)
    is_fraud=models.BooleanField(default=False,null=True,blank=True)
    last_login_date=models.DateTimeField(blank=True,null=True)
    is_aadhar_verified=models.BooleanField(default=False,null=True,blank=True)
    scheme_count=models.ManyToManyField(Scheme_count,null=True,blank=True) 
  
    # def save(self, *args, **kwargs):
    #         self.password = make_password(self.password)
    #         self.secret_question = make_password(self.secret_question)
    #         super(Accounts, self).save(*args, **kwargs)
    def _str_(self) :
        return self.name       


