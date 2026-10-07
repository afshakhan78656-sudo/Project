from django.shortcuts import render, redirect
from .models import *
import random
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from functools import wraps
import razorpay

# Create your views here.

def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'email' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper











def index(request):
    return render(request,'index.html')



def signup(request):
    if request.method == 'POST':
        if User.objects.filter(email=request.POST['email']).exists():
            msg = "Email already exists. Please use a different email."
            return render(request, 'signup.html', {'msg': msg})     
            
        elif User.objects.filter(username=request.POST['username']).exists():
            msg = "Username already exists. Please choose a different username."
            return render(request, 'signup.html', {'msg': msg})
            
        else:
            if request.POST['password'] == request.POST['cpassword']:
                user = User.objects.create(
                    first_name=request.POST['first_name'],
                    last_name=request.POST['last_name'],
                    username=request.POST['username'],
                    email=request.POST['email'],
                    password=make_password(request.POST['password']),
                    mobile=request.POST['mobile'],
                    city=request.POST['city'],
                    profile=request.FILES.get('profile'), # Fix: use get() to avoid KeyError if no file is uploaded
                    usertype = request.POST['usertype']          
                )
            
                msg = "User created successfully. Please log in."
                return render(request, 'login.html', {'msg': msg})
            else:
                msg = "Passwords do not match."
                return render(request, 'signup.html', {'msg': msg})
    else:
        return render(request, 'signup.html')    


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def login(request):
    if request.method == 'POST':
        user = User.objects.filter(email=request.POST['email']).first()
        if user:
            # Secure verification: check hashed password, fallback to plaintext check for existing data
            is_correct = False
            if user.password.startswith('pbkdf2_') or user.password.startswith('bcrypt'):
                is_correct = check_password(request.POST['password'], user.password)
            else:
                is_correct = (user.password == request.POST['password'])
                if is_correct:
                    # Upgrade to hashed password dynamically
                    user.password = make_password(request.POST['password'])
                    user.save()

            if is_correct:
                request.session['email'] = user.email
                request.session['username'] = user.username
                request.session['profile'] = user.profile.url if user.profile else '/static/images/man.png'
                request.session['usertype'] = user.usertype
                return redirect('index')
            else:
                msg = "Incorrect password. Please try again."
                return render(request, 'login.html', {'msg': msg})
        else:
            msg = "Email does not exist. Please sign up."
            return render(request, 'login.html', {'msg': msg})

    else:                    
        return render(request,'login.html')


# Logout ------   
def logout(request):
    request.session.flush()
    return redirect('index')


# Forgot Password -------
def f_pass(request):
    if request.method == 'POST':
        email = request.POST['email']
        if User.objects.filter(email=email).exists():
            # Here you would typically generate an OTP and send it to the user's email

            user = User.objects.get(email=email)

            subject = "Travelix Password Reset OTP"
            otp = random.randint(1001, 9999)
            message = f"""
            Dear {user.first_name} {user.last_name},

            We received a request to reset your Travelix account password.

            Your One-Time Password (OTP) is: {str(otp)}

            This OTP is valid for the next 10 minutes. Please do not share it with anyone for security reasons.

            If you did not request a password reset, please ignore this email. Your account will remain secure.

            Thank you,
            Travelix Team
            """
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [user.email,]
            send_mail(subject, message, email_from, recipient_list)

            request.session['otp'] = otp
            request.session['otp_email'] = email

            msg = "An OTP has been sent to your email address."
            return render(request, 'verify_otp.html', {'msg': msg})
        else:
            msg = "Email does not exist. Please sign up."
            return render(request, 'f_pass.html', {'msg': msg})
    return render(request,'f_pass.html')


# Verify Otp ----
def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST['otp']
        session_otp = str(request.session.get('otp'))
        if entered_otp == session_otp:
            # OTP is correct, allow user to reset password
            del request.session['otp']  # Clear OTP from session
            msg = "OTP verified successfully. You can now reset your password."
            return render(request, 'reset_password.html', {'msg': msg})
        
        else:
            msg = "Invalid OTP. Please try again."
            return render(request, 'verify_otp.html', {'msg': msg})
    else:
        return render(request,'verify_otp.html')


# Reset Password ---------
def reset_password(request):
    email = request.session.get('otp_email')
    if not email:
        return redirect('login')

    if request.method == 'POST':
        user = User.objects.get(email=email)
        new_password = request.POST['password']
        confirm_password = request.POST['cpassword']

        if new_password == confirm_password:
            user.password = make_password(new_password)
            user.save()
            del request.session['otp_email']  # Clear email from session
            msg = "Password reset successfully. Please log in with your new password."
            return render(request, 'login.html', {'msg': msg})
        else:
            msg = "Passwords do not match. Please try again."
            return render(request, 'reset_password.html', {'msg': msg})
    else:
        return render(request,'reset_password.html')
    


# Update Profile ------
@login_required
def uprofile(request):
    user = User.objects.get(email=request.session['email'])
    
    if request.method == 'POST' :

        if request.FILES.get('profile'):
            user.profile = request.FILES['profile']
            user.save()
            request.session['profile'] = user.profile.url
        
        if request.POST.get('first_name'):
            user.first_name = request.POST['first_name']
        
        if request.POST.get('last_name'):
            user.last_name = request.POST['last_name']
        
        if request.POST.get('username'):
            user.username = request.POST['username']
            request.session['username'] = user.username
        
        if request.POST.get('mobile'):
            user.mobile = request.POST['mobile']

        if request.POST.get('city'):
            user.city = request.POST['city']
        
        if request.POST.get('password'):
            if request.POST.get('password') == request.POST.get('cpassword'):
                user.password = make_password(request.POST['password'])
            else:
                msg = "Passwords do not match. Please try again."
                return render(request, 'uprofile.html', {'msg': msg, 'user': user}) 
        user.save()
        msg = "Profile updated successfully."
        return render(request,'uprofile.html', {'msg': msg, 'user': user})
    
    else:
        return render(request,'uprofile.html',{'user': user})


# Add-Car -------- for rent 
@login_required
def add_car(request):
    if request.method == "POST":
        try:
            user = User.objects.get(email=request.session['email'])

            Car.objects.create(
                user = user,

                brand=request.POST.get('brand'),
                model=request.POST.get('model'),
                year=request.POST.get('year'),
                color=request.POST.get('color'),
                number_plate=request.POST.get('number_plate'),
                seats=request.POST.get('seats'),
                car_type=request.POST.get('car_type'),
                fuel_type=request.POST.get('fuel_type'),
                transmission=request.POST.get('transmission'),

                # Features
                has_ac='has_ac' in request.POST,
                has_gps='has_gps' in request.POST,
                has_music='has_music' in request.POST,
                has_bluetooth='has_bluetooth' in request.POST,
                has_usb='has_usb' in request.POST,
                has_sunroof='has_sunroof' in request.POST,
                has_rear_camera='has_rear_camera' in request.POST,
                has_airbags='has_airbags' in request.POST,
                has_abs='has_abs' in request.POST,
                has_cruise='has_cruise' in request.POST,
                has_power_windows='has_power_windows' in request.POST,
                has_central_lock='has_central_lock' in request.POST,
                has_parking_sensor='has_parking_sensor' in request.POST,
                has_spare_tyre='has_spare_tyre' in request.POST,
                has_first_aid='has_first_aid' in request.POST,

                price_per_day=request.POST.get('price_per_day'),
                city=request.POST.get('city'),
                pickup_address=request.POST.get('pickup_address'),
                main_photo=request.FILES.get('main_photo'),
                description=request.POST.get('description'),
            )

            msg = "Add_car succefully !!"

            return render(request,"add_car.html",{'msg' : msg})  # apne URL name ke hisab se change karna
        except Exception as e :
            print(e)
            return render(request, 'add_car.html', {'msg': f"Error adding car: {e}"})

    else:
        return render(request, 'add_car.html')
    



# Edit Car Function ------
@login_required
def edit_car(request, pk):
    car = Car.objects.get(id=pk)

    if request.method == "POST":

        car.brand = request.POST.get('brand')
        car.model = request.POST.get('model')
        car.year = request.POST.get('year')
        car.color = request.POST.get('color')
        car.number_plate = request.POST.get('number_plate')
        car.seats = request.POST.get('seats')
        car.car_type = request.POST.get('car_type')
        car.fuel_type = request.POST.get('fuel_type')
        car.transmission = request.POST.get('transmission')

        # Features
        car.has_ac = 'has_ac' in request.POST
        car.has_gps = 'has_gps' in request.POST
        car.has_music = 'has_music' in request.POST
        car.has_bluetooth = 'has_bluetooth' in request.POST
        car.has_usb = 'has_usb' in request.POST
        car.has_sunroof = 'has_sunroof' in request.POST
        car.has_rear_camera = 'has_rear_camera' in request.POST
        car.has_airbags = 'has_airbags' in request.POST
        car.has_abs = 'has_abs' in request.POST
        car.has_cruise = 'has_cruise' in request.POST
        car.has_power_windows = 'has_power_windows' in request.POST
        car.has_central_lock = 'has_central_lock' in request.POST
        car.has_parking_sensor = 'has_parking_sensor' in request.POST
        car.has_spare_tyre = 'has_spare_tyre' in request.POST
        car.has_first_aid = 'has_first_aid' in request.POST

        car.price_per_day = request.POST.get('price_per_day')
        car.city = request.POST.get('city')
        car.pickup_address = request.POST.get('pickup_address')
        car.description = request.POST.get('description')

        # Photo update (optional)
        if request.FILES.get('main_photo'):
            car.main_photo = request.FILES.get('main_photo')

        car.save()

        msg = "Car Updated Successfully !!"
        return render(request, 'edit_car.html', {
            'car': car,
            'msg': msg
        })

    else:
        return render(request, 'edit_car.html', { 'car': car })
    




 # View-car Function
@login_required
def view_car(request):
    user = User.objects.get(email = request.session['email'])
    cars = Car.objects.filter(user = user)

    return render(request,"view_car.html",{'cars' : cars})


# Rent Car ------------
def rent_car(request):
    cars = Car.objects.all()

    wishlist_ids = []

    if 'email' in request.session:
        user = User.objects.get(email=request.session['email'])

        wishlist_ids = Wishlist.objects.filter(
            user=user
        ).values_list('car_id', flat=True)

    return render(request, 'rent_car.html', {
        'cars': cars,
        'wishlist_ids': wishlist_ids
    })


# delete-car --------
@login_required
def delete_car(request,pk):
    user = User.objects.get(email = request.session['email'])
    car = Car.objects.get(pk=pk, user=user)
    car.delete()
    return redirect('index')



# Add Wishlist Function ---------
@login_required
def add_wishlist(request,pk):
    user = User.objects.get(email=request.session['email'])
    car = Car.objects.get(pk=pk)

    if not Wishlist.objects.filter(user=user, car=car).exists():
        Wishlist.objects.create(
            user=user,
            car=car
        )

    return redirect(request.META.get('HTTP_REFERER', 'rent_car'))

# wishlist --------------
@login_required
def wishlist(request):
    user = User.objects.get(email = request.session['email'])
    wishlist = Wishlist.objects.filter(user=user)

    request.session['wishlist'] = wishlist.count()
    return render(request, "wishlist.html" , {'wishlist' : wishlist})


# delet Wishlist--------
@login_required
def delete_wishlist(request,pk):
    user = User.objects.get(email=request.session['email'])
    car = Car.objects.get(pk=pk)
    
    wishlists = Wishlist.objects.filter(user=user, car=car)
    if wishlists.exists():
        wishlists.delete()

    return redirect(request.META.get('HTTP_REFERER', 'rent_car'))


# book car -----------
@login_required
def book_car(request,pk):
    user = User.objects.get(email=request.session['email'])
    car = Car.objects.get(pk=pk)

    if request.method == "POST":
        # Clear existing unpaid items in the cart to isolate this booking
        Cart.objects.filter(user=user, payment=False).delete()
        # Add the selected car to the cart
        Cart.objects.create(
            user=user,
            car=car,
            tprice=car.price_per_day,
            dprice=car.price_per_day,
            payment=False
        )
        # Store form details in session
        request.session['cart_booking_data'] = {
            'full_name': request.POST.get('full_name'),
            'email': request.POST.get('email'),
            'mobile': request.POST.get('mobile'),
            'pickup_date': request.POST.get('pickup_date'),
            'return_date': request.POST.get('return_date'),
            'note': request.POST.get('note', '')
        }
        return redirect('cart_booking_summary')

    return render(request,'book_car.html',{'car':car , 'user': user})





# add cart--------
@login_required
def addcart(request,pk):
    user = User.objects.get(email=request.session['email'])
    car = Car.objects.get(pk=pk)

    # Check if the car is already in the cart to prevent duplicates
    if not Cart.objects.filter(user=user, car=car, payment=False).exists():
        Cart.objects.create(
                    user = user,
                    car = car,
                    tprice = car.price_per_day,
                    dprice = car.price_per_day,
                    payment = False
        )

    return redirect("scart")


@login_required
def delet_cart(request,pk):
    user = User.objects.get(email = request.session['email'])
    car = Car.objects.get(pk=pk)
    c = Cart.objects.get(user=user,car=car,payment=False)

    c.delete()

    return redirect("scart")




@login_required
def scart(request):
    user = User.objects.get(email=request.session['email'])

    carts = Cart.objects.filter(user=user,payment=False)

    total_amount = 0
    for item in carts:
        total_amount += item.tprice

    payment = None
    if total_amount > 0:
        # Razorpay Client
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        # Razorpay Order
        payment = client.order.create({
            "amount": int(total_amount * 100),   # Rupees -> Paise
            "currency": "INR",
            "payment_capture": 1
        })

    context = {
        "user": user,
        "carts": carts,
        "total_amount": total_amount,
        "payment": payment,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
    }

    return render(request, "scart.html", context)




@login_required
def sucess(request):
    user = User.objects.get(email=request.session['email'])
    cart = Cart.objects.filter(user=user, payment=False)
    for i in cart:
        i.payment=True
        i.save()
    return render(request,'succes.html',{'cart':cart})

@login_required
def myorder(request):
    user = User.objects.get(email=request.session['email'])
    cart=Cart.objects.filter(user=user,payment=True)
    return render(request,'myorder.html',{'cart':cart})

def about(request):
    return render(request,'about.html')

def contact(request):
    return render(request,'contact.html')