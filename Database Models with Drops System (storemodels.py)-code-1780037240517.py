import uuid
from django.db import models

class DropCollection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    is_live = models.BooleanField(default=False)
    go_live_at = models.DateTimeField()

    def __str__(self):
        return f"{self.name} - Live: {self.is_live}"

class ApparelProduct(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    collection = models.ForeignKey(DropCollection, on_delete=models.CASCADE, related_name="products")
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    global_sku = models.CharField(max_length=100, unique=True) # Essential for mapping to print factories

    def __str__(self):
        return self.title

class VariantInventory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(ApparelProduct, on_delete=models.CASCADE, related_name="variants")
    size = models.CharField(max_length=10, choices=[('S','S'), ('M','M'), ('L','L'), ('XL','XL'), ('XXL','XXL')])
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'size')

class CustomerOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stripe_session_id = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    shipping_details = models.JSONField(default=dict)
    is_paid = models.BooleanField(default=False)
    fulfillment_status = models.CharField(max_length=50, default="Pending Payment")
    created_at = models.DateTimeField(auto_now_add=True)