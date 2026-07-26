"""
=============================================================================
NEXSTREAM — Rutas de Suscripciones (Stripe)
=============================================================================
Archivo: app/subscription/routes.py
Descripción: Lógica de planes de pago, checkout de Stripe y webhooks.
=============================================================================
"""

import os
import stripe
from flask import (
    render_template, redirect, url_for, flash,
    request, current_app, jsonify, abort
)
from flask_login import login_required, current_user
from extensions import db
from app.subscription import bp
from app.models.subscription import Plan, Subscription
from app.models.interaction import ActivityLog


# ─── PLANES DE PAGO ────────────────────────────────────────────────────────

@bp.route('/planes')
def plans():
    """Muestra la tabla de precios y planes disponibles."""
    # Obtenemos los planes activos ordenados por precio
    available_plans = Plan.query.filter_by(is_active=True).order_by(Plan.price_monthly).all()
    
    # Ver si el usuario actual tiene una suscripción activa
    current_plan = None
    if current_user.is_authenticated and current_user.subscription and current_user.subscription.is_active:
        current_plan = current_user.subscription.plan
        
    return render_template(
        'subscription/plans.html',
        plans=available_plans,
        current_plan=current_plan,
        title='Planes de Suscripción — NEXSTREAM'
    )


# ─── CHECKOUT ──────────────────────────────────────────────────────────────

@bp.route('/checkout/<int:plan_id>', methods=['POST'])
@login_required
def checkout(plan_id):
    """Crea una sesión de Checkout de Stripe para el plan seleccionado."""
    plan = Plan.query.get_or_404(plan_id)
    
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    
    if not stripe.api_key:
        flash('El sistema de pagos no está configurado (Falta STRIPE_SECRET_KEY).', 'error')
        return redirect(url_for('subscription.plans'))
        
    try:
        # Configurar URLs de retorno
        # request.host_url ya termina en '/'
        success_url = request.host_url + 'suscripcion/exito?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = request.host_url + 'suscripcion/planes'
        
        # Buscar si el usuario ya es cliente en Stripe (opcional, para mantener el mismo customer_id)
        customer_id = None
        if current_user.subscription and current_user.subscription.stripe_customer_id:
            customer_id = current_user.subscription.stripe_customer_id
            
        checkout_kwargs = {
            'payment_method_types': ['card'],
            'line_items': [{
                'price': plan.stripe_price_id,
                'quantity': 1,
            }],
            'mode': 'subscription',
            'success_url': success_url,
            'cancel_url': cancel_url,
            'client_reference_id': str(current_user.id),
        }
        
        if customer_id:
            checkout_kwargs['customer'] = customer_id
        else:
            checkout_kwargs['customer_email'] = current_user.email
            
        # Crear la sesión de checkout
        checkout_session = stripe.checkout.Session.create(**checkout_kwargs)
        
        return redirect(checkout_session.url, code=303)
        
    except Exception as e:
        current_app.logger.error(f'Error de Stripe Checkout: {str(e)}')
        flash('Ocurrió un error al procesar tu solicitud de pago.', 'error')
        return redirect(url_for('subscription.plans'))


@bp.route('/exito')
@login_required
def success():
    """Página de éxito tras completar el pago."""
    session_id = request.args.get('session_id')
    if not session_id:
        return redirect(url_for('main.index'))
        
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    
    try:
        # Verificar la sesión con Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid' or session.status == 'complete':
            ActivityLog.log('subscription_success', 'Suscripción completada', user_id=current_user.id)
            return render_template('subscription/success.html', title='Suscripción Activada')
    except Exception as e:
        current_app.logger.error(f'Error al verificar sesión de Stripe: {str(e)}')
        
    flash('No se pudo verificar el pago. Si crees que esto es un error, contacta a soporte.', 'error')
    return redirect(url_for('subscription.plans'))


@bp.route('/portal')
@login_required
def customer_portal():
    """Redirige al Customer Portal de Stripe para gestionar métodos de pago o cancelar."""
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    
    if not current_user.subscription or not current_user.subscription.stripe_customer_id:
        flash('No tienes una suscripción activa para gestionar.', 'warning')
        return redirect(url_for('subscription.plans'))
        
    try:
        return_url = request.host_url + 'perfil/configuracion'
        
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.subscription.stripe_customer_id,
            return_url=return_url,
        )
        return redirect(portal_session.url, code=303)
        
    except Exception as e:
        current_app.logger.error(f'Error al crear portal de Stripe: {str(e)}')
        flash('Ocurrió un error al cargar el portal de gestión.', 'error')
        return redirect(url_for('user.settings'))


# ─── WEBHOOK DE STRIPE ─────────────────────────────────────────────────────

@bp.route('/webhook', methods=['POST'])
def webhook():
    """
    Endpoint para recibir eventos asíncronos de Stripe (webhook).
    Crucial para actualizar el estado de suscripción cuando ocurren cobros recurrentes.
    """
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = current_app.config['STRIPE_WEBHOOK_SECRET']
    
    if not webhook_secret:
        return 'Webhook secret not configured', 500

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    # Manejar eventos de Stripe
    if event.type == 'checkout.session.completed':
        session = event.data.object
        _handle_checkout_completed(session)
        
    elif event.type == 'customer.subscription.updated':
        subscription = event.data.object
        _handle_subscription_updated(subscription)
        
    elif event.type == 'customer.subscription.deleted':
        subscription = event.data.object
        _handle_subscription_deleted(subscription)

    return jsonify({'status': 'success'})


def _handle_checkout_completed(session):
    """Procesar checkout exitoso (crear suscripción inicial)."""
    user_id = session.get('client_reference_id')
    if not user_id:
        return
        
    # Obtener detalles de la suscripción desde Stripe
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    stripe_sub = stripe.Subscription.retrieve(session.subscription)
    
    # Buscar el plan correspondiente en nuestra BD por el price_id
    price_id = stripe_sub.items.data[0].price.id
    plan = Plan.query.filter_by(stripe_price_id=price_id).first()
    
    if not plan:
        current_app.logger.error(f'Plan no encontrado para price_id: {price_id}')
        return
        
    from app.models.user import User
    user = User.query.get(user_id)
    if not user:
        return
        
    # Actualizar o crear registro de suscripción
    sub = user.subscription
    if not sub:
        sub = Subscription(user_id=user.id)
        db.session.add(sub)
        
    sub.plan_id = plan.id
    sub.stripe_customer_id = session.customer
    sub.stripe_subscription_id = session.subscription
    sub.status = stripe_sub.status
    
    import datetime
    sub.current_period_start = datetime.datetime.fromtimestamp(stripe_sub.current_period_start, tz=datetime.timezone.utc)
    sub.current_period_end = datetime.datetime.fromtimestamp(stripe_sub.current_period_end, tz=datetime.timezone.utc)
    
    db.session.commit()
    ActivityLog.log('webhook_sub_created', 'Suscripción creada por Stripe Webhook', user_id=user.id)


def _handle_subscription_updated(stripe_sub):
    """Procesar actualización de suscripción (renovación, cambio de plan)."""
    sub = Subscription.query.filter_by(stripe_subscription_id=stripe_sub.id).first()
    if not sub:
        return
        
    sub.status = stripe_sub.status
    sub.cancel_at_period_end = stripe_sub.cancel_at_period_end
    
    import datetime
    sub.current_period_start = datetime.datetime.fromtimestamp(stripe_sub.current_period_start, tz=datetime.timezone.utc)
    sub.current_period_end = datetime.datetime.fromtimestamp(stripe_sub.current_period_end, tz=datetime.timezone.utc)
    
    # Revisar si cambió de plan
    price_id = stripe_sub.items.data[0].price.id
    plan = Plan.query.filter_by(stripe_price_id=price_id).first()
    if plan and sub.plan_id != plan.id:
        sub.plan_id = plan.id
        
    db.session.commit()


def _handle_subscription_deleted(stripe_sub):
    """Procesar cancelación definitiva (expiración o impago)."""
    sub = Subscription.query.filter_by(stripe_subscription_id=stripe_sub.id).first()
    if not sub:
        return
        
    sub.status = 'canceled'
    db.session.commit()
