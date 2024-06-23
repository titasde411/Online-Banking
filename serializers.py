from rest_framework_json_api import serializers
from .models import *

class AadharSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Aadhar
        fields = ('name','dob', 'address', 'aadhar_no')


