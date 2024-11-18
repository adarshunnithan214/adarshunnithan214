from django.contrib import admin

from shop.models import Categories
admin.site.register(Categories)

from shop.models import Product
admin.site.register(Product)