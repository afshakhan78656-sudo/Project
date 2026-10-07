from django.db import models
from django.utils import timezone

# Create your models here.
class User(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    mobile = models.BigIntegerField()
    city = models.CharField(max_length=30, blank=True)
    profile = models.FileField(upload_to='profile_images/', blank=True, null=True)
    usertype = models.CharField(max_length=10, default='customer')
    def __str__(self):
        return self.first_name





class Car(models.Model):

    user = models.ForeignKey(
                                User,
                                on_delete=models.CASCADE,
                                null=True,
                                blank=True,
                                limit_choices_to={'usertype':'agency'}
                            )

    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    color = models.CharField(max_length=50)
    number_plate = models.CharField(max_length=50)
    seats = models.IntegerField()
    car_type = models.CharField(max_length=50)
    fuel_type = models.CharField(max_length=50)
    transmission = models.CharField(max_length=50)


    # Features checkbox
    has_ac = models.BooleanField(default=False)
    has_gps = models.BooleanField(default=False)
    has_music = models.BooleanField(default=False)
    has_bluetooth = models.BooleanField(default=False)
    has_usb = models.BooleanField(default=False)
    has_sunroof = models.BooleanField(default=False)
    has_rear_camera = models.BooleanField(default=False)
    has_airbags = models.BooleanField(default=False)
    has_abs = models.BooleanField(default=False)
    has_cruise = models.BooleanField(default=False)
    has_power_windows = models.BooleanField(default=False)
    has_central_lock = models.BooleanField(default=False)
    has_parking_sensor = models.BooleanField(default=False)
    has_spare_tyre = models.BooleanField(default=False)
    has_first_aid = models.BooleanField(default=False)



    price_per_day = models.IntegerField()
    city = models.CharField(max_length=100)
    pickup_address = models.TextField()
    main_photo = models.ImageField(upload_to='cars/')

    description = models.TextField(blank=True)


    def __str__(self):
        return self.brand + " " + self.model
    

class Wishlist(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    car = models.ForeignKey(Car,on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.first_name + " "+ self.car.brand
    



class Cart(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    car = models.ForeignKey(Car,on_delete = models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    tprice = models.PositiveBigIntegerField()
    dprice = models.PositiveBigIntegerField()
    payment = models.BooleanField(default=False)

    def __str__(self):
        return self.user.first_name + " " + self.car.brand + " " + self.car.model


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile = models.CharField(max_length=20)
    note = models.TextField(blank=True, null=True)
    
    total_days = models.IntegerField(default=1)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    booking_status = models.CharField(max_length=30, default='Pending Payment') # Pending Payment, Confirmed, Cancelled, Completed
    payment_status = models.CharField(max_length=20, default='Pending') # Pending, Success, Failed
    
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"Booking #{self.id} - {self.full_name}"


class BookedCar(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='cars')
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    price_per_day = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    pickup_date = models.DateField()
    return_date = models.DateField()

    def __str__(self):
        return f"Booking #{self.booking.id} - {self.car.brand} {self.car.model}"
    
    