from django.urls import path

from . import views

urlpatterns = [
    path('', views.homePage, name='home'),
    path('login', views.loginPage, name='login'),
    path('register', views.registerPage, name='register'),
    path('logout', views.logoutUser, name='logout'),
    path('driver_register/<int:pk>', views.driver_register, name='driver_register'),
    path('driver_save/<int:pk>', views.driver_save, name='driver_save'),
    path('driver_home/<int:pk>', views.driver_home, name='driver_home'),
    path('delete/<int:pk>', views.driver_delete, name='driver_delete'),
    path('update/<int:pk>', views.driver_update, name='driver_update'),
    path('edit/<int:pk>', views.update, name='edit'),
    path('driver_ride_detail/<int:pk>/<int:id>', views.driver_ride_detail, name='driver_ride_detail'),
    path('driver_ride_confirm/<int:pk>/<int:id>', views.driver_ride_confirm, name='driver_ride_confirm'),
    path('driver_ride_complete/<int:pk>/<int:id>', views.driver_ride_complete, name='driver_ride_complete'),
    path('driver_confirmed_ride_detail/<int:pk>/<int:id>', views.driver_confirmed_ride_detail, name='driver_confirmed_ride_detail'),
    ##########################################################

    path('rideowner/', views.rideowner, name='ride_owner'),
    path('ridesharer/', views.ridesharer, name='ride_sharer'),
    path('newrequest/', views.createNewRequest, name='create_new_request'),
    path('noncompleteride/', views.nonCompleteRide, name='non_complete_ride'),
    path('editopenride/<openride_id>', views.editOpenRide, name='edit_open_ride'),
    path('deleteopenride/<openride_id>', views.deleteOpenRide, name='delete_open_ride'),
    path('searchsharableride', views.searchSharableRide, name='search_sharable_ride'),
    path('searchresult', views.searchResult, name='search_result'),
    path('joinopenride/<openride_id>', views.joinOpenRide, name='join_open_ride'),
    path('dropopenride/<openride_id>', views.dropOpenRide, name='drop_open_ride'),
    path('viewdriverandvehicledetail/<confirmedride_id>', views.viewDriverAndVehicleDetail,
         name='view_driver_and_vehicle_detail'),
]
