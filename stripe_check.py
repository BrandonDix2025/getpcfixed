import os
import stripe

# Load secret key from Windows environment variable
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")

# Tier names must match your Stripe product names exactly
PRO_PRODUCT_NAME   = "GetPCFixed Pro"
GAMER_PRODUCT_NAME = "GetPCFixed Gamer"


def get_subscription_tier(email: str) -> str:
    """
    Checks Stripe for an active subscription tied to this email.
    Returns: "gamer", "pro", or "free"
    """
    if not stripe.api_key:
        return "free"

    if not email or "@" not in email:
        return "free"

    try:
        # Find customer by email
        customers = stripe.Customer.list(email=email, limit=1)
        if not customers.data:
            return "free"

        customer = customers.data[0]

        # Check for active subscriptions
        subscriptions = stripe.Subscription.list(
            customer=customer.id,
            status="active",
            limit=5,
            expand=["data.items.data.price.product"]
        )

        if not subscriptions.data:
            return "free"

        # Check what product they are subscribed to
        for sub in subscriptions.data:
            for item in sub["items"]["data"]:
                product = item["price"]["product"]
                product_name = product.get("name", "")

                if product_name == GAMER_PRODUCT_NAME:
                    return "gamer"
                if product_name == PRO_PRODUCT_NAME:
                    return "pro"

        return "free"

    except stripe.error.AuthenticationError:
        return "free"
    except stripe.error.StripeError:
        return "free"
    except Exception:
        return "free"


def is_paid(email: str) -> bool:
    """Returns True if user has any active paid subscription."""
    return get_subscription_tier(email) in ("pro", "gamer")
