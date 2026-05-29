import json
import requests
from celery import shared_task
from django.conf import settings
from .models import CustomerOrder

@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def process_global_fulfillment(self, order_id):
    """Asynchronously pushes verified purchases directly to global print-on-demand nodes."""
    try:
        order = CustomerOrder.objects.get(id=order_id)
        
        endpoint = "https://api.printful.com/orders"
        headers = {
            "Authorization": f"Bearer {settings.PRINTFUL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Structure payload to seamlessly map to manufacturing facility standards
        payload = {
            "recipient": {
                "name": order.shipping_details.get('name'),
                "address1": order.shipping_details.get('line1'),
                "city": order.shipping_details.get('city'),
                "country_code": order.shipping_details.get('country'),
                "zip": order.shipping_details.get('postal_code')
            },
            "items": order.shipping_details.get('cart_items_manifest', [])
        }
        
        response = requests.post(endpoint, data=json.dumps(payload), headers=headers)
        
        if response.status_code in [200, 201]:
            order.fulfillment_status = "Pushed to Global Factory"
            order.save()
        else:
            # Raise an exception to safely trigger automatic Celery worker retries
            raise Exception(f"Factory API rejected sync: {response.text}")
            
    except Exception as exc:
        raise self.retry(exc=exc)