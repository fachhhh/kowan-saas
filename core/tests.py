from django.test import TestCase
from django.urls import reverse
from .models import Product, Tenant, User
import io
import json
from unittest.mock import patch

class IsolasiTenantTest(TestCase):
    def setUp(self):
        self.ta = Tenant.objects.create(nama='Toko A')
        self.tb = Tenant.objects.create(nama='Toko B')
        self.ua = User.objects.create_user('usera', password='pass12345', tenant=self.ta)
        self.ub = User.objects.create_user('userb', password='pass12345', tenant=self.tb)
        self.pa = Product.objects.create(tenant=self.ta, nama='Produk Milik A', harga=1000, stok=1)
        self.pb = Product.objects.create(tenant=self.tb, nama='Produk Milik B', harga=2000, stok=2)

    def test_harus_login(self):
        r = self.client.get(reverse('product_list'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login/', r.url)

    def test_list_hanya_milik_sendiri(self):
        self.client.login(username='usera', password='pass12345')
        r = self.client.get(reverse('product_list'))
        self.assertContains(r, 'Produk Milik A')
        self.assertNotContains(r, 'Produk Milik B')

    def test_edit_produk_tenant_lain_404(self):
        self.client.login(username='usera', password='pass12345')
        r = self.client.get(reverse('product_update', args=[self.pb.pk]))
        self.assertEqual(r.status_code, 404)

    def test_hapus_produk_tenant_lain_404(self):
        self.client.login(username='usera', password='pass12345')
        r = self.client.post(reverse('product_delete', args=[self.pb.pk]))
        self.assertEqual(r.status_code, 404)
        self.assertTrue(Product.objects.filter(pk=self.pb.pk).exists())

    def test_tambah_produk_masuk_tenant_sendiri(self):
        self.client.login(username='usera', password='pass12345')
        self.client.post(reverse('product_create'),
                         {'nama': 'Baru', 'harga': 500, 'stok': 3, 'deskripsi': ''})
        self.assertTrue(Product.objects.filter(nama='Baru', tenant=self.ta).exists())

    def test_superuser_tanpa_tenant_redirect_ke_admin(self):
        admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass123')
        self.client.login(username='admin', password='adminpass123')
        r = self.client.get(reverse('product_list'))
        self.assertRedirects(r, reverse('admin:index'))

    def test_get_views_produk(self):
        self.client.login(username='usera', password='pass12345')
        # GET create
        r_create = self.client.get(reverse('product_create'))
        self.assertEqual(r_create.status_code, 200)
        self.assertContains(r_create, 'Tambah Produk')

        # GET update
        r_update = self.client.get(reverse('product_update', args=[self.pa.pk]))
        self.assertEqual(r_update.status_code, 200)
        self.assertContains(r_update, 'Edit Produk')

        # GET delete
        r_delete = self.client.get(reverse('product_delete', args=[self.pa.pk]))
        self.assertEqual(r_delete.status_code, 200)
        self.assertContains(r_delete, 'Hapus produk?')

class ExportCsvTest(TestCase):
    def setUp(self):
        self.ta = Tenant.objects.create(nama='Toko A')
        self.tb = Tenant.objects.create(nama='Toko B')
        self.ua = User.objects.create_user('usera', password='pass12345', tenant=self.ta)
        Product.objects.create(tenant=self.ta, nama='Produk Milik A', harga=1000, stok=1)
        Product.objects.create(tenant=self.tb, nama='Produk Milik B', harga=2000, stok=2)

    def test_harus_login(self):
        r = self.client.post(reverse('product_export'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login/', r.url)

    def test_hanya_post(self):
        self.client.login(username='usera', password='pass12345')
        r = self.client.get(reverse('product_export'))
        self.assertEqual(r.status_code, 405)

    @patch('core.views.boto3.client')
    def test_hanya_kirim_produk_tenant_sendiri(self, mock_client):
        body = json.dumps({
            'statusCode': 200,
            'body': json.dumps({'url': 'https://contoh.s3.amazonaws.com/x.csv'}),
        })
        mock_client.return_value.invoke.return_value = {'Payload': io.BytesIO(body.encode())}

        self.client.login(username='usera', password='pass12345')
        r = self.client.post(reverse('product_export'))

        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, 'https://contoh.s3.amazonaws.com/x.csv')
        terkirim = json.loads(mock_client.return_value.invoke.call_args.kwargs['Payload'])
        nama = [p['nama'] for p in terkirim['products']]
        self.assertIn('Produk Milik A', nama)
        self.assertNotIn('Produk Milik B', nama)