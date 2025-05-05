import os
import stripe
stripe.api_key = os.getenv('STRIPE_API_KEY')

def issue_refund(amount, claimant_email):
    payment_intent = stripe.PaymentIntent.create(
        amount=int(amount*100),
        currency='eur',
        receipt_email=claimant_email,
        payment_method_types=['card'],
    )
    refund = stripe.Refund.create(payment_intent=payment_intent.id)
    return refund.id
