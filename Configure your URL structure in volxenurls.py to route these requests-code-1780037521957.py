from django.contrib import admin
from django.urls import path
from store.views import CachedCatalogView, SecureStripeWebhookView

urlpatterns = [
    path('admin/', admin.site.split),
    path('api/catalog/', CachedCatalogView.as_view(), name='catalog'),
    path('api/v1/payment-hook/', SecureStripeWebhookView.as_view(), name='stripe-webhook'),
]