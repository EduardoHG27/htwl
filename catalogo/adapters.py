# catalogo/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adaptador personalizado para manejar el login con Google
    y forzar la verificación del correo
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Se ejecuta ANTES de que se complete el login social
        """
        # Obtener el email del usuario de Google
        email = sociallogin.account.extra_data.get('email')
        
        if not email:
            # Si no hay email, no continuar
            messages.error(request, 'No se pudo obtener tu correo electrónico de Google')
            return redirect('catalogo:login')
        
        # Verificar si ya existe un usuario con este email
        try:
            email_address = EmailAddress.objects.get(email=email)
            
            # Si el email existe pero NO está verificado
            if not email_address.verified:
                # No permitir login, redirigir a verificación
                messages.warning(
                    request, 
                    f'El correo {email} está registrado pero no verificado. '
                    'Por favor verifica tu correo antes de continuar.'
                )
                # Redirigir a página de reenviar verificación
                return redirect('catalogo:reenviar_verificacion')
            
            # Si el email existe y está verificado, continuar normalmente
            
        except EmailAddress.DoesNotExist:
            # El email no existe, se creará en el paso siguiente
            pass
        
        return super().pre_social_login(request, sociallogin)
    
    def save_user(self, request, sociallogin, form=None):
        """
        Guarda el usuario después del login social
        """
        user = super().save_user(request, sociallogin, form)
        
        # Obtener el email de los datos de Google
        email = sociallogin.account.extra_data.get('email')
        
        if email:
            # Obtener o crear el EmailAddress
            email_address, created = EmailAddress.objects.get_or_create(
                user=user,
                email=email,
                defaults={
                    'verified': False,  # Inicialmente no verificado
                    'primary': True
                }
            )
            
            # Si se creó ahora, marcar como no verificado inicialmente
            if created:
                # Enviar correo de verificación
                email_address.send_confirmation(request)
                messages.info(
                    request, 
                    'Hemos enviado un correo de verificación a tu email. '
                    'Por favor verifica tu cuenta antes de continuar.'
                )
            else:
                # Si ya existía pero no estaba verificado
                if not email_address.verified:
                    email_address.send_confirmation(request)
                    messages.info(
                        request, 
                        'Tu correo no está verificado. Hemos enviado un nuevo enlace de verificación.'
                    )
        
        return user