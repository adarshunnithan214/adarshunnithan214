from django.shortcuts import render,redirect
from shop.models import Product
from shop.models import Categories
from cart.models import Cart
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
import razorpay
from cart.models import Payment
from cart.models import Order_details
from django.views.decorators.csrf import csrf_exempt

@login_required
def addtocart(request,i):
    p=Product.objects.get(id=i)
    u=request.user
    try:
        c=Cart.objects.get(product=p,user=u)
        if(p.stock>0):
              c.quality+=1
              c.save()
              p.stock-=1
              p.save()
    except:
        if(p.stock>0):
              c=Cart.objects.create(product=p,user=u,quality=1)
              c.save()
              p.stock-=1
              p.save()

    return redirect('cart:cart')

def cart_view(request):
     u = request.user
     c = Cart.objects.filter(user=u)
     total = 0
     for i in c:
            total += i.quality*i.product.price
            context={'cart':c, 'total': total}
     return render(request, 'cart.html',context)

@login_required
def cart_remove(request,i):

    p=Product.objects.get(id=i)
    u=request.user

    try:
        c=Cart.objects.get(product=p,user=u)
        if(c.quality>1):
            c.quality-=1
            c.save()
            p.stock+=1
            p.save()
        else:
            c.delete()
            p.stock += 1
            p.save()
    except:
        pass

    return redirect('cart:cart')

@login_required
def cart_delete(request,i):

    p=Product.objects.get(id=i)
    u=request.user

    try:
        c = Cart.objects.get(product=p, user=u)
        c.delete()
        p.stock += c.quantity
        p.save()
    except:
        pass

    return redirect('cart:cart')

@login_required
def order_form(request):
    if(request.method=="POST"):
        address=request.POST['a']
        phone=request.POST['p']
        pin=request.POST['pi']
        u=request.user
        c=Cart.objects.filter(user=u)
        total=0
        for i in c:
            total+=i.quality*i.product.price
        total1=int(total*100)
        print(total)
        client=razorpay.Client(auth=('rzp_test_37h3t9ZIGC5fDa','qfxNvjz8OoxUOx10xeltJIGO'))
        response_payment=client.order.create(dict(amount=total1,currency="INR"))
        print(response_payment)
        order_id=response_payment['id']
        status=response_payment['status']

        if(status=="created"):
            p=Payment.objects.create(name=u.username,amount=total,order_id=order_id)
            p.save()
            for i in c:
                o = Order_details.objects.create(products=i.product, user=u, no_of_items=i.quality, address=address, pin=pin,phone_no=phone, order_id=order_id)
                o.save()
            response_payment['name'] = u.username
        context = {'payment': response_payment}
        return render(request, 'payment.html',context)

    return render(request,'orderform.html')

@csrf_exempt
def payment_status(request,u):
  u= User.objects.get(username=u)
  if not request.user.is_authenticated:
    login(request,u)

  if(request.method=="POST"):
    response=request.POST
    print(response)
    param_dict={
         'razorpay_order_id':response['razorpay_order_id'],
         'razorpay_payment_id': response['razorpay_payment_id'],
         'razorpay_signature': response['razorpay_signature'],
      }#to check the authentication of rayzorpay signature
    client=razorpay.Client(auth=('rzp_test_37h3t9ZIGC5fDa','qfxNvjz8OoxUOx10xeltJIGO'))
    print(client)
    try:
        status=client.utility.verify_payment_signature(param_dict)
        print(status)

        p = Payment.objects.get(order_id=response['razorpay_order_id'])
        p.razorpay_payment_id = response['razorpay_payment_id']
        p.paid = True
        p.save()

        o = Order_details.objects.filter(order_id=response['razorpay_order_id'])
        print(o)
        for i in o:
            i.payment_status = "completed"
            i.save()

            u=User.objects.get(username=u)
            c=Cart.objects.filter(user=u)
            c.delete()
    except:
        pass

  return render(request,'payment_status.html',{'status':status})

@login_required()
def order_view(request):
    u=request.user
    o=Order_details.objects.filter(user=u)
    context={'orders':o}
    return render(request,'orderview.html',context)

@login_required()
def add_categories(request):
    if(request.method=="POST"):
        n=request.POST['n']
        d=request.POST['d']
        i=request.FILES['i']
        c=Categories.objects.create(name=n,description=d,image=i)
        c.save()
        return redirect('shop:categories')
    return render(request,'addcategories.html',)

@login_required()
def add_products(request):
    if (request.method == "POST"):
        n = request.POST['n']
        d = request.POST['d']
        i = request.FILES['i']
        p = request.POST['p']
        s = request.POST['s']
        c = request.POST['c']

        cat=Categories.objects.get(name=c)
        p = Product.objects.create(name=n,desc=d,image=i,price=p,stock=s,category=cat)
        p.save()
        return redirect('shop:categories')
    return render(request,'addproducts.html',)

