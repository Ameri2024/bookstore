import logging
from django.urls import reverse
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from azbankgateways import bankfactories, models as bank_models
from azbankgateways.exceptions import AZBankGatewaysException
from apps.cart.models import Order
from .models import Transaction

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user, is_paid=False)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found or already paid.'}, status=404)

    amount = int(order.final_amount)
    if amount < 11000:
        return Response({'error': 'Payment amount must be at least 11,000 IRR.'}, status=400)

    transaction = Transaction.objects.create(
        user=request.user,
        order=order,
        amount=amount,
        status='INIT'
    )

    factory = bankfactories.BankFactory()
    try:
        bank = factory.create(bank_models.BankType.ZARINPAL)
        bank.set_request(request)
        bank.set_callback_url(request.build_absolute_uri(reverse('payment_callback')))

        response = bank.go(amount, user_mobile_number=request.user.phone_number)
        if response.is_successful():
            transaction.authority = response.authority
            transaction.save()
            return Response({'payment_url': response.pay_url}, status=200)
        else:
            transaction.status = 'FAIL'
            transaction.save()
            return Response({'error': response.error_message or 'Gateway communication error.'}, status=400)
    except AZBankGatewaysException as e:
        logger.error(f"Payment initiation failed: {str(e)}")
        transaction.status = 'FAIL'
        transaction.save()
        return Response({'error': 'Unable to connect to payment gateway. Please try again later.'}, status=500)


@csrf_exempt
def payment_callback(request):
    authority = request.GET.get('Authority')
    if not authority:
        raise Http404("Invalid transaction: missing authority code.")

    try:
        transaction = Transaction.objects.get(authority=authority)
    except Transaction.DoesNotExist:
        raise Http404("Transaction not found.")

    if transaction.status != 'INIT':
        return HttpResponse("This transaction has already been processed.")

    factory = bankfactories.BankFactory()
    bank = factory.create(bank_models.BankType.ZARINPAL)
    bank.set_request(request)

    try:
        verification_response = bank.verify(transaction.amount)
        if verification_response.is_successful():
            transaction.status = 'SUCCESS'
            transaction.ref_id = verification_response.reference_number
            transaction.save()

            order = transaction.order
            order.is_paid = True
            order.status = 'paid'
            order.paid_at = timezone.now()
            order.save()

            logger.info(f"Payment successful for order #{order.id}, transaction #{transaction.id}")
            return HttpResponse("Payment completed successfully.")
        else:
            transaction.status = 'FAIL'
            transaction.save()
            logger.warning(f"Payment verification failed for transaction #{transaction.id}")
            return HttpResponse("Payment failed. Please try again.")
    except AZBankGatewaysException as e:
        logger.error(f"Payment verification error: {str(e)}")
        transaction.status = 'FAIL'
        transaction.save()
        return HttpResponse("Payment gateway error. Please contact support.")