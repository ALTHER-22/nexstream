"""
=============================================================================
NEXSTREAM — Modelos de Base de Datos: Suscripciones y Planes
=============================================================================
Archivo: app/models/subscription.py
Descripción: Modelos SQLAlchemy para gestionar planes de pago y suscripciones (Stripe).
=============================================================================
"""

from datetime import datetime, timezone
from extensions import db

class Plan(db.Model):
    """
    ─── Modelo de Plan ───────────────────────────────────────────────────────
    Define los niveles de suscripción disponibles.
    Ej: Básico (720p), Estándar (1080p), Premium (4K).
    """
    __tablename__ = 'plans'

    id = db.Column(db.Integer, primary_key=True)
    stripe_product_id = db.Column(db.String(100), unique=True)
    stripe_price_id = db.Column(db.String(100), unique=True)
    
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    price_monthly = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    
    # Características del plan
    max_resolution = db.Column(db.String(20), default='1080p')
    max_devices = db.Column(db.Integer, default=1)
    has_downloads = db.Column(db.Boolean, default=False)
    
    is_active = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)

    # Relaciones
    subscriptions = db.relationship('Subscription', back_populates='plan', lazy='dynamic')

    def __repr__(self):
        return f'<Plan {self.name}>'


class Subscription(db.Model):
    """
    ─── Modelo de Suscripción ────────────────────────────────────────────────
    Registra la suscripción activa de un usuario.
    """
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    
    stripe_customer_id = db.Column(db.String(100), unique=True)
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    
    status = db.Column(db.String(50), nullable=False, default='active') # active, past_due, canceled, incomplete
    
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones
    user = db.relationship('User', backref=db.backref('subscription', uselist=False))
    plan = db.relationship('Plan', back_populates='subscriptions')

    def __repr__(self):
        return f'<Subscription User:{self.user_id} Plan:{self.plan_id}>'
    
    @property
    def is_active(self):
        """Verifica si la suscripción permite acceso."""
        return self.status in ['active', 'trialing']
