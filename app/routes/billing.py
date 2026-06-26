import os
import stripe
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/api/billing", tags=["Billing"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class CheckoutRequest(BaseModel):
    user_id: int

@router.post("/create-checkout-session")
async def create_checkout_session(payload: CheckoutRequest):
    try:
        PRICE_ID = "price_1TjdmHAATbKivDRIYOKLzfu5"
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price': PRICE_ID,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            metadata={
                "user_id": str(payload.user_id)
            },
            success_url=f"{os.getenv('FRONTEND_URL')}/parametres?status=success",
            cancel_url=f"{os.getenv('FRONTEND_URL')}/abonnement?status=cancel",
        )
        
        return {"url": checkout_session.url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    stripe_signature = request.headers.get("stripe-signature")
    payload = await request.body()
    webhook_secret = "whsec_be033f55e40192ba0ad0d64c7d45537347f81a8d68d5c455451ce302df9c80a8"
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, webhook_secret
        )
    except ValueError as e:
        print(f"Payload invalide : {str(e)}")
        raise HTTPException(status_code=400, detail="Payload invalide")
    except stripe.error.SignatureVerificationError as e:
        print(f"Signature invalide : {str(e)}")
        raise HTTPException(status_code=400, detail="Signature invalide")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        session_dict = session.to_dict()
        metadata = session_dict.get('metadata', {})
        user_id = metadata.get('user_id') if metadata else None
        
        if user_id:
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user:
                user.is_premium = True
                db.commit()
                print(f"Succes ! L'utilisateur {user_id} est maintenant PREMIUM.")
                
    return {"status": "success"}