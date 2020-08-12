from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

# Create your models here.

class Categories(models.Model):
    category_name = models.CharField(max_length=200)
    category_picture = models.ImageField(null=True, blank=True, upload_to='images/')
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.category_name

class Subcategories(models.Model):
    category = models.ForeignKey('Categories', on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    status = models.IntegerField(null=True)

    def __str__(self):
        return self.name


class Products(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    product_price = models.DecimalField(null=True, decimal_places=2, max_digits=10)
    product_quantity = models.IntegerField(null=True)
    product_description = models.TextField(null=True)
    product_image = models.ImageField(null=True)
    #product_color = models.CharField(max_length=50, null=True)
    #product_size = models.CharField(max_length=200, null=True)
    category = models.ForeignKey('Categories', null=True, on_delete=models.CASCADE)
    catalogue = models.ForeignKey('Catalogue', null=True, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

class Product_images(models.Model):
    product = models.ForeignKey('Products', null=True, on_delete=models.CASCADE)
    image = models.ImageField(null=True, blank=True, upload_to='images/')

    def __str__(self):
        return self.product.product_name + " Image"

