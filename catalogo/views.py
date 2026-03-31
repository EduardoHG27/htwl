# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from .models import Producto, Categoria, Marca, Carrito, ItemCarrito, Pedido, ItemPedido, Reseña,CarruselImagen
from django.contrib.auth.models import User
from django.core.paginator import Paginator
import csv
import openpyxl
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from django.conf import settings
from datetime import datetime, timedelta
import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from allauth.account.models import EmailAddress



# Productos
def lista_productos(request):
    productos_list = Producto.objects.filter(disponible=True)
    
    # Búsqueda
    query = request.GET.get('q')
    if query:
        productos_list = productos_list.filter(
            Q(nombre__icontains=query) | 
            Q(descripcion__icontains=query) |
            Q(marca__nombre__icontains=query)
        )
    
    # Filtros
    categoria_slug = request.GET.get('categoria')
    marca_slug = request.GET.get('marca')
    precio_min = request.GET.get('precio_min')
    precio_max = request.GET.get('precio_max')
    
    if categoria_slug:
        productos_list = productos_list.filter(categoria__slug=categoria_slug)
    if marca_slug:
        productos_list = productos_list.filter(marca__slug=marca_slug)
    if precio_min:
        productos_list = productos_list.filter(precio__gte=precio_min)
    if precio_max:
        productos_list = productos_list.filter(precio__lte=precio_max)
    
    # Ordenamiento
    orden = request.GET.get('orden', '-fecha_creacion')
    productos_list = productos_list.order_by(orden)
    
    # Paginación
    paginator = Paginator(productos_list, 12)
    page = request.GET.get('page')
    productos = paginator.get_page(page)
    
    context = {
        'productos': productos,
        'categorias': Categoria.objects.all(),
        'marcas': Marca.objects.all(),
        'query': query,
        'categoria_activa': categoria_slug,
        'marca_activa': marca_slug,
    }
    return render(request, 'lista_productos.html', context)

def detalle_producto(request, slug):
    producto = get_object_or_404(Producto, slug=slug, disponible=True)
    productos_relacionados = Producto.objects.filter(
        categoria=producto.categoria, 
        disponible=True
    ).exclude(id=producto.id)[:20]  # Aumentado a 20 para mejor visualización del carrusel
    
    # Calcular descuento y porcentaje para el producto principal
    descuento = None
    porcentaje_descuento = None
    if producto.precio_oferta:
        descuento = producto.precio - producto.precio_oferta
        porcentaje_descuento = (descuento / producto.precio) * 100
    
    # Calcular descuento y porcentaje para cada producto relacionado
    for p in productos_relacionados:
        p.porcentaje_descuento = None
        if p.precio_oferta:
            descuento_rel = p.precio - p.precio_oferta
            p.porcentaje_descuento = (descuento_rel / p.precio) * 100
    
    # Reseñas
    reseñas = producto.reseñas.all()
    promedio_calificacion = reseñas.aggregate(Avg('calificacion'))['calificacion__avg']
    
    # Verificar si el usuario ya ha reseñado
    usuario_reseño = False
    if request.user.is_authenticated:
        usuario_reseño = reseñas.filter(usuario=request.user).exists()
    
    context = {
        'producto': producto,
        'relacionados': productos_relacionados,
        'reseñas': reseñas,
        'promedio_calificacion': promedio_calificacion,
        'usuario_reseño': usuario_reseño,
        'descuento': descuento,
        'porcentaje_descuento': porcentaje_descuento,
    }
    return render(request, 'detalle_producto.html', context)

# Autenticación
def registro_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if password != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'catalogo/registro.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe')
            return render(request, 'registro.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado')
            return render(request, 'registro.html')
        
        # Crear usuario
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        
        # Hacer login automáticamente después del registro
        login(request, user)
        
        # Transferir carrito usando la función auxiliar
        items_transferidos = transferir_carrito_sesion_a_usuario(request, user)
        
        if items_transferidos:
            messages.info(request, f'Se transfirieron {items_transferidos} items de tu carrito anterior')
        
        messages.success(request, 'Registro exitoso. ¡Bienvenido!')
        return redirect('catalogo:index')
    
    return render(request, 'registro.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Verificar si el email está confirmado
            try:
                email_address = EmailAddress.objects.get(user=user, email=user.email)
                
                if not email_address.verified:
                    messages.warning(
                        request, 
                        'Tu correo electrónico no está verificado. '
                        'Por favor revisa tu bandeja de entrada y verifica tu cuenta.'
                    )
                    return redirect('catalogo:reenviar_verificacion')
            except EmailAddress.DoesNotExist:
                # Si no existe EmailAddress, crearlo y enviar verificación
                email_address = EmailAddress.objects.create(
                    user=user,
                    email=user.email,
                    verified=False,
                    primary=True
                )
                
                # Enviar correo de verificación usando el método correcto
                try:
                    # Método 1: Usar el adaptador
                    from allauth.account.utils import perform_login
                    from allauth.account.adapter import get_adapter
                    
                    # Enviar confirmación por email
                    email_address.send_confirmation(request)
                    messages.warning(
                        request, 
                        'Debes verificar tu correo electrónico. '
                        'Hemos enviado un enlace de verificación a tu email.'
                    )
                except Exception as e:
                    messages.error(request, f'Error al enviar verificación: {str(e)}')
                
                return redirect('catalogo:reenviar_verificacion')
            
            # Si está verificado, continuar con login normal
            login(request, user)
            
            # Transferir carrito (tu código existente)
            sesion_id = request.session.session_key
            carrito_sesion = None
            
            if sesion_id:
                try:
                    carrito_sesion = Carrito.objects.get(sesion_id=sesion_id, activo=True)
                except Carrito.DoesNotExist:
                    pass
            
            if carrito_sesion:
                carrito_usuario, created = Carrito.objects.get_or_create(
                    usuario=user, 
                    activo=True,
                    defaults={'sesion_id': None}
                )
                
                for item in carrito_sesion.items.all():
                    item_existente = carrito_usuario.items.filter(producto=item.producto).first()
                    if item_existente:
                        item_existente.cantidad += item.cantidad
                        item_existente.save()
                        item.delete()
                    else:
                        item.carrito = carrito_usuario
                        item.save()
                
                if carrito_sesion.items.count() == 0:
                    carrito_sesion.delete()
                else:
                    carrito_sesion.activo = False
                    carrito_sesion.save()
            
            messages.success(request, f'¡Bienvenido {username}!')
            return redirect('catalogo:index')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Sesión cerrada exitosamente')
    return redirect('catalogo:index')

# Carrito

def obtener_o_crear_carrito(request):
    """
    Obtiene o crea un carrito para el usuario actual (autenticado o anónimo)
    """
    if request.user.is_authenticated:
        # Usuario autenticado - buscar carrito activo
        carrito, created = Carrito.objects.get_or_create(
            usuario=request.user,
            activo=True,
            defaults={'sesion_id': None}
        )
        return carrito
    else:
        # Usuario anónimo - usar sesión
        if not request.session.session_key:
            request.session.create()
        
        sesion_id = request.session.session_key
        
        # Buscar carrito activo para esta sesión
        carrito = Carrito.objects.filter(
            sesion_id=sesion_id,
            activo=True
        ).first()
        
        if not carrito:
            # Crear nuevo carrito si no existe
            carrito = Carrito.objects.create(
                sesion_id=sesion_id,
                activo=True,
                usuario=None
            )
        
        return carrito

def carrito_view(request):
    carrito = obtener_o_crear_carrito(request)
    items = carrito.items.select_related('producto').all()
    
    # Calcular valores para mostrar en el template
    subtotal = carrito.total  # El total del carrito es el subtotal
    iva = subtotal * Decimal('0.16')
    total_con_iva = subtotal + iva
    
    context = {
        'carrito': carrito,
        'items': items,
        'subtotal': subtotal,
        'iva': iva,
        'total_con_iva': total_con_iva,  # Nuevo: total con IVA incluido
    }
    return render(request, 'carrito.html', context)

def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id, disponible=True)
    
    if producto.existencias < 1:
        messages.error(request, 'Producto sin stock disponible')
        return redirect('catalogo:detalle_producto', slug=producto.slug)
    
    carrito = obtener_o_crear_carrito(request)
    
    cantidad = int(request.POST.get('cantidad', 1))
    if cantidad > producto.existencias:
        messages.error(request, f'Solo hay {producto.existencias} unidades disponibles')
        return redirect('catalogo:detalle_producto', slug=producto.slug)
    
    item, created = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        producto=producto,
        defaults={'cantidad': cantidad}
    )
    
    if not created:
        if item.cantidad + cantidad <= producto.existencias:
            item.cantidad += cantidad
            item.save()
            messages.success(request, 'Carrito actualizado')
        else:
            messages.error(request, 'No hay suficiente stock')
            return redirect('catalogo:detalle_producto', slug=producto.slug)
    else:
        messages.success(request, 'Producto agregado al carrito')
    
    return redirect('catalogo:carrito')

def actualizar_carrito(request, item_id):
    item = get_object_or_404(ItemCarrito, id=item_id)
    cantidad = int(request.POST.get('cantidad', 1))
    
    if cantidad <= 0:
        item.delete()
        messages.success(request, 'Producto eliminado del carrito')
    elif cantidad <= item.producto.existencias:
        item.cantidad = cantidad
        item.save()
        messages.success(request, 'Carrito actualizado')
    else:
        messages.error(request, f'Solo hay {item.producto.existencias} unidades disponibles')
    
    return redirect('catalogo:carrito')

def eliminar_del_carrito(request, item_id):
    item = get_object_or_404(ItemCarrito, id=item_id)
    item.delete()
    messages.success(request, 'Producto eliminado del carrito')
    return redirect('catalogo:carrito')

# Checkout y pedidos
@login_required
def checkout_view(request):
    
    carrito = obtener_o_crear_carrito(request)
    
    if carrito.cantidad_items == 0:
        messages.warning(request, 'Tu carrito está vacío')
        return redirect('catalogo:carrito')
    
    # Calcular montos
    subtotal = carrito.total
    costo_envio = Decimal('110.00')
    iva = subtotal * Decimal('0.16')
    total_con_envio = subtotal + costo_envio + iva
    total_sin_envio = subtotal + iva
    
    # Obtener datos del usuario para prellenar el formulario
    user_data = {
        'full_name': request.user.get_full_name() or request.user.username,
        'email': request.user.email,
        # Si tienes un perfil de usuario con más datos, puedes agregarlos aquí
    }
    
    if request.method == 'POST':
        tipo_entrega = request.POST.get('tipo_entrega')
        metodo_pago = request.POST.get('metodo_pago')
        
        # VALIDACIÓN IMPORTANTE: Si metodo_pago viene vacío, asignar valor por defecto
        if not metodo_pago:
            metodo_pago = 'transferencia'  # Valor por defecto
            print("⚠️ metodo_pago no recibido, asignando 'transferencia' por defecto")
        
        nombre_completo = request.POST.get('nombre_completo')
        direccion = request.POST.get('direccion') if tipo_entrega == 'envio' else 'Recolección en tienda'
        ciudad = request.POST.get('ciudad') if tipo_entrega == 'envio' else 'N/A'
        codigo_postal = request.POST.get('codigo_postal') if tipo_entrega == 'envio' else '00000'
        telefono = request.POST.get('telefono')
        
        # Validar campos requeridos
        if not nombre_completo or not telefono:
            messages.error(request, 'Por favor completa todos los campos requeridos')
            return render(request, 'checkout.html', {
                'carrito': carrito,
                'items': carrito.items.all(),
                'subtotal': subtotal,
                'costo_envio': costo_envio,
                'iva': iva,
                'total_con_envio': total_con_envio,
                'total_sin_envio': total_sin_envio,
                'datos_bancarios': settings.DATOS_BANCARIOS,
                'user_data': user_data,
                'form_data': request.POST  # Para mantener los datos ingresados
            })
        
        # Determinar total según tipo de entrega
        total = total_con_envio if tipo_entrega == 'envio' else total_sin_envio
        costo_envio_aplicado = costo_envio if tipo_entrega == 'envio' else Decimal('0.00')
        
        # Generar referencia única para transferencia
        fecha_actual = datetime.now()
        referencia = f"PED{request.user.id}{fecha_actual.strftime('%d%m%Y%H%M%S')}"
        
        # Crear pedido
        pedido = Pedido.objects.create(
            usuario=request.user,
            subtotal=subtotal,
            costo_envio=costo_envio_aplicado,
            iva=iva,
            total=total,
            nombre_completo=nombre_completo,
            direccion=direccion,
            ciudad=ciudad,
            codigo_postal=codigo_postal,
            telefono=telefono,
            metodo_pago=metodo_pago,
            tipo_entrega=tipo_entrega,
            referencia_pago=referencia,
            estado_pago='pendiente' if metodo_pago == 'transferencia' else 'pagado',
        )
        
        # Crear items del pedido
        for item in carrito.items.all():
            ItemPedido.objects.create(
                pedido=pedido,
                producto=item.producto,
                cantidad=item.cantidad,
                precio_unitario=item.producto.precio_actual()
            )
            
            # Actualizar stock
            producto = item.producto
            producto.existencias -= item.cantidad
            producto.vendidos += item.cantidad
            producto.save()
        
        # Marcar carrito como inactivo
        carrito.activo = False
        carrito.save()
        
        # Si es transferencia, redirigir a instrucciones
        if metodo_pago == 'transferencia':
            return redirect('catalogo:instrucciones_transferencia', pedido_id=pedido.id)
        else:
            messages.success(request, '¡Pedido realizado con éxito!')
            return redirect('catalogo:pedido_confirmado', pedido_id=pedido.id)
    
    context = {
        'carrito': carrito,
        'items': carrito.items.all(),
        'subtotal': subtotal,
        'costo_envio': costo_envio,
        'iva': iva,
        'total_con_envio': total_con_envio,
        'total_sin_envio': total_sin_envio,
        'datos_bancarios': settings.DATOS_BANCARIOS,
        'user_data': user_data,  # Datos del usuario para el template
    }
    return render(request, 'checkout.html', context)

@login_required
def instrucciones_transferencia(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    
    # Calcular tiempo límite (24 horas)
    tiempo_limite = pedido.fecha_creacion + timedelta(hours=24)
    
    context = {
        'pedido': pedido,
        'datos_bancarios': settings.DATOS_BANCARIOS,
        'tiempo_limite': tiempo_limite,
        'referencia_formateada': f"PEDIDO-{pedido.id}",
    }
    return render(request, 'instrucciones_transferencia.html', context)

@login_required
def subir_comprobante(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
        
        if 'comprobante' in request.FILES:
            pedido.comprobante_pago = request.FILES['comprobante']
            pedido.estado_pago = 'verificando'
            pedido.save()
            
            # Enviar notificación al admin
            messages.success(request, 'Comprobante recibido. Estaremos verificando tu pago.')
            
        return redirect('catalogo:detalle_pedido', pedido_id=pedido.id)

def pedido_confirmado(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    
    # Calcular valores para mostrar
    iva = pedido.total * Decimal('0.16')
    total_con_iva = pedido.total + iva
    
    context = {
        'pedido': pedido,
        'iva': iva,
        'total_con_iva': total_con_iva,
    }
    return render(request, 'pedido_confirmado.html', context)

@login_required
def mis_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    return render(request, 'mis_pedidos.html', {'pedidos': pedidos})

@login_required
def agregar_reseña(request, producto_id):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)
        calificacion = int(request.POST.get('calificacion'))
        comentario = request.POST.get('comentario')
        
        # Verificar si ya existe una reseña
        reseña, created = Reseña.objects.get_or_create(
            producto=producto,
            usuario=request.user,
            defaults={
                'calificacion': calificacion,
                'comentario': comentario
            }
        )
        
        if not created:
            reseña.calificacion = calificacion
            reseña.comentario = comentario
            reseña.save()
            messages.success(request, 'Reseña actualizada')
        else:
            messages.success(request, 'Reseña agregada')
        
        return redirect('catalogo:detalle_producto', slug=producto.slug)
    
    return redirect('catalogo:index')

# Exportar catálogo
def exportar_catalogo_excel(request):
    productos = Producto.objects.filter(disponible=True)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Catálogo"
    
    # Encabezados
    headers = ['Nombre', 'Marca', 'Categoría', 'Precio', 'Precio Oferta', 'Stock', 'Descripción']
    ws.append(headers)
    
    # Datos
    for producto in productos:
        ws.append([
            producto.nombre,
            producto.marca.nombre if producto.marca else '',
            producto.categoria.nombre,
            float(producto.precio),
            float(producto.precio_oferta) if producto.precio_oferta else '',
            producto.existencias,
            producto.descripcion[:100] + '...' if len(producto.descripcion) > 100 else producto.descripcion
        ])
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="catalogo.xlsx"'
    wb.save(response)
    return response

def exportar_catalogo_csv(request):
    productos = Producto.objects.filter(disponible=True)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="catalogo.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Nombre', 'Marca', 'Categoría', 'Precio', 'Precio Oferta', 'Stock', 'Descripción'])
    
    for producto in productos:
        writer.writerow([
            producto.nombre,
            producto.marca.nombre if producto.marca else '',
            producto.categoria.nombre,
            producto.precio,
            producto.precio_oferta if producto.precio_oferta else '',
            producto.existencias,
            producto.descripcion[:100] + '...' if len(producto.descripcion) > 100 else producto.descripcion
        ])
    
    return response

def transferir_carrito_sesion_a_usuario(request, user):
    """
    Función auxiliar para transferir el carrito de la sesión al usuario
    """
    sesion_id = request.session.session_key
    if not sesion_id:
        return None
    
    try:
        carrito_sesion = Carrito.objects.get(sesion_id=sesion_id, activo=True)
    except Carrito.DoesNotExist:
        return None
    
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
    
    # Desactivar/eliminar carrito de sesión
    if carrito_sesion.items.count() == 0:
        carrito_sesion.delete()
    else:
        carrito_sesion.activo = False
        carrito_sesion.save()
    
    return items_transferidos

def exportar_catalogo_pdf(request):
    productos = Producto.objects.filter(disponible=True)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="catalogo.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Título
    elements.append(Paragraph("Catálogo de Productos", styles['Title']))
    
    # Tabla de productos
    data = [['Nombre', 'Marca', 'Categoría', 'Precio', 'Stock']]
    
    for producto in productos[:50]:  # Limitamos a 50 productos para el PDF
        data.append([
            producto.nombre[:30] + '...' if len(producto.nombre) > 30 else producto.nombre,
            producto.marca.nombre if producto.marca else '',
            producto.categoria.nombre,
            f"${producto.precio_actual()}",
            str(producto.existencias)
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    return response


@login_required
def reenviar_verificacion(request):
    """
    Vista para reenviar el correo de verificación
    """
    if request.method == 'POST':
        try:
            # Obtener o crear el EmailAddress para el usuario
            email_address, created = EmailAddress.objects.get_or_create(
                user=request.user,
                email=request.user.email,
                defaults={'verified': False, 'primary': True}
            )
            
            if email_address.verified:
                messages.info(request, 'Tu correo ya está verificado. Puedes iniciar sesión normalmente.')
                # Si ya está verificado, hacer login automático
                login(request, request.user)
                return redirect('catalogo:index')
            
            # Enviar el correo de confirmación usando el método correcto
            email_address.send_confirmation(request)
            
            messages.success(
                request, 
                '¡Correo de verificación enviado! Por favor revisa tu bandeja de entrada '
                'y sigue las instrucciones para verificar tu cuenta.'
            )
            return redirect('account_email_verification_sent')
            
        except Exception as e:
            messages.error(request, f'Error al enviar el correo: {str(e)}')
            return redirect('catalogo:index')
    
    return render(request, 'reenviar_verificacion.html')

@login_required
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    context = {
        'pedido': pedido,
        'items': pedido.items.all(),
    }
    return render(request, 'detalle_pedido.html', context)


def api_carrito_cantidad(request):
    """API endpoint para obtener la cantidad de items en el carrito"""
    try:
        if request.user.is_authenticated:
            carrito = Carrito.objects.filter(usuario=request.user, activo=True).first()
        else:
            sesion_id = request.session.session_key
            if sesion_id:
                carrito = Carrito.objects.filter(sesion_id=sesion_id, activo=True).first()
            else:
                carrito = None
        
        cantidad = carrito.cantidad_items if carrito else 0
        
        return JsonResponse({
            'cantidad': cantidad,
            'success': True
        })
    except Exception as e:
        return JsonResponse({
            'cantidad': 0,
            'success': False,
            'error': str(e)
        })
    
def index(request):
    productos_destacados = Producto.objects.filter(destacado=True, disponible=True)[:8]
    productos_nuevos = Producto.objects.filter(disponible=True).order_by('-fecha_creacion')[:8]
    productos_mas_vendidos = Producto.objects.filter(disponible=True).order_by('-vendidos')[:8]
    categorias = Categoria.objects.all()[:6]
    
    # Obtener imágenes activas del carrusel
    carrusel_imagenes = CarruselImagen.objects.filter(activo=True).order_by('orden')
    
    context = {
        'destacados': productos_destacados,
        'nuevos': productos_nuevos,
        'mas_vendidos': productos_mas_vendidos,
        'categorias': categorias,
        'carrusel_imagenes': carrusel_imagenes,  # Importante para el carrusel
    }
    return render(request, 'index.html', context)

@require_GET
def obtener_contenido_caja(request, producto_id):
    """API para obtener el contenido de la caja en formato JSON"""
    try:
        producto = Producto.objects.get(id=producto_id, disponible=True)
        
        if not producto.venta_por_caja:
            return JsonResponse({
                'success': False,
                'error': 'Este producto no se vende por caja'
            }, status=400)
        
        contenido = producto.contenido_caja
        
        # Obtener detalles de los productos incluidos
        items_detalle = []
        for item in contenido.get('items', []):
            try:
                producto_incluido = Producto.objects.get(id=item['producto_id'])
                items_detalle.append({
                    'id': producto_incluido.id,  # ← Añadir ID
                    'producto_id': producto_incluido.id,
                    'nombre': producto_incluido.nombre,
                    'slug': producto_incluido.slug,  # ← AÑADIR EL SLUG AQUÍ
                    'cantidad': item['cantidad'],
                    'imagen': producto_incluido.imagen_principal.url if producto_incluido.imagen_principal else None,
                    'precio_unitario': float(producto_incluido.precio_actual()),
                    'stock': producto_incluido.existencias  # ← Añadir stock para mostrar disponibilidad
                })
            except Producto.DoesNotExist:
                continue
        
        total_unidades = sum(item['cantidad'] for item in items_detalle)
        precio_por_unidad = producto.get_precio_por_unidad()
        
        return JsonResponse({
            'success': True,
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'venta_por_caja': True,
                'precio_caja': float(producto.precio_caja) if producto.precio_caja else None,
                'precio_por_unidad': float(precio_por_unidad) if precio_por_unidad else None,
                'total_unidades': total_unidades
            },
            'contenido': items_detalle
        })
    except Producto.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Producto no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)