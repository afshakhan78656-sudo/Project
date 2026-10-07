"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from myapp import views, cart_payment_views


urlpatterns = [
    path('index/', views.index, name='index'), 
    
    path('login/', views.login, name='login'), 
    path('logout/', views.logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('contact/', views.contact, name='contact'), 
    path('about/', views.about, name='about'),
    
    path('f_pass/', views.f_pass, name='f_pass'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('reset_password/', views.reset_password, name='reset_password'),
    
    path('uprofile/', views.uprofile, name='uprofile'),
    
    
    path('add_car/', views.add_car, name='add_car'),
    path('view_car/', views.view_car, name='view_car'),
    path('delete_car/<int:pk>/', views.delete_car, name='delete_car'),
    path('edit_car/<int:pk>/', views.edit_car, name='edit_car'),
    path('rent_car/', views.rent_car, name='rent_car'),
    
    
    path('add_wishlist/<int:pk>/', views.add_wishlist, name='add_wishlist'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('delete_wishlist/<int:pk>/', views.delete_wishlist, name='delete_wishlist'),

    path('book_car/<int:pk>/', views.book_car, name='book_car'),
    
    path('addcart/<int:pk>/', views.addcart, name='addcart'),
    path('scart/', views.scart, name='scart'),
    path('delet_cart/<int:pk>/', views.delet_cart, name='delet_cart'),
    path('sucess/', views.sucess, name='sucess'),
    path('myorder/', views.myorder, name='myorder'),

    # Cart Checkout & Summary Flow
    path('cart-booking-details/', cart_payment_views.cart_booking_details_view, name='cart_booking_details'),
    path('cart-booking-summary/', cart_payment_views.cart_booking_summary_view, name='cart_booking_summary'),
    path('cart-booking-payment-handler/', cart_payment_views.cart_booking_payment_handler, name='cart_booking_payment_handler'),
    path('cart-booking-success/', cart_payment_views.cart_booking_success_view, name='cart_booking_success'),
    path('cart-booking-failed/', cart_payment_views.cart_booking_failed_view, name='cart_booking_failed'),
    path('my-bookings/', cart_payment_views.my_bookings_view, name='my_bookings'),

    # Car Book summary view & Payment
]


