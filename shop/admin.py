from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import ProductImage, User, Product, Order, OrderItem, Payment, ManualPayment

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'vendor_approved')
    list_filter = ('role', 'vendor_approved')
    actions = ['approve_vendors']
    
    def approve_vendors(self, request, queryset):
        # Only approve vendors, not other users
        vendors = queryset.filter(role=User.VENDOR)
        updated = vendors.update(vendor_approved=True)
        self.message_user(request, f"{updated} vendors were approved.")
    approve_vendors.short_description = "Approve selected vendors"

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

# New inline for product images
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # Allows one extra form by default for uploading

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name','vendor','price_mwk','stock_quantity','category')
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ('name','description')
    inlines = [ProductImageInline]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','customer','total_amount_mwk','payment_status','payment_method','created_at')
    inlines = [OrderItemInline]

admin.site.register(Payment)
admin.site.register(ManualPayment)
admin.site.register(ProductImage)