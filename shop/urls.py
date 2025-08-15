from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    ProductCreateView, ProductDeleteView, ProductUpdateView, approve_vendor, home, product_detail, add_to_cart, checkout, thank_you, manual_submit, topup_wallet,
    vendor_orders, vendor_cod_collected, manual_review, manual_review_action,
    signup_customer, signup_vendor, dashboard_customer, dashboard_vendor, dashboard_admin, logout_success, custom_logout, vendor_product_list, wallet_detail
)

urlpatterns = [
    path('', home, name='home'),
    path('p/<slug:slug>/', product_detail, name='product_detail'),
    path('cart/add/', add_to_cart, name='add_to_cart'),
    path('checkout/', checkout, name='checkout'),
    path('orders/<int:order_id>/thank-you/', thank_you, name='thank_you'),

    # manual payments
    path('payments/manual/<int:order_id>/submit/', manual_submit, name='manual_submit'),
    path('admin/manual/review/', manual_review, name='manual_review'),
    path('admin/manual/review/<int:mp_id>/<str:action>/', manual_review_action, name='manual_review_action'),

    # auth
    path('accounts/login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/signup/customer/', signup_customer, name='signup_customer'),
    path('accounts/signup/vendor/', signup_vendor, name='signup_vendor'),
    path('accounts/logout/', custom_logout, name='logout'),
    path('accounts/logout/success/', logout_success, name='logout_success'),

    # dashboards
    path('dashboard/customer/', dashboard_customer, name='dashboard_customer'),
    path('dashboard/vendor/', dashboard_vendor, name='dashboard_vendor'),
    path('dashboard/admin/', dashboard_admin, name='dashboard_admin'),

    # Vendor product management
    path('vendor/products/', vendor_product_list, name='vendor_product_list'),
    path('vendor/products/add/', ProductCreateView.as_view(), name='product_create'),
    path('vendor/products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_update'),
    path('vendor/products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
    
    # Vendor approval
    path('admin/approve-vendor/<int:user_id>/', approve_vendor, name='approve_vendor'),
    
    # Wallet
    path('wallet/', wallet_detail, name='wallet_detail'),
    path('wallet/topup/', topup_wallet, name='topup_wallet'),
]