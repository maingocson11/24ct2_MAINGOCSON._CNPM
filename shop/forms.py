from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import Order, Product, ProductImage, Review, User, Variant


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ["username", "first_name", "email", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email đã được sử dụng.")
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "address"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Email đã được sử dụng.")
        return email


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["image", "caption"]

    def clean_image(self):
        image = self.cleaned_data["image"]
        if image.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Ảnh tối đa 5 MB.")
        if image.image.format not in ("JPEG", "PNG", "WEBP"):
            raise forms.ValidationError("Chỉ chấp nhận ảnh JPEG, PNG hoặc WebP.")
        return image


class CheckoutForm(forms.ModelForm):
    phone = forms.CharField(label="Số điện thoại", validators=[RegexValidator(r"^0[0-9]{9,10}$", "Nhập số điện thoại 10–11 chữ số, bắt đầu bằng 0.")])

    class Meta:
        model = Order
        fields = ["recipient", "phone", "address", "note"]
        widgets = {"note": forms.Textarea(attrs={"rows": 3})}


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "description", "price", "original_price", "image_url", "color", "artwork", "active"]


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "content"]
        widgets = {"content": forms.Textarea(attrs={"rows": 3})}


VariantFormSet = forms.inlineformset_factory(Product, Variant, fields=["color", "size", "stock"], extra=4, can_delete=False, min_num=1, validate_min=True)
