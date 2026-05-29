import stripe
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .models import ApparelProduct, CustomerOrder
from .tasks import process_global_fulfillment

class CachedCatalogView(APIView):
    """Serves the drop clothing catalog straight out of hot memory cache."""
    @method_decorator(cache_page(60 * 5)) # Caches catalog views globally for 5 minutes
    def get(self, request):
        products = ApparelProduct.objects.filter(collection__is_live=True)
        data = [{
            "id": p.id, "title": p.title, "price": str(p.price), 
            "sku": p.global_sku, "description": p.description
        } for p in products]
        return Response(data, status=status.HTTP_200_OK)


class SecureStripeWebhookView(APIView):
    """Handles real-time payment authentication directly from global financial networks."""
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response({"error": "Invalid cryptographic handshake"}, status=status.HTTP_400_BAD_REQUEST)
            
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Process order states within safe database isolation loops
            order, created = CustomerOrder.objects.get_or_create(
                stripe_session_id=session['id'],
                defaults={
                    'email': session['customer_details']['email'],
                    'shipping_details': {
                        'name': session['shipping_details']['name'],
                        'line1': session['shipping_details']['address']['line1'],
                        'city': session['shipping_details']['address']['city'],
                        'country': session['shipping_details']['address']['country'],
                        'postal_code': session['shipping_details']['address']['postal_code'],
                    },
                    'is_paid': True,
                    'fulfillment_status': 'Payment Captured'
                }
            )
            
            if not created:
                order.is_paid = True
                order.save()
                
            # Offload heavy tasks to Celery immediately to keep the request path fast
            process_global_fulfillment.delay(order.id)
            
        return Response({"status": "success"}, status=status.HTTP_200_OK)