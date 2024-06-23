from django import forms
from .models import Accounts_list
from captcha.fields import CaptchaField

#creating registration form
class User_form(forms.ModelForm):
    #name=forms.CharField(label="Full Name")
    class Meta:
        model=Accounts_list
        fields=[
            'name',
            'Date_of_birth',
            'marital_status',
            'Address',
            'aadhar',
            'username',
            'password',
            'secret_question',
            'email',
            'Mobile_number'

        ]
        labels={
             'name': '',
            'Date_of_birth':'',
            'marital_status':'',
            'Address':'',
            'aadhar':'',
            'username':'',
            'password':'',
            'secret_question':'',
            'email':'',
            'Mobile_number':''
        }
        widgets={
            'name': forms.TextInput(attrs={'placeholder':'Enter Your full name','class':'form-control','label':'Full Name'}),
            'Date_of_birth':forms.TextInput(attrs={'placeholder':'Enter Your Date of birth (yyyy-mm-dd)','class':'form-control'}),
            'marital_status':forms.TextInput(attrs={'placeholder':'Enter marital status','class':"form-check-label"}),
            'Address':forms.TextInput(attrs={'placeholder':'Enter Your address','class':'form-control'}),
            'aadhar':forms.TextInput(attrs={'placeholder':'Enter aadhar id','class':'form-control'}),
            'username':forms.TextInput(attrs={'placeholder':'Create an username','class':'form-control'}),
            'password':forms.PasswordInput(attrs={'placeholder':'Create a password','class':'form-control'}),
            'secret_question':forms.TextInput(attrs={'placeholder':'What is your nickname','class':'form-control'}),
            'email':forms.TextInput(attrs={'placeholder':'Enter your email-id','class':'form-control'}),
            'Mobile_number':forms.TextInput(attrs={'placeholder':'Enter Your contact number','class':'form-control'})
        }
class MyForm(forms.Form):
     captcha=CaptchaField()   
class Photo(forms.ModelForm):

    class Meta:
        model = Accounts_list
        fields = ['image']    