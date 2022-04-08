from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from . models import DriverInfo

import datetime
from .models import RideRequest, SearchHistory
from .initial_data import car_type_dict
from django.utils import timezone


class ContactForm(forms.Form):
    name=forms.CharField()
    email=forms.EmailField(label='E-Mail')
    category=forms.ChoiceField(choices=[('question', 'Question'), ('other', 'Other')])
    subject=forms.CharField(required=False)
    body=forms.CharField(widget=forms.Textarea)


class RideRequestForm(forms.ModelForm):
    class Meta:
        model = RideRequest
        fields = ('required_time_arrival', 'departure_address',
                  'destination_address', 'canShare', 'number_of_ride_owner_party', 'vehicle_type', 'special_rider_info')
        labels = {
            'canShare': 'Share with others?',
        }
        widgets = {
            'required_time_arrival': forms.DateTimeInput(attrs={'placeholder': 'yyyy-mm-dd hh:mm'}),
            'special_rider_info': forms.TextInput(attrs={'placeholder': 'your special requests'}),
            #'departure_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street, City, Zip-Code'}),
            #'destination_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street, City, Zip-Code'}),
            #'canShare': forms.CheckboxInput(attrs={'class': 'form-control', 'placeholder': ''}),
            #'numOfRideOwnerParty': forms.NumberInput(attrs={'class': 'form-control'}),
            #'vehicle_type': forms.ChoiceField(attrs={'class': 'form-control', 'placeholder': ''}),
        }

    def clean_required_time_arrival(self):
        required_time_arrival = self.cleaned_data['required_time_arrival']
        current_datetime = datetime.datetime.now(required_time_arrival.tzinfo)
        print(required_time_arrival)
        print(current_datetime)
        print(required_time_arrival-current_datetime)
        if required_time_arrival-current_datetime <= datetime.timedelta(seconds=59):
            raise forms.ValidationError("The required time at arrival cannot be in the past!")
        return required_time_arrival

    def clean(self):
        cleaned_data = super(RideRequestForm, self).clean()
        vehicle_type = cleaned_data['vehicle_type']
        num_of_passengers_in_party = cleaned_data['number_of_ride_owner_party']
        departure_address = cleaned_data['departure_address']
        destination_address = cleaned_data['destination_address']
        if departure_address == destination_address:
            raise forms.ValidationError("Destination address should be different from departure address")
        if num_of_passengers_in_party < 1:
            raise forms.ValidationError("number of passengers in your party should be larger than 0 (including you)")

        if num_of_passengers_in_party > car_type_dict[vehicle_type]:
            raise forms.ValidationError("number of passengers may be larger than the capacity of your preferred vehicle type")

        return cleaned_data
    # def clean_number_of_ride_owner_party(self):
    #     vehicle_type = self.cleaned_data['vehicle_type']
    #     num_of_passengers_in_party = self.cleaned_data['number_of_ride_owner_party']
    #     if num_of_passengers_in_party <= 1:
    #         raise  forms.ValidationError("number of passengers in your party should be larger than 0 (including you)")
    #
    #     if num_of_passengers_in_party > car_type_dict[vehicle_type]:
    #         raise  forms.ValidationError("number of passengers may be larger than the capacity of your preferred vehicle type")
    #
    #     return num_of_passengers_in_party

class SearchHistoryForm(forms.ModelForm):
    class Meta:
        model = SearchHistory
        fields = ('destination_address', 'earliest_acceptable_arrival_time',
                  'latest_acceptable_arrival_time', 'num_of_passengers_in_party')
        labels = {
            'num_of_passengers_in_party': 'Number of passengers in your party',
        }
        widgets={
            'earliest_acceptable_arrival_time': forms.DateTimeInput(attrs={'placeholder': 'yyyy-mm-dd hh:mm'}),
            'latest_acceptable_arrival_time': forms.DateTimeInput(attrs={'placeholder': 'yyyy-mm-dd hh:mm'}),
        }


    def clean(self):
        cleaned_data = super(SearchHistoryForm, self).clean()
        latest_acceptable_arrival_time = cleaned_data['latest_acceptable_arrival_time']
        earliest_acceptable_arrival_time = cleaned_data['earliest_acceptable_arrival_time']
        current_datetime = datetime.datetime.now(earliest_acceptable_arrival_time.tzinfo)
        if earliest_acceptable_arrival_time-current_datetime <= datetime.timedelta(minutes=0):
            raise forms.ValidationError("The required time at arrival cannot be in the past!")
        if latest_acceptable_arrival_time-earliest_acceptable_arrival_time <= datetime.timedelta(minutes=0):
             raise forms.ValidationError("The latest acceptable arrival time should be larger "
                                        "than the earliest acceptable arrival time!")
        return cleaned_data

    def clean_num_of_passengers_in_party(self):
        num_of_passengers_in_party = self.cleaned_data['num_of_passengers_in_party']
        if num_of_passengers_in_party < 1:
            raise  forms.ValidationError("number of passengers in your party should be larger than 0 (including you)")

        return num_of_passengers_in_party






#######################################################
class CreateUserForm(UserCreationForm):
    first_name = forms.CharField(required=True, max_length=15)
    last_name = forms.CharField(required=True, max_length=15)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name','email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
        return user


class DriverRegisterForm(forms.ModelForm):
    class Meta:
        model = DriverInfo
        fields = '__all__'

        error_messages = {
            'first_name': {
                'max_length': 'name length cannot exceed 20 letters',
                'min_length': 'cannot be 0 letters'
            },
            'last_name': {
                'max_length': 'name length cannot exceed 20 letters',
                'min_length': 'cannot be 0 letters'
            },
            'licence_number':{
                'required': 'cannot be empty',
                'max_length': 'number is too long, exceed 15 characters'
            }

        }



