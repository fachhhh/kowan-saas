from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import Product, Tenant, User


class BootstrapMixin:
    """Tambahkan class Bootstrap ke semua field."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class LoginForm(BootstrapMixin, AuthenticationForm):
    pass


class RegisterTenantForm(BootstrapMixin, UserCreationForm):
    nama_tenant = forms.CharField(max_length=100, label='Nama toko / tenant')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)

    def clean_nama_tenant(self):
        nama = self.cleaned_data['nama_tenant'].strip()
        if Tenant.objects.filter(nama__iexact=nama).exists():
            raise forms.ValidationError('Nama tenant sudah dipakai.')
        return nama

    def save(self, commit=True):
        user = super().save(commit=False)
        tenant = Tenant.objects.create(nama=self.cleaned_data['nama_tenant'])
        user.tenant = tenant
        if commit:
            user.save()
        return user


class ProductForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = ('nama', 'harga', 'stok', 'deskripsi')
        widgets = {'deskripsi': forms.Textarea(attrs={'rows': 3})}