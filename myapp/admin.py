from django.contrib import admin

# Register your models here.

from .models import User, Car, Wishlist, Cart, Booking, BookedCar

admin.site.register(User)
admin.site.register(Car)
admin.site.register(Wishlist)
admin.site.register(Cart)
admin.site.register(Booking)
admin.site.register(BookedCar)