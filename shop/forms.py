from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import ManualPayment

User = get_user_model()

class CustomerSignUpForm(UserCreationForm):
    phone_number = forms.CharField(required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username','email','phone_number','address')

class VendorSignUpForm(UserCreationForm):
    display_name = forms.CharField(required=True)
    phone_number = forms.CharField(required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username','email','phone_number','address')

class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(widget=forms.Textarea(attrs={'rows':3}))
    payment_method = forms.ChoiceField(choices=[('cod','Cash on Delivery'),('manual','Manual Deposit')])
    msisdn = forms.CharField(required=False, help_text='Phone number for payment reference (optional)')

class ManualPaymentForm(forms.ModelForm):
    class Meta:
        model = ManualPayment
        fields = ['payer_name','msisdn','method','reference_code','receipt_image']