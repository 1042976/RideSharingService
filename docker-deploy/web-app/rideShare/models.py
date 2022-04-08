from django.db import models

# Create your models here.
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import User


class DriverInfo(models.Model):
    #first_name = models.CharField(max_length=20, blank=False)
    #last_name = models.CharField(max_length=20, blank=False)

    DRIVER_STATUS = [
        ("AVAILABLE", "available"),
        ("CONFIRM", "confirm"),
        ("START", "start"),
        ("COMPLETE", "complete"),
    ]

    TYPE_CHOICES = (
        ("FULLSIZE", 'Fullsize'),
        ("SUV", 'SUV'),
        ("MPV", 'MPV'),
        ("VAN", 'VAN'),
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="FULLSIZE")
    license_number = models.CharField(max_length=15, unique=True)
    max_passengers = models.IntegerField(default=5, validators=[MaxValueValidator(20), MinValueValidator(1)])
    driver_user = models.OneToOneField(User, related_name='driver', on_delete=models.CASCADE, primary_key=True)
    special_info = models.CharField(max_length=200, blank=True)
    driver_status = models.CharField(
        max_length=20,
        choices=DRIVER_STATUS,
        default="AVAILABLE"
    )

    def __str__(self):
        return self.user.get_full_name() + " vehicle with license number" + self.licence_number


class RideRequest(models.Model):
    TYPE_CHOICES = (
        ("FULLSIZE", 'Fullsize'),
        ("SUV", 'SUV'),
        ("MPV", 'MPV'),
        ("VAN", 'VAN'),
    )

    RIDE_STATUS = (
        ("OPEN", "open"),
        ("CONFIRMED", "confirmed"),
        ("START", "start"),
        ("COMPLETE", "complete"),
    )
    ride_owner_user = models.ForeignKey(User, on_delete=models.CASCADE)
    num_passengers = models.IntegerField(default=1, validators=[MaxValueValidator(20), MinValueValidator(1)])
    required_time_arrival = models.DateTimeField()
    departure_address = models.CharField(max_length=50)
    destination_address = models.CharField(max_length=50)
    canShare = models.BooleanField(default=False)
    number_of_ride_owner_party = models.IntegerField()
    vehicle_type = models.CharField(choices=TYPE_CHOICES, max_length=10, blank=True)
    special_rider_info = models.CharField(max_length=200, blank=True, null=True)
    driver = models.ForeignKey(DriverInfo, related_name='ride', on_delete=models.CASCADE, null=True)
    ride_status = models.CharField(
        choices=RIDE_STATUS,
        max_length=20,
        default="OPEN",
    )

    def __str__(self):
        return "from " + self.departure_address + " to " + self.destination_address


class RideInfo(models.Model):
    ride_request = models.OneToOneField(RideRequest, on_delete=models.CASCADE, primary_key=True)
    total_number_of_passengers = models.IntegerField(default=0)

#one user could be multiple owners
class RideOwner(models.Model):
    ride_owner_user = models.ForeignKey(User, on_delete=models.CASCADE)

#one user could be multiple sharers
class RideSharer(models.Model):
    ride_sharer_user = models.ForeignKey(User, on_delete=models.CASCADE)

#for sharer: many to one. for request. one to one
class ShareInfo(models.Model):
    ride_sharer = models.ForeignKey(User, on_delete=models.CASCADE)
    ride_request = models.ForeignKey(RideRequest, on_delete=models.CASCADE)
    ride_info = models.ForeignKey(RideInfo, on_delete=models.CASCADE)
    number_of_ride_sharer_party = models.IntegerField(default=1)

#many to one
class RideConfirmed(models.Model):
    driver_info = models.ForeignKey(DriverInfo, on_delete=models.CASCADE)
    ride_request = models.OneToOneField(RideRequest, on_delete=models.CASCADE, primary_key=True)

#store the search history
class SearchHistory(models.Model):
    search_user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    destination_address = models.CharField(max_length=50)
    earliest_acceptable_arrival_time = models.DateTimeField()
    latest_acceptable_arrival_time = models.DateTimeField()
    num_of_passengers_in_party = models.IntegerField()
    search_time = models.DateTimeField(auto_now_add=True)
