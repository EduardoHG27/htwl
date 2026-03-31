# catalogo/signals.py
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added, pre_social_login
from django.contrib.auth.signals import user_logged_in
from django.shortcuts import get_object_or_404
from .models import Carrito, ItemCarrito
import logging

logger = logging.getLogger(__name__)

@receiver(pre_social_login)
def transferir_carrito_antes_google_login(sender, request, sociallogin, **kwargs):
    """
    Transferir carrito de sesión a usuario ANTES de que se complete el login social
    Esto asegura que el carrito se transfiera correctamente
    """
    if not request.user.is_authenticated:
        # Usuario no autenticado - transferir carrito de sesión
        sesion_id = request.session.session_key
        
        if sesion_id:
            try:
                # Buscar carrito de sesión
                carrito_sesion = Carrito.objects.get(sesion_id=sesion_id, activo=True)
                logger.info(f"Carrito de sesión encontrado: {carrito_sesion.id}")
                
                # Guardar el carrito en el request para usarlo después
                request.carrito_sesion = carrito_sesion
            except Carrito.DoesNotExist:
                pass

@receiver(social_account_added)
def transferir_carrito_despues_google_login(sender, request, sociallogin, **kwargs):
    """
    Transferir carrito de sesión a usuario DESPUÉS de que se crea la cuenta social
    """
    user = sociallogin.user
    
    # Transferir carrito de sesión si existe
    if hasattr(request, 'carrito_sesion'):
        carrito_sesion = request.carrito_sesion
        
        # Obtener o crear carrito del usuario
        carrito_usuario, created = Carrito.objects.get_or_create(
            usuario=user,
            activo=True,
            defaults={'sesion_id': None}
        )
        
        # Transferir items
        items_transferidos = 0
        for item in carrito_sesion.items.all():
            item_existente = carrito_usuario.items.filter(producto=item.producto).first()
            if item_existente:
                item_existente.cantidad += item.cantidad
                item_existente.save()
                item.delete()
            else:
                item.carrito = carrito_usuario
                item.save()
            items_transferidos += 1
        
        # Desactivar carrito de sesión
        if carrito_sesion.items.count() == 0:
            carrito_sesion.delete()
        else:
            carrito_sesion.activo = False
            carrito_sesion.save()
        
        if items_transferidos > 0:
            logger.info(f"Transferidos {items_transferidos} items del carrito de sesión al usuario {user.username}")
            
            # Opcional: Agregar mensaje de éxito
            from django.contrib import messages
            messages.info(request, f'Se transfirieron {items_transferidos} items de tu carrito anterior')