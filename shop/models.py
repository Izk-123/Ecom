from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    CUSTOMER, VENDOR, ADMIN = 'customer', 'vendor', 'admin'
    ROLE_CHOICES = [(CUSTOMER,'Customer'),(VENDOR,'Vendor'),(ADMIN,'Admin')]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=CUSTOMER)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    vendor_approved = models.BooleanField(default=False)

    @property
    def is_vendor(self):
        return self.role == self.VENDOR

    @property
    def is_admin(self):
        return self.is_superuser or self.role == self.ADMIN

class Product(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price_mwk = models.PositiveIntegerField()
    stock_quantity = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return self.name

# New model for product images
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')

class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.PROTECT)
    total_amount_mwk = models.PositiveIntegerField(default=0)
    payment_status = models.CharField(max_length=16, default='pending')  # pending|paid|failed
    delivery_status = models.CharField(max_length=16, default='pending')
    payment_method = models.CharField(max_length=12, default='cod')      # cod|manual
    shipping_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price_mwk = models.PositiveIntegerField()
    @property
    def line_total(self): return self.quantity * self.unit_price_mwk

class Payment(models.Model):
    order = models.ForeignKey(Order, related_name='payments', on_delete=models.PROTECT, null=True, blank=True)
    provider = models.CharField(max_length=16)  # cod|manual
    amount_mwk = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, default='initiated')  # initiated|pending|success|failed
    created_at = models.DateTimeField(auto_now_add=True)

class ManualPayment(models.Model):
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL)
    payer_name = models.CharField(max_length=120)
    msisdn = models.CharField(max_length=20)
    method = models.CharField(max_length=20)  # bank_deposit|mobile_money|other
    reference_code = models.CharField(max_length=64)
    receipt_image = models.ImageField(upload_to='receipts/', blank=True)
    status = models.CharField(max_length=20, default='submitted')  # submitted|approved|rejected
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance_mwk = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet"