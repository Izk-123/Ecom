from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Product, Order, OrderItem, Payment, ManualPayment

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (("Role & Contact", {"fields": ("role","phone_number","address")}),)
    list_display = ('username','email','role','is_active','is_staff')
    list_filter = ('role','is_staff','is_active')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name','vendor','price_mwk','stock_quantity','category')
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ('name','description')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','customer','total_amount_mwk','payment_status','payment_method','created_at')
    inlines = [OrderItemInline]

admin.site.register(Payment)
admin.site.register(ManualPayment)