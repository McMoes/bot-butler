import json
from decimal import Decimal
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import stripe
from django.conf import settings
from .models import Order, BotCategory
from .utils import process_order_notifications

stripe.api_key = settings.STRIPE_SECRET_KEY

@method_decorator(csrf_exempt, name='dispatch')
class CreateOrderView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'requires_login': True, 'error': 'Authentication required'}, status=401)

        try:
            data = json.loads(request.body)
            category_id = data.get('category_id')
            requirements = data.get('requirements_json', {})
            consulting_requested = data.get('consulting_requested', False)
            contact_info = data.get('contact_info', '')

            if not category_id:
                return JsonResponse({'error': 'Category ID is required'}, status=400)

            try:
                category = BotCategory.objects.get(pk=category_id)
            except BotCategory.DoesNotExist:
                return JsonResponse({'error': 'Invalid Category ID'}, status=400)

            # Price Calculation
            ai_price_estimate = Decimal(str(requirements.get('pricing_estimate', 0.00)))
            total_price = category.base_price + ai_price_estimate
            
            if consulting_requested:
                total_price += Decimal('150.00')

            # Create Order as pending
            order = Order.objects.create(
                user=request.user,
                category=category,
                requirements_json=requirements,
                consulting_requested=consulting_requested,
                contact_info=contact_info,
                total_price=total_price,
                status='pending'
            )

            # Create Stripe Checkout Session
            domain_url = request.build_absolute_uri('/')[:-1] # Remove trailing slash
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': f"Bot Butler - {category.name}",
                            'description': "Custom AI Automated Solution",
                        },
                        'unit_amount': int(total_price * 100), # Stripe expects cents
                    },
                    'quantity': 1,
                }],
                metadata={
                    'order_id': order.order_id
                },
                mode='payment',
                success_url=domain_url + '/?checkout=success',
                cancel_url=domain_url + '/?checkout=canceled',
            )

            return JsonResponse({
                'success': True,
                'checkout_url': checkout_session.url
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            # Invalid payload
            return JsonResponse({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return JsonResponse({'error': 'Invalid signature'}, status=400)

        # Handle the checkout.session.completed event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            order_id = session.get('metadata', {}).get('order_id')
            
            if order_id:
                try:
                    order = Order.objects.get(order_id=order_id)
                    if order.status == 'pending':
                        order.status = 'paid'
                        order.save()
                        
                        # Generate Draft and Notify Dev
                        process_order_notifications(order)
                except Order.DoesNotExist:
                    pass

        return JsonResponse({'status': 'success'})

from django.contrib.auth.mixins import LoginRequiredMixin
from .models import BotAdjustment

class ToggleBotStatusView(LoginRequiredMixin, View):
    def post(self, request, order_id, *args, **kwargs):
        try:
            data = json.loads(request.body)
            order = Order.objects.get(order_id=order_id, user=request.user)
            order.is_active = data.get('is_active', True)
            order.save()
            return JsonResponse({'success': True})
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class BotBuilderChatView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            category_id = data.get('category_id')
            history = data.get('history', [])
            
            if not category_id or not history:
                return JsonResponse({'error': 'Invalid data'}, status=400)
                
            category = BotCategory.objects.get(pk=category_id)
            from .ai_utils import get_sales_chat_response
            ai_reply = get_sales_chat_response(history, category.name, category.base_price)
            
            return JsonResponse({'success': True, 'reply': ai_reply})
        except BotCategory.DoesNotExist:
            return JsonResponse({'error': 'Category not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class BotAdjustmentView(LoginRequiredMixin, View):
    def post(self, request, order_id, *args, **kwargs):
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            if not message:
                return JsonResponse({'error': 'Message required'}, status=400)
                
            order = Order.objects.get(order_id=order_id, user=request.user)
            # Save user message
            BotAdjustment.objects.create(order=order, message=message, is_from_user=True)
            
            # Fetch history
            history = []
            for adj in order.adjustments.all().order_by('created_at'):
                role = "user" if adj.is_from_user else "model"
                history.append({"role": role, "parts": [adj.message]})
                
            from .ai_utils import get_upsell_chat_response
            ai_reply = get_upsell_chat_response(history, order)
            
            # Save AI reply
            BotAdjustment.objects.create(order=order, message=ai_reply, is_from_user=False)
            
            return JsonResponse({'success': True, 'reply': ai_reply})
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
        except Exception as e:
            import traceback; traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)
