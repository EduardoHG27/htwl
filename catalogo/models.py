# catalogo/models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    
    class Meta:
        verbose_name_plural = "Categorías"
    
    def __str__(self):
        return self.nombre

class Marca(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='marcas/', blank=True, null=True)
    
    def __str__(self):
        return self.nombre

class Producto(models.Model):
    # Información básica
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField()
    especificaciones = models.JSONField(default=dict, blank=True)
    
    # Relaciones
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    
    # Precios y stock
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    precio_oferta = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    existencias = models.PositiveIntegerField(default=0)
    
    # Imágenes
    imagen_principal = models.ImageField(upload_to='productos/')
    imagen_1 = models.ImageField(upload_to='productos/', blank=True, null=True)
    imagen_2 = models.ImageField(upload_to='productos/', blank=True, null=True)
    
    # Metadatos
    disponible = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Campo adicional para ventas (lo usaremos para ordenar por más vendidos)
    vendidos = models.PositiveIntegerField(default=0)
    
      # Nuevos campos para venta por caja
    venta_por_caja = models.BooleanField(default=False, help_text="¿Este producto se vende por caja?")
    contenido_caja = models.JSONField(default=dict, blank=True, help_text="Contenido de la caja (ej: {'items': [{'producto_id': 1, 'cantidad': 10}]})")
    precio_caja = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Precio de la caja (opcional, si es diferente al precio unitario x cantidad)")


    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return self.nombre
    
    def get_absolute_url(self):
        return reverse('detalle_producto', args=[self.slug])
    
    def precio_actual(self):
        """Retorna el precio actual (normal o en oferta)"""
        return self.precio_oferta if self.precio_oferta else self.precio
    
    def en_stock(self):
        """Verifica si hay stock disponible"""
        return self.existencias > 0
    
    def get_precio_por_unidad(self):
        """Obtiene el precio por unidad cuando se vende por caja"""
        if self.venta_por_caja and self.precio_caja and self.contenido_caja:
            total_unidades = sum(item['cantidad'] for item in self.contenido_caja.get('items', []))
            if total_unidades > 0:
                return self.precio_caja / total_unidades
        return self.precio_actual()

class Reseña(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='reseñas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reseñas')
    calificacion = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['producto', 'usuario']  # Un usuario solo puede reseñar una vez
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.producto.nombre} - {self.calificacion}★"

class Carrito(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='carritos')
    sesion_id = models.CharField(max_length=100, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Carrito {self.id}"
    
    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def cantidad_items(self):
        return self.items.aggregate(total=models.Sum('cantidad'))['total'] or 0

class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['carrito', 'producto']
    
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
    
    @property
    def subtotal(self):
        """Calcula el subtotal del item en el carrito usando el precio actual del producto"""
        if self.producto:
            return self.cantidad * self.producto.precio_actual()
        return 0

class Pedido(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    ESTADOS_PAGO = [
        ('pendiente', 'Pendiente de pago'),
        ('verificando', 'Verificando pago'),
        ('pagado', 'Pagado'),
        ('rechazado', 'Pago rechazado'),
    ]
    
    TIPO_ENTREGA = [
        ('envio', 'Envío a domicilio'),
        ('recoleccion', 'Recolección en tienda'),
    ]
    
    METODOS_PAGO = [
        ('transferencia', 'Transferencia bancaria'),
        ('tarjeta', 'Tarjeta de crédito/débito'),
        ('efectivo', 'Pago contra entrega'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pedidos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Estado
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    estado_pago = models.CharField(max_length=20, choices=ESTADOS_PAGO, default='pendiente')
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='transferencia')
    tipo_entrega = models.CharField(max_length=20, choices=TIPO_ENTREGA, default='envio')
    
    # Montos
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Información de envío
    nombre_completo = models.CharField(max_length=200)
    direccion = models.TextField()
    ciudad = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=20)
    telefono = models.CharField(max_length=20)
    
    # Transferencia
    referencia_pago = models.CharField(max_length=100, blank=True, null=True)
    comprobante_pago = models.ImageField(upload_to='comprobantes/', blank=True, null=True)
    fecha_pago = models.DateTimeField(blank=True, null=True)
    observaciones_pago = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.username}"


# catalogo/models.py (agrega este modelo al final del archivo)

class CarruselImagen(models.Model):
    """
    Modelo para gestionar las imágenes del carrusel principal
    """
    titulo = models.CharField(max_length=200, blank=True, verbose_name="Título")
    subtitulo = models.TextField(blank=True, verbose_name="Subtítulo")
    imagen = models.ImageField(upload_to='carrusel/', verbose_name="Imagen")
    url = models.URLField(blank=True, verbose_name="URL de enlace")
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['orden', '-fecha_creacion']
        verbose_name = "Imagen del carrusel"
        verbose_name_plural = "Imágenes del carrusel"
    
    def __str__(self):
        return self.titulo or f"Imagen {self.id}"
    
    def imagen_preview(self):
        if self.imagen:
            from django.utils.html import format_html
            return format_html('<img src="{}" width="100" height="60" style="object-fit: cover;" />', self.imagen.url)
        return "Sin imagen"
    imagen_preview.short_description = 'Vista previa'

    
class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True,blank=True)
    
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
    
    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad