from django.contrib.auth.models import AbstractUser
from django.db import models


class Tenant(models.Model):
    nama = models.CharField(max_length=100, unique=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nama


class User(AbstractUser):
    # null=True agar superuser (admin platform) tidak wajib punya tenant
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='users'
    )


class Product(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='products')
    nama = models.CharField(max_length=150)
    harga = models.PositiveIntegerField(help_text='Dalam Rupiah')
    stok = models.PositiveIntegerField(default=0)
    deskripsi = models.TextField(blank=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diubah_pada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-dibuat_pada']

    def __str__(self):
        return f'{self.nama} ({self.tenant})'