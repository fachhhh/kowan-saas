from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import ProductForm, RegisterTenantForm
from .models import Product

import json
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

def register(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.tenant_id is None:
            return redirect('admin:index')
        return redirect('product_list')
    if request.method == 'POST':
        form = RegisterTenantForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
            messages.success(request, f'Selamat datang! Toko/Tenant "{user.tenant.nama}" berhasil didaftarkan.')
            login(request, user)
            return redirect('product_list')
    else:
        form = RegisterTenantForm()
    return render(request, 'registration/register.html', {'form': form})


class TenantRequiredMixin(LoginRequiredMixin):
    """Wajib login DAN punya tenant."""
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.tenant_id is None:
            if request.user.is_superuser or request.user.is_staff:
                return redirect('admin:index')
            return HttpResponseForbidden('Akun ini tidak terhubung ke tenant manapun.')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # KUNCI ISOLASI: semua query otomatis difilter per tenant
        return Product.objects.filter(tenant=self.request.user.tenant)


class ProductListView(TenantRequiredMixin, ListView):
    model = Product
    context_object_name = 'products'


class ProductCreateView(TenantRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    success_url = reverse_lazy('product_list')
    success_message = 'Produk berhasil ditambahkan.'

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)


class ProductUpdateView(TenantRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    success_url = reverse_lazy('product_list')
    success_message = 'Produk berhasil diubah.'


class ProductDeleteView(TenantRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('product_list')

    def form_valid(self, form):
        messages.success(self.request, 'Produk berhasil dihapus.')
        return super().form_valid(form)

@login_required
@require_POST
def export_csv(request):
    tenant = request.user.tenant
    if tenant is None:
        return HttpResponseForbidden('Akun ini tidak terhubung ke tenant manapun.')

    # Hanya produk milik tenant sendiri yang dikirim ke Lambda
    produk = list(
        Product.objects.filter(tenant=tenant).values('nama', 'harga', 'stok', 'deskripsi')
    )
    payload = {'tenant_id': tenant.id, 'tenant_nama': tenant.nama, 'products': produk}

    try:
        client = boto3.client('lambda', region_name=settings.AWS_REGION)
        resp = client.invoke(
            FunctionName=settings.EXPORT_LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload).encode('utf-8'),
        )
        hasil = json.loads(resp['Payload'].read())
        if resp.get('FunctionError') or hasil.get('statusCode') != 200:
            raise RuntimeError(f'Lambda mengembalikan error: {hasil}')
        url = json.loads(hasil['body'])['url']
    except (BotoCoreError, ClientError, RuntimeError, ValueError, KeyError):
        logger.exception('Gagal ekspor CSV untuk tenant %s', tenant.id)
        messages.error(request, 'Gagal membuat file ekspor. Silakan coba lagi.')
        return redirect('product_list')

    return HttpResponseRedirect(url)