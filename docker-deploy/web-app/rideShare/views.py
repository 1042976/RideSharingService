import datetime

from django.conf import settings
from django.db.models.functions import TruncMinute
from django.shortcuts import render, redirect, reverse
from django.core.mail import send_mail
from django.db.models import Q
# Create your views here.
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone


from .models import DriverInfo
from .form import DriverRegisterForm, CreateUserForm
from .models import RideRequest, ShareInfo, SearchHistory, RideInfo, RideConfirmed
from .form import ContactForm, RideRequestForm, SearchHistoryForm
from django.utils.timezone import now, localtime
from .initial_data import car_type_dict


@login_required(login_url='login')
def homePage(request):
    context = {'id': request.user.id}
    return render(request, 'rideShare/home.html', context)


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.info(request, 'username or password is incorrect')

        context = {}
        return render(request, 'rideShare/login.html', context)


def registerPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        form = CreateUserForm()
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                user = form.save()
                firstN = form.cleaned_data.get('first_name')
                lastN = form.cleaned_data.get('last_name')
                messages.success(request, "account was created for " + firstN + " " + lastN)
                return redirect('login')
            else:
                messages.info(request, form.error_messages)
        context = {'form': form}
        return render(request, 'rideShare/register.html', context)


@login_required(login_url='login')
def driver_register(request, pk):
    print('successfully enter driver registration page!')
    form = DriverRegisterForm(request.POST)
    if form.is_valid():
        print('hello world')
        form.save()
        driver_user_firstname = form.cleaned_data.get('first_name')
        driver_user_lastname = form.cleaned_data.get('last_name')
        messages.success(request, driver_user_firstname + driver_user_lastname + ", you register successfully")
        return redirect(reverse('driver_home', kwargs={'pk': pk}))
    return render(request, 'rideShare/driver_register.html', {'pk': pk})


@login_required(login_url='login')
def driver_save(request, pk):
    d_info = DriverInfo()
    result = checkDriverInfo(request)
    license_num = request.POST.get('license_number')
    if result[0] == False:
        messages.info(request, result[1])
        return redirect(reverse('driver_register', kwargs={'pk': pk}))
    elif DriverInfo.objects.filter(license_number=license_num).exists():
        print("hello")
        messages.info(request, "Sorry, the license number already exists")
        return redirect(reverse('driver_register', kwargs={'pk': pk}))
    else:
        d_info.license_number = request.POST.get('license_number')
        d_info.type = request.POST.get('vehicle_type')
        d_info.max_passengers = request.POST.get('max_passengers')
        d_info.special_info = request.POST.get('special_info')
        d_info.driver_user_id = request.user.id
        d_info.save()
    messages.success(request, result[1])
    return redirect(reverse('driver_home', kwargs={'pk': pk}))


@login_required(login_url='login')
def checkDriverInfo(request):
    license_number = request.POST.get('license_number')
    special_info = request.POST.get('special_info')
    max_passengers = request.POST.get('max_passengers')
    car_type = request.POST.get('vehicle_type')
    if len(license_number) > 15:
        return (False, 'license number is too long')
    elif len(special_info) > 200:
        return (False, 'special information is too long')
    elif car_type == "FULLSIZE" and max_passengers != "4":
        return (False, 'FullSize capacity should be 4')
    elif car_type == "SUV" and max_passengers != "6":
        return (False, 'SUV capacity should be 6')
    elif car_type == "MPV" and max_passengers != "8":
        return (False, 'MPV capacity should be 8')
    elif car_type == "VAN" and max_passengers != "15":
        return (False, 'VAN capacity should be 15')
    return (True, 'Registration successfully!')


@login_required(login_url='login')
def driver_home(request, pk):
    # case1: driver status is OPEN, shows all open rides filtered by special_info,
    # vehicle_type, num_passengers < max_passengers
    # all open rides' arrival time should > current time

    driver = request.user
    try:
        driver_info = DriverInfo.objects.get(driver_user_id=pk)
        if driver_info.driver_status == "AVAILABLE":
            currentTime = TruncMinute(now())
            rideRequests = RideRequest.objects.filter(Q(special_rider_info=driver_info.special_info) | Q(special_rider_info=None) | Q(special_rider_info=''))
            #todo filter the ride requests
            openRideLists = rideRequests.filter(Q(ride_status="OPEN") & Q(num_passengers__lte=driver_info.max_passengers)).order_by('required_time_arrival')
            openRideLists = openRideLists.filter(Q(vehicle_type=driver_info.type) & Q(required_time_arrival__gte=currentTime))
            all_confirmed_rides = RideRequest.objects.all().filter(driver_id=pk)
            all_confirmed_rides = all_confirmed_rides.filter(Q(ride_status="CONFIRMED") | Q(ride_status="COMPLETE")).order_by('-required_time_arrival')
            #all_confirmed_rides = RideRequest.objects.all().filter(driver_id=pk, ride_status="COMPLETE").order_by('-required_time_arrival')
            context={'requests': openRideLists, 'info': driver_info, 'pk': pk, 'all_confirmed_rides': all_confirmed_rides}
            return render(request, 'rideShare/driver_home.html', context)
        elif driver_info.driver_status == "CONFIRM":

        # case2: show open rides whose arrival time is later than confirmed ride in process
        #  show open rides whose arrival time > currentRide's arrival time
            currentRide = RideRequest.objects.all().filter(driver_id=pk).filter(ride_status="CONFIRMED")
            time_arrival = currentRide.first().required_time_arrival
            rideRequests = RideRequest.objects.filter(
                Q(special_rider_info=driver_info.special_info) | Q(special_rider_info=None) | Q(special_rider_info=''))
            openRideLists = rideRequests.filter(Q(ride_status="OPEN") & Q(num_passengers__lte=driver_info.max_passengers))
            openRideLists = openRideLists.filter(
                Q(vehicle_type=driver_info.type) & Q(required_time_arrival__gte=time_arrival))
            # include confirmed rides and complete rides
            #complete ride's link should be disable
            all_confirmed_rides = RideRequest.objects.all().filter(driver_id=pk)
            all_confirmed_rides = all_confirmed_rides.filter(Q(ride_status="CONFIRMED") | Q(ride_status="COMPLETE")).order_by('-required_time_arrival')
            context = {'requests': openRideLists, 'info': driver_info, 'pk': pk, 'all_confirmed_rides': all_confirmed_rides}
            return render(request, 'rideShare/driver_home.html', context)

    except DriverInfo.DoesNotExist:
        driver_info = None
        context= {'requests': None, 'info': driver_info, 'pk': pk, 'all_confirmed_rides': None}
        return render(request, 'rideShare/driver_home.html', context)


@login_required(login_url='login')
def driver_delete(request, pk):
    info = DriverInfo.objects.get(driver_user_id=pk)
    info.delete()
    messages.success(request, "This piece of driver info deleted successfully!")
    return redirect(reverse('driver_home', kwargs={'pk': pk}))


@login_required(login_url='login')
def driver_update(request, pk):
    info = DriverInfo.objects.get(driver_user_id=pk)
    return render(request, 'rideShare/driver_update.html', {'info': info})


@login_required(login_url='login')
def update(request, pk):
    d_info = DriverInfo.objects.get(driver_user_id=pk)
    result = checkDriverInfo(request)
    if result[0] == False:
        messages.info(request, result[1])
        return redirect(reverse('driver_update', kwargs={'pk': pk}))

    else:
        d_license_number = request.POST.get('license_number')
        d_type = request.POST.get('vehicle_type')
        d_max_passengers = int(request.POST.get('max_passengers'))
        print(d_max_passengers)
        d_special_info = request.POST.get('special_info')
        d_info = DriverInfo.objects.filter(driver_user_id=pk).update(license_number=d_license_number,\
        type=d_type, max_passengers=d_max_passengers, special_info=d_special_info)

    messages.success(request, "Update Successfully!")
    return redirect(reverse('driver_home', kwargs={'pk': pk}))


@login_required(login_url='login')
def driver_ride_detail(request, pk, id):

    open_requests = RideRequest.objects.filter(id=pk)

    context = {'open_requests': open_requests, 'id': id}
    return render(request, 'rideShare/driver_ride_detail.html', context)


@login_required(login_url='login')
def driver_ride_confirm(request, pk, id):
    # pk for rider's id
    # id for driver's id
    #todo what if owner cancel ride, but driver wants to confirm ride?
    try:
        selected_request = RideRequest.objects.get(id=pk)
        selected_request.ride_status = "CONFIRMED"
        selected_request.driver_id = id
        driver = DriverInfo.objects.get(driver_user_id=id)
        driver.driver_status = "CONFIRM"
        messages.success(request, "You confirm this ride successfully!")
        selected_request.save()
        driver.save()
        # send email

        # todo have not add sharers because we haven't designed the rideSharer models
        share_infos = ShareInfo.objects.filter(ride_request=selected_request)

        # send to owner
        send_mail(
            "Your ride request has been confirmed successfully",  # subject
            "Ride owner: Your ride has been confirmed! The driver's license number is " + driver.license_number,  # message
            settings.EMAIL_HOST_USER,  # from email
            [User.objects.get(id=selected_request.ride_owner_user_id).email]  # to email
        )

        # send to sharers
        for share_info in share_infos:
            send_mail(
                "Your ride request has been confirmed successfully",  # subject
                "Ride sharer: Your ride has been confirmed! The driver's license number is " + driver.license_number,  # message
                settings.EMAIL_HOST_USER,  # from email
                [share_info.ride_sharer.email]  # to email
            )
        # create rideConfirm
        RideConfirmed.objects.create(ride_request=selected_request, driver_info=driver)
    except RideRequest.DoesNotExist:
        messages.info(request, "Sorry! The owner deleted the trip!")
    return redirect(reverse('driver_home', kwargs={'pk': id}))



@login_required(login_url='login')
def driver_ride_complete(request, pk, id):
    # pk for rider's id
    # id for driver's id
    selected_request = RideRequest.objects.get(id=pk)
    selected_request.ride_status = "COMPLETE"
    driver = DriverInfo.objects.get(driver_user_id=request.user.id)
    selected_request.save()
    driver = DriverInfo.objects.filter(driver_user_id=request.user.id).update(driver_status="AVAILABLE")
    messages.success(request, "You have completed this ride !")
    return redirect(reverse('driver_home', kwargs={'pk': id}))


@login_required(login_url='login')
def driver_confirmed_ride_detail(request, pk, id):
    selected_confirmed_requests = RideRequest.objects.filter(id=pk)
    context = {'selected_confirmed_requests': selected_confirmed_requests, 'id': id}
    return render(request, 'rideShare/driver_confirmed_ride_detail.html', context)


def logoutUser(request):
    logout(request)
    return redirect('login')


def findDriverByPK(pk):
    if DriverInfo.objects.filter(driver_user_id=pk).exists():
        return True
    return False


########################################################
#owner part & sharer part
def rideowner(request):
    return render(request, 'rideShare/rideowner.html')


def ridesharer(request):
    return render(request, 'rideShare/ridesharer.html')



def nonCompleteRide(request):
    ride_list = RideRequest.objects.filter(ride_owner_user=request.user)
    share_info_list_as_owner = ShareInfo.objects.filter(ride_request__ride_owner_user=request.user)
    share_info_list_as_sharer = ShareInfo.objects.filter(ride_sharer=request.user)
    share_info_list = ShareInfo.objects.all()
    ride_info_list_as_owner = RideInfo.objects.filter(ride_request__ride_owner_user=request.user)
    return render(request, 'rideShare/noncompleteride.html', {'ride_list': ride_list,
                                                              'share_info_list_as_owner': share_info_list_as_owner,
                                                              'share_info_list_as_sharer': share_info_list_as_sharer,
                                                              'share_info_list': share_info_list,
                                                              'ride_info_list_as_owner': ride_info_list_as_owner
                                                              })


def createNewRequest(request):
    submitted = False
    if request.method == 'POST':
        form = RideRequestForm(request.POST)
        if form.is_valid():

            myrequest = RideRequest.objects.create(
                ride_owner_user=request.user,
                required_time_arrival=localtime(form.cleaned_data['required_time_arrival']),
                departure_address=form.cleaned_data['departure_address'],
                destination_address=form.cleaned_data['destination_address'],
                canShare=form.cleaned_data['canShare'],
                number_of_ride_owner_party=form.cleaned_data['number_of_ride_owner_party'],
                num_passengers=form.cleaned_data['number_of_ride_owner_party'],
                vehicle_type=form.cleaned_data['vehicle_type'],
                special_rider_info=form.cleaned_data['special_rider_info'],
            )
            myrequest.save()
            ride_info = RideInfo.objects.create(ride_request=myrequest,
                                                total_number_of_passengers=myrequest.number_of_ride_owner_party)
            ride_info.save()
            messages.success(request, "Your Request has been successfully created")
            return HttpResponseRedirect('/rideShare/newrequest?submitted=True')
    else:
        form = RideRequestForm
        if 'submitted' in request.GET:
            submitted = True

    return render(request, 'rideShare/requestform.html', {'form': form, 'submitted': submitted})


def editOpenRide(request, openride_id):
    try:
        openride_confirmed = RideConfirmed.objects.get(pk=openride_id)
    except RideConfirmed.DoesNotExist:
        openride_confirmed = None

    if openride_confirmed is not None:
        messages.warning(request, 'The ride has been confirmed by driver.')
        return redirect('non_complete_ride')

    openride = RideRequest.objects.get(pk=openride_id)

    # old data
    num_of_owner_party_old = openride.number_of_ride_owner_party
    destination_address_old = openride.destination_address
    required_arrival_time_old = openride.required_time_arrival
 #   canShare_old = openride.canShare
    form = RideRequestForm(request.POST or None, instance=openride)
    if form.is_valid():
        # check again if openride has been confirmed
        try:
            openride_confirmed = RideConfirmed.objects.get(pk=openride_id)
        except RideConfirmed.DoesNotExist:
            openride_confirmed = None

        if openride_confirmed is not None:
            messages.warning(request, 'The ride has been confirmed by driver.')
            return redirect('non_complete_ride')

        if not form.cleaned_data['canShare']:
            ShareInfo.objects.filter(ride_request=openride).delete()

        # todo need to review and test here
        max_num_of_passengers = car_type_dict[form.cleaned_data['vehicle_type']]
        current_num_of_sharers = openride.num_passengers - num_of_owner_party_old
#        canShare_old = openride.canShare
        if current_num_of_sharers + form.cleaned_data['number_of_ride_owner_party'] > max_num_of_passengers:
            messages.warning(request,
                             'Fail to update because the total number of passengers(including sharers) may '
                             'exceed the capacity of the vehicle type you prefer.')
            return redirect('non_complete_ride')
        else:
            # If change destination or time. cancel sharers' ride and notify them
            if destination_address_old != form.cleaned_data['destination_address'] or \
                    required_arrival_time_old != form.cleaned_data['required_time_arrival']:
                share_infos = ShareInfo.objects.filter(ride_request=openride)
                # send to sharers
                for share_info in share_infos:
                    send_mail(
                        "Your ride has been cancelled",  # subject
                        "Ride sharer: Your ride to " + destination_address_old + " "
                                                                                 "has been cancelled since "
                                                                                 "the destination, required arrival time or share status has been updated by ride owner!",
                        # message
                        settings.EMAIL_HOST_USER,  # from email
                        [share_info.ride_sharer.email]  # to email
                    )
                share_infos.delete()
                current_num_of_sharers = 0

            form.save()
            openride.num_passengers = current_num_of_sharers + form.cleaned_data['number_of_ride_owner_party']
            openride.save()
            openride_info = RideInfo.objects.get(pk=openride_id)
            openride_info.total_number_of_passengers = openride.num_passengers
            openride_info.save()

        return redirect('non_complete_ride')

    return render(request, 'rideShare/editopenride.html', {'openride': openride, 'form': form})

'''

def editOpenRide(request, openride_id):
    try:
        openride_confirmed = RideConfirmed.objects.get(pk=openride_id)
    except RideConfirmed.DoesNotExist:
        openride_confirmed = None

    if openride_confirmed is not None:
        messages.warning(request, 'The ride has been confirmed by driver.')
        return redirect('non_complete_ride')

    openride = RideRequest.objects.get(pk=openride_id)

    # old data
    num_of_owner_party_old = openride.number_of_ride_owner_party
    destination_address_old = openride.destination_address
    required_arrival_time_old = openride.required_time_arrival

    form = RideRequestForm(request.POST or None, instance=openride)
    if form.is_valid():
        # check again if openride has been confirmed
        try:
            openride_confirmed = RideConfirmed.objects.get(pk=openride_id)
        except RideConfirmed.DoesNotExist:
            openride_confirmed = None

        if openride_confirmed is not None:
            messages.warning(request, 'The ride has been confirmed by driver.')
            return redirect('non_complete_ride')

        if not form.cleaned_data['canShare']:
            ShareInfo.objects.filter(ride_request=openride).delete()
            share_infos = ShareInfo.objects.filter(ride_request=openride)
            # send to sharers
            for share_info in share_infos:
                send_mail(
                    "Your ride has been cancelled",  # subject
                    "Ride sharer: Your ride to " + destination_address_old + " "
                                                                             "has been cancelled since "
                                                                             "by ride owner!",
                    # message
                    settings.EMAIL_HOST_USER,  # from email
                    [share_info.ride_sharer.email]  # to email
                )

        # todo need to review and test here
        max_num_of_passengers = car_type_dict[form.cleaned_data['vehicle_type']]
        current_num_of_sharers = openride.num_passengers - num_of_owner_party_old
        if current_num_of_sharers + form.cleaned_data['number_of_ride_owner_party'] > max_num_of_passengers:
            messages.warning(request,
                             'Fail to update because the total number of passengers(including sharers) may '
                             'exceed the capacity of the vehicle type you prefer.')
            return redirect('non_complete_ride')
        else:
            # If change destination or time. cancel sharers' ride and notify them
            if destination_address_old != form.cleaned_data['destination_address'] or \
                    required_arrival_time_old != form.cleaned_data['required_time_arrival']:
                share_infos = ShareInfo.objects.filter(ride_request=openride)
                # send to sharers
                for share_info in share_infos:
                    send_mail(
                        "Your ride has been cancelled",  # subject
                        "Ride sharer: Your ride to " + destination_address_old + " "
                                                                                 "has been cancelled since "
                                                                                 "the destination or required arrival time  has been updated by ride owner!",
                        # message
                        settings.EMAIL_HOST_USER,  # from email
                        [share_info.ride_sharer.email]  # to email
                    )
                share_infos.delete()
                current_num_of_sharers = 0

            form.save()
            openride.num_passengers = current_num_of_sharers + form.cleaned_data['number_of_ride_owner_party']
            openride.save()
            openride_info = RideInfo.objects.get(pk=openride_id)
            openride_info.total_number_of_passengers = openride.num_passengers
            openride_info.save()

        return redirect('non_complete_ride')

    return render(request, 'rideShare/editopenride.html', {'openride': openride, 'form': form})

'''


def deleteOpenRide(request, openride_id):
    try:
        openride_confirmed = RideConfirmed.objects.get(pk=openride_id)
    except RideConfirmed.DoesNotExist:
        openride_confirmed = None

    if openride_confirmed is not None:
        messages.warning(request, 'The ride has been confirmed by driver.')
        return redirect('non_complete_ride')

    openride = RideRequest.objects.get(pk=openride_id)
    openride.delete()
    return redirect('non_complete_ride')


def dropOpenRide(request, openride_id):
    try:
        openride = RideRequest.objects.get(pk=openride_id)
    except RideRequest.DoesNotExist:
        openride = None
    if openride is None:
        return redirect('non_complete_ride')

    try:
        openride_confirmed = RideConfirmed.objects.get(pk=openride_id)
    except RideConfirmed.DoesNotExist:
        openride_confirmed = None

    if openride_confirmed is not None:
        messages.warning(request, 'The ride has been confirmed by driver.')
        return redirect('non_complete_ride')

    try:
        share_info = ShareInfo.objects.filter(ride_request_id=openride_id).filter(ride_sharer=request.user).get()
    except:
        share_info = None

    if share_info is None:
        messages.warning(request, 'The ride has been set unsharable by owner.')
        return redirect('non_complete_ride')

    ride_info = RideInfo.objects.get(ride_request_id=openride_id)
    openride = RideRequest.objects.get(pk=openride_id)
    old_num = openride.num_passengers
    ride_info.total_number_of_passengers = old_num - share_info.number_of_ride_sharer_party
    openride.num_passengers = old_num-share_info.number_of_ride_sharer_party
    share_info.delete()
    ride_info.save()
    openride.save()
    return redirect('non_complete_ride')

def joinOpenRide(request, openride_id):
    try:
        openride = RideRequest.objects.get(pk=openride_id)
    except RideRequest.DoesNotExist:
        openride = None
    if openride is None:
        messages.warning(request, 'The ride has been deleted by owner.')
        return redirect('search_result')
    try:
        openride_confirmed = RideConfirmed.objects.get(pk=openride_id)
    except RideConfirmed.DoesNotExist:
        openride_confirmed = None

    if openride_confirmed is not None:
        messages.warning(request, 'The ride has been confirmed by driver.')
        return redirect('search_result')

    #check if number exceed max num (num may change after search)
    old_num = openride.num_passengers
    number_of_ride_sharer_party = SearchHistory.objects.get(search_user=request.user).num_of_passengers_in_party
    if car_type_dict[openride.vehicle_type] < old_num+number_of_ride_sharer_party:
        messages.warning(request, 'Fail to join this open ride because the number '
                                  'of passengers in your party exceeds the capacity of '
                                  'current vehicle type')
        return redirect('search_result')

    ride_info = RideInfo.objects.get(ride_request_id=openride_id)
    new_share_info = ShareInfo.objects.create(
        ride_sharer=request.user,
        ride_request=openride,
        ride_info=ride_info,
        number_of_ride_sharer_party=number_of_ride_sharer_party
    )
    new_share_info.save()
    ride_info.total_number_of_passengers = old_num + new_share_info.number_of_ride_sharer_party
    ride_info.save()
    openride.num_passengers = old_num+new_share_info.number_of_ride_sharer_party
    openride.save()
    return redirect('search_result')


def viewDriverAndVehicleDetail(request, confirmedride_id):
    ride_confirmed = RideConfirmed.objects.get(pk=confirmedride_id)
    driver_and_vehicle_info = ride_confirmed.driver_info
    return render(request, 'rideShare/driverandvehicledetail.html',
                  {'driver_and_vehicle_info': driver_and_vehicle_info})


def searchSharableRide(request):
    if request.method == "POST":
        form = SearchHistoryForm(request.POST)
        if form.is_valid():
            destination_address = form.cleaned_data['destination_address']
            earliest_acceptable_arrival_time = form.cleaned_data['earliest_acceptable_arrival_time']
            latest_acceptable_arrival_time = form.cleaned_data['latest_acceptable_arrival_time']
            num_of_passengers_in_your_party = form.cleaned_data['num_of_passengers_in_party']
            try:
                my_search_history = SearchHistory.objects.get(pk=request.user)
            except SearchHistory.DoesNotExist:
                my_search_history = None

            if my_search_history is None:
                my_search_history = SearchHistory.objects.create(
                    search_user=request.user,
                    destination_address=destination_address,
                    earliest_acceptable_arrival_time=earliest_acceptable_arrival_time,
                    latest_acceptable_arrival_time=latest_acceptable_arrival_time,
                    num_of_passengers_in_party=num_of_passengers_in_your_party
                )
                my_search_history.save()
            else:
                my_search_history.destination_address = destination_address
                my_search_history.earliest_acceptable_arrival_time = earliest_acceptable_arrival_time
                my_search_history.latest_acceptable_arrival_time = latest_acceptable_arrival_time
                my_search_history.num_of_passengers_in_party = num_of_passengers_in_your_party
                my_search_history.save()

            sharable_open_rides = RideRequest.objects.filter(ride_status="OPEN"). \
                filter(canShare=True).filter(destination_address=destination_address). \
                filter(ride_status="OPEN").filter(required_time_arrival__gte=earliest_acceptable_arrival_time, \
                                                  required_time_arrival__lte=latest_acceptable_arrival_time)

            your_own_open_rides = RideRequest.objects.filter(ride_status="OPEN"). \
                filter(canShare=True).filter(destination_address=destination_address). \
                filter(ride_status="OPEN").filter(ride_owner_user=request.user)
            share_infos = ShareInfo.objects.filter(ride_sharer=request.user)
            for share_info in share_infos:
                sharable_open_rides = sharable_open_rides.exclude(pk=share_info.ride_request.pk)

            to_exclude_pk_arr = []
            for sharable_open_ride in sharable_open_rides:
                max_num = car_type_dict[sharable_open_ride.vehicle_type]
                if max_num < sharable_open_ride.num_passengers+num_of_passengers_in_your_party:
                    to_exclude_pk_arr.append(sharable_open_ride.pk)
            for ride_pk in to_exclude_pk_arr:
                sharable_open_rides = sharable_open_rides.exclude(pk=ride_pk)

            sharable_open_rides = sharable_open_rides.difference(your_own_open_rides)

            return render(request, 'rideShare/searchresult.html',
                          {'destination_address': destination_address,
                           'earliest_acceptable_arrival_time': earliest_acceptable_arrival_time,
                           'latest_acceptable_arrival_time': latest_acceptable_arrival_time,
                           'num_of_passengers_in_your_party': num_of_passengers_in_your_party,
                           'sharable_open_rides': sharable_open_rides,
                           }
                          )
    else:
        form = SearchHistoryForm
    return render(request, 'rideShare/searchsharableride.html', {'form': form})


def searchResult(request):
    # get search history
    search_history = SearchHistory.objects.get(search_user=request.user)
    destination_address = search_history.destination_address
    earliest_acceptable_arrival_time = search_history.earliest_acceptable_arrival_time
    latest_acceptable_arrival_time = search_history.latest_acceptable_arrival_time
    num_of_passengers_in_your_party = search_history.num_of_passengers_in_party
    # search the target rides again
    sharable_open_rides = RideRequest.objects.filter(ride_status="OPEN"). \
        filter(canShare=True).filter(destination_address=destination_address). \
        filter(ride_status="OPEN")
    your_own_open_rides = RideRequest.objects.filter(ride_status="OPEN"). \
        filter(canShare=True).filter(destination_address=destination_address). \
        filter(ride_status="OPEN").filter(ride_owner_user=request.user)
    share_infos = ShareInfo.objects.filter(ride_sharer=request.user)
    for share_info in share_infos:
        sharable_open_rides = sharable_open_rides.exclude(pk=share_info.ride_request.pk)
    sharable_open_rides = sharable_open_rides.difference(your_own_open_rides)

    # show results
    return render(request, 'rideShare/searchresult.html',
                  {'destination_address': destination_address,
                   'earliest_acceptable_arrival_time': earliest_acceptable_arrival_time,
                   'latest_acceptable_arrival_time': latest_acceptable_arrival_time,
                   'num_of_passengers_in_your_party': num_of_passengers_in_your_party,
                   'sharable_open_rides': sharable_open_rides,
                   }
                  )
