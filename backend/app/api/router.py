from fastapi import APIRouter

from app.api.v1 import admin, auth, circle, event, health, im, network, payment, points, post, user, verification

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(user.router)
api_router.include_router(verification.router)
api_router.include_router(circle.router)
api_router.include_router(network.router)
api_router.include_router(post.router)
api_router.include_router(points.router)
api_router.include_router(event.router)
api_router.include_router(im.router)
api_router.include_router(payment.router)
api_router.include_router(admin.router)
