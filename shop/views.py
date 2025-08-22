# shop/views.py (updated, added formset handling)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth import logout
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.forms import inlineformset_factory  # Added for formsets
from django.contrib import messages
from .models import Product, Order, OrderItem, Payment, ManualPayment, User, Wallet, ProductImage  # Added ProductImage
from .forms import CheckoutForm, ManualPaymentForm, CustomerSignUpForm, VendorSignUpForm

# Inline formset for product images (allows multiple uploads)
ProductImageFormSet = inlineformset_factory(
    Product, ProductImage, fields=('image',), extra=3, can_delete=True, max_num=10  # Basic: Up to 10 images, 3 forms shown
)

# Public views
def home(request):
    qs = Product.objects.order_by('-id')
    paginator = Paginator(qs, 12)
    page = request.GET.get('page')
    return render(request, 'home.html', {'page_obj': paginator.get_page(page)})

def product_detail(request, slug):
    obj = get_object_or_404(Product, slug=slug)
    return render(request, 'product_detail.html', {'object': obj})

# session cart
def add_to_cart(request):
    if request.method == 'POST':
        pid = str(request.POST.get('product_id'))
        qty = int(request.POST.get('qty', 1))
        cart = request.session.get('cart', {})
        cart[pid] = cart.get(pid, 0) + qty
        request.session['cart'] = cart
    return redirect('checkout')

# Signup flows

def signup_customer(request):
    if request.method == 'POST':
        form = CustomerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.CUSTOMER
            user.is_active = True
            user.save()
            login(request, user)
            return redirect('dashboard_customer')
    else:
        form = CustomerSignUpForm()
    return render(request, 'auth/signup_customer.html', {'form': form})

def signup_vendor(request):
    if request.method == 'POST':
        form = VendorSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.VENDOR
            user.is_active = True
            user.vendor_approved = False
            user.save()
            # notify admin by email (console backend prints it)
            from django.core.mail import send_mail
            send_mail('New vendor signup', f'Vendor {user.username} signed up. Approve in admin.', 'noreply@example.com', ['admin@example.com'])
            login(request, user)
            return redirect('dashboard_vendor')
    else:
        form = VendorSignUpForm()
    return render(request, 'auth/signup_vendor.html', {'form': form})

# Checkout & orders (unchanged)
@login_required
@transaction.atomic
def checkout(request):
    cart = request.session.get('cart', {})
    products = Product.objects.select_for_update().filter(id__in=cart.keys())
    lines, total = [], 0
    for p in products:
        qty = int(cart.get(str(p.id), 0))
        if qty <= 0: continue
        lines.append({'product': p, 'qty': qty, 'line_total': p.price_mwk*qty})
        total += p.price_mwk*qty

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid() and products:
            order = Order.objects.create(
                customer=request.user,
                shipping_address=form.cleaned_data['shipping_address'],
                payment_method=form.cleaned_data['payment_method'],
                total_amount_mwk=0,
            )
            for p in products:
                qty = int(cart.get(str(p.id), 0))
                if qty <= 0: continue
                OrderItem.objects.create(order=order, product=p, quantity=qty, unit_price_mwk=p.price_mwk)
                p.stock_quantity = max(0, p.stock_quantity - qty)
                p.save(update_fields=['stock_quantity'])
            order.total_amount_mwk = total
            order.save(update_fields=['total_amount_mwk'])

            if order.payment_method == 'cod':
                Payment.objects.create(order=order, provider='cod', amount_mwk=total, status='pending')
            else:
                Payment.objects.create(order=order, provider='manual', amount_mwk=total, status='initiated')
            request.session['cart'] = {}
            return redirect('thank_you', order_id=order.id)
    else:
        form = CheckoutForm()

    return render(request, 'checkout.html', {'form': form, 'lines': lines, 'total': total})

@login_required
def thank_you(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'thank_you.html', {'order': order})

# Manual payments
@login_required
def manual_submit(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    if request.method == 'POST':
        form = ManualPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            mp = form.save(commit=False)
            mp.order = order
            mp.save()
            return redirect('thank_you', order_id=order.id)
    else:
        form = ManualPaymentForm()
    return render(request, 'manual_submit.html', {'form': form, 'order': order})

# Vendor views
@login_required
def vendor_orders(request):
    if not getattr(request.user, 'is_vendor', False):
        return redirect('home')
    qs = Order.objects.filter(items__product__vendor=request.user).distinct().order_by('-id')
    return render(request, 'vendor_orders.html', {'orders': qs})

@login_required
def vendor_cod_collected(request, order_id):
    if not getattr(request.user, 'is_vendor', False):
        return redirect('home')
    o = get_object_or_404(Order, id=order_id)
    if o.payment_method == 'cod' and o.payment_status != 'paid':
        Payment.objects.create(order=o, provider='cod', amount_mwk=o.total_amount_mwk, status='success')
        o.payment_status = 'paid'
        o.save(update_fields=['payment_status'])
    return redirect('vendor_orders')

# Admin manual payment review
@user_passes_test(lambda u: u.is_staff or getattr(u,'is_admin',False))
def manual_review(request):
    q = ManualPayment.objects.filter(status='submitted').order_by('-id')
    return render(request, 'manual_review.html', {'items': q})

@user_passes_test(lambda u: u.is_staff or getattr(u,'is_admin',False))
def manual_review_action(request, mp_id, action):
    mp = get_object_or_404(ManualPayment, id=mp_id)
    if action == 'approve':
        mp.status = 'approved'
        mp.reviewed_by = request.user
        mp.reviewed_at = timezone.now()
        mp.save(update_fields=['status','reviewed_by','reviewed_at'])
        if mp.order:
            o = mp.order
            o.payment_status = 'paid'
            o.save(update_fields=['payment_status'])
    elif action == 'reject':
        mp.status = 'rejected'
        mp.reviewed_by = request.user
        mp.reviewed_at = timezone.now()
        mp.save(update_fields=['status','reviewed_by','reviewed_at'])
    return redirect('manual_review')

# Dashboards
@login_required
def dashboard_customer(request):
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'dashboards/customer.html', {'orders': orders})

@login_required
def dashboard_vendor(request):
    if not getattr(request.user, 'is_vendor', False):
        return redirect('home')
    products = Product.objects.filter(vendor=request.user)
    orders = Order.objects.filter(items__product__vendor=request.user).distinct().order_by('-id')
    return render(request, 'dashboards/vendor.html', {'products': products, 'orders': orders})

@login_required
def dashboard_admin(request):
    if not request.user.is_staff:
        return redirect('home')
    vendors_pending = User.objects.filter(role=User.VENDOR, vendor_approved=False)
    manual_payments = ManualPayment.objects.filter(status='submitted')
    return render(request, 'dashboards/admin.html', {'vendors_pending': vendors_pending, 'manual_payments': manual_payments})

def custom_logout(request):
    logout(request)
    return redirect('logout_success')

def logout_success(request):
    return render(request, 'auth/logout.html')

@login_required
def vendor_product_list(request):
    if not request.user.is_vendor:
        return redirect('home')
    products = Product.objects.filter(vendor=request.user)
    return render(request, 'vendor_product_list.html', {'products': products})

class ProductCreateView(CreateView):
    model = Product
    fields = ['name', 'slug', 'description', 'price_mwk', 'stock_quantity', 'category']
    template_name = 'product_form.html'
    success_url = reverse_lazy('vendor_product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ProductImageFormSet(self.request.POST, self.request.FILES)
        else:
            context['formset'] = ProductImageFormSet()
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.vendor = self.request.user
        self.object.save()
        formset = ProductImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if formset.is_valid():
            formset.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

class ProductUpdateView(UpdateView):
    model = Product
    fields = ['name', 'slug', 'description', 'price_mwk', 'stock_quantity', 'category']
    template_name = 'product_form.html'
    success_url = reverse_lazy('vendor_product_list')

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ProductImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['formset'] = ProductImageFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        form.save()
        formset = ProductImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if formset.is_valid():
            formset.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'product_confirm_delete.html'
    success_url = reverse_lazy('vendor_product_list')

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user)

@login_required
def approve_vendor(request, user_id):
    if not request.user.is_admin:
        return redirect('home')
    vendor = get_object_or_404(User, id=user_id, role=User.VENDOR)
    vendor.vendor_approved = True
    vendor.save()
    messages.success(request, f"Vendor {vendor.username} has been approved successfully!")
    return redirect('dashboard_admin')

# views.py
@login_required
def wallet_detail(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    return render(request, 'wallet_detail.html', {'wallet': wallet})

@login_required
def topup_wallet(request):
    if request.method == 'POST':
        amount = int(request.POST.get('amount', 0))
        if amount > 0:
            wallet = Wallet.objects.get(user=request.user)
            wallet.balance_mwk += amount
            wallet.save()
            return redirect('wallet_detail')
    return render(request, 'topup_wallet.html')