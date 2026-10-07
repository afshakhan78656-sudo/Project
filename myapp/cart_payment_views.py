from django.shortcuts import render, redirect
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import User, Car, Cart, Booking, BookedCar
from myapp.views import login_required
import razorpay
from datetime import datetime
from django.utils import timezone

@login_required
def cart_booking_details_view(request):
    user = User.objects.get(email=request.session['email'])
    carts = Cart.objects.filter(user=user, payment=False)
    if not carts.exists():
        return redirect('scart')

    if request.method == 'POST':
        # Store form data in session
        request.session['cart_booking_data'] = {
            'full_name': request.POST.get('full_name'),
            'email': request.POST.get('email'),
            'mobile': request.POST.get('mobile'),
            'pickup_date': request.POST.get('pickup_date'),
            'return_date': request.POST.get('return_date'),
            'note': request.POST.get('note', '')
        }
        return redirect('cart_booking_summary')

    booking_data = request.session.get('cart_booking_data', {})
    return render(request, 'cart_booking_details.html', {
        'carts': carts,
        'booking_data': booking_data
    })


@login_required
def cart_booking_summary_view(request):
    user = User.objects.get(email=request.session['email'])
    carts = Cart.objects.filter(user=user, payment=False)
    if not carts.exists():
        return redirect('scart')

    booking_data = request.session.get('cart_booking_data')
    if not booking_data:
        return redirect('cart_booking_details')

    # Calculate days
    try:
        p_date = datetime.strptime(booking_data['pickup_date'], '%Y-%m-%d')
        r_date = datetime.strptime(booking_data['return_date'], '%Y-%m-%d')
        delta = r_date - p_date
        total_days = max(1, delta.days)
    except Exception:
        total_days = 1

    # Calculate totals
    items_summary = []
    grand_total = 0
    for item in carts:
        car_total = item.car.price_per_day * total_days
        grand_total += car_total
        items_summary.append({
            'car': item.car,
            'price_per_day': item.car.price_per_day,
            'total_price': car_total
        })

    booking_data['total_days'] = total_days
    booking_data['grand_total'] = float(grand_total)
    request.session['cart_booking_data'] = booking_data

    # Generate a pending booking in the database to have a stable Booking ID
    # Clear older pending bookings for this user to avoid clutter
    # Booking.objects.filter(user=user, booking_status='Pending Payment').delete()

    booking = Booking.objects.create(
        user=user,
        full_name=booking_data['full_name'],
        email=booking_data['email'],
        mobile=booking_data['mobile'],
        note=booking_data['note'],
        total_days=total_days,
        grand_total=grand_total,
        booking_status='Pending Payment',
        payment_status='Pending'
    )

    # Save booked cars
    for item in carts:
        BookedCar.objects.create(
            booking=booking,
            car=item.car,
            price_per_day=item.car.price_per_day,
            total_price=item.car.price_per_day * total_days,
            pickup_date=p_date.date(),
            return_date=r_date.date()
        )

    # Create Razorpay Order
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    payment = client.order.create({
        "amount": int(grand_total * 100),
        "currency": "INR",
        "payment_capture": 1
    })

    # Update order ID
    booking.razorpay_order_id = payment['id']
    booking.save()

    return render(request, 'cart_booking_summary.html', {
        'booking': booking,
        'items_summary': items_summary,
        'booking_data': booking_data,
        'grand_total': grand_total,
        'payment': payment,
        'razorpay_key': settings.RAZORPAY_KEY_ID
    })


@csrf_exempt
@login_required
def cart_booking_payment_handler(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        user = User.objects.get(email=request.session['email'])
        try:
            client.utility.verify_payment_signature(params_dict)
            
            # Retrieve booking and update status
            booking = Booking.objects.get(user=user, razorpay_order_id=order_id)
            booking.booking_status = 'Confirmed'
            booking.payment_status = 'Success'
            booking.razorpay_payment_id = payment_id
            booking.razorpay_signature = signature
            booking.save()

            # Clear user cart
            Cart.objects.filter(user=user, payment=False).delete()

            # Save booking info in session for success redirect
            request.session['last_booking_id'] = booking.id

            if 'cart_booking_data' in request.session:
                del request.session['cart_booking_data']

            return redirect('cart_booking_success')

        except Exception as e:
            print("Razorpay payment validation signature mismatch:", e)
            booking = Booking.objects.filter(user=user, razorpay_order_id=order_id).first()
            if booking:
                booking.payment_status = 'Failed'
                booking.booking_status = 'Pending Payment'
                booking.save()
                return redirect(f'/cart-booking-failed/?booking_id={booking.id}&error=Signature+Verification+Failed')
            return redirect('scart')

    return redirect('scart')


@login_required
def cart_booking_success_view(request):
    booking_id = request.session.get('last_booking_id')
    if not booking_id:
        return redirect('my_bookings')
        
    user = User.objects.get(email=request.session['email'])
    booking = Booking.objects.get(user=user, id=booking_id)
    
    return render(request, 'cart_booking_success.html', {
        'booking': booking,
        'payment_time': timezone.now()
    })


@login_required
def cart_booking_failed_view(request):
    user = User.objects.get(email=request.session['email'])
    booking_id = request.GET.get('booking_id')
    error_msg = request.GET.get('error', 'Payment transaction failed.')

    booking = None
    payment = None
    if booking_id:
        # Keep booking as failed/pending payment
        booking = Booking.objects.filter(user=user, id=booking_id).first()
        if booking:
            booking.payment_status = 'Failed'
            booking.booking_status = 'Pending Payment'
            booking.save()

            # Re-generate Razorpay Order for retry
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            payment = client.order.create({
                "amount": int(booking.grand_total * 100),
                "currency": "INR",
                "payment_capture": 1
            })
            booking.razorpay_order_id = payment['id']
            booking.save()

    return render(request, 'cart_booking_failed.html', {
        'booking': booking,
        'payment': payment,
        'error_msg': error_msg,
        'razorpay_key': settings.RAZORPAY_KEY_ID
    })


@login_required
def my_bookings_view(request):
    user = User.objects.get(email=request.session['email'])
    bookings = Booking.objects.filter(user=user).order_by('-created_at')
    return render(request, 'my_bookings.html', {
        'bookings': bookings
    })
