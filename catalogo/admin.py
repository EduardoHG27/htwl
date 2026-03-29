# catalogo/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import CarruselImagen, Categoria, Marca, Producto, Reseña, Pedido, ItemPedido, Carrito, ItemCarrito

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'slug', 'productos_count']
    prepopulated_fields = {'slug': ('nombre',)}
    search_fields = ['nombre']
    
    def productos_count(self, obj):
        return obj.productos.count()
    productos_count.short_description = 'Productos'

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'slug', 'logo_preview', 'productos_count']
    prepopulated_fields = {'slug': ('nombre',)}
    search_fields = ['nombre']
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "Sin logo"
    logo_preview.short_description = 'Logo'
    
    def productos_count(self, obj):
        return obj.productos.count()
    productos_count.short_description = 'Productos'

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ['producto', 'cantidad', 'precio_unitario']
    
    def subtotal(self, obj):
        return obj.subtotal
    subtotal.short_description = 'Subtotal'

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'categoria', 'marca', 'precio_actual', 'existencias', 'vendidos', 'destacado', 'disponible', 'imagen_preview']
    list_display_links = ['id', 'nombre']  
    list_filter = ['categoria', 'marca', 'destacado', 'disponible', 'venta_por_caja']
    search_fields = ['nombre', 'descripcion']
    prepopulated_fields = {'slug': ('nombre',)}
    list_editable = ['destacado', 'disponible', 'existencias']
    readonly_fields = ['vendidos', 'fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'slug', 'descripcion', 'especificaciones')
        }),
        ('Clasificación', {
            'fields': ('categoria', 'marca')
        }),
        ('Precios y Stock', {
            'fields': ('precio', 'precio_oferta', 'existencias', 'vendidos')
        }),
        ('Venta por Caja', {
            'fields': ('venta_por_caja', 'precio_caja', 'contenido_caja'),
            'classes': ('collapse',)
        }),
        ('Imágenes', {
            'fields': ('imagen_principal', 'imagen_1', 'imagen_2')
        }),
        ('Estado', {
            'fields': ('destacado', 'disponible')
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion')
        }),
    )

    def imagen_preview(self, obj):
        if obj.imagen_principal:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.imagen_principal.url)
        return "Sin imagen"
    imagen_preview.short_description = 'Imagen'
    
    def precio_actual(self, obj):
        precio = obj.precio_actual()
        if obj.precio_oferta:
            return format_html(
                '<span style="color:red;"><del>${}</del> <strong>${}</strong></span>',
                obj.precio, obj.precio_oferta
            )
        return f"${precio}"
    precio_actual.short_description = 'Precio'
    
    actions = ['marcar_como_destacado', 'quitar_destacado', 'marcar_disponible', 'marcar_no_disponible']
    
    def marcar_como_destacado(self, request, queryset):
        queryset.update(destacado=True)
    marcar_como_destacado.short_description = "Marcar como destacados"
    
    def quitar_destacado(self, request, queryset):
        queryset.update(destacado=False)
    quitar_destacado.short_description = "Quitar destacado"
    
    def marcar_disponible(self, request, queryset):
        queryset.update(disponible=True)
    marcar_disponible.short_description = "Marcar como disponibles"
    
    def marcar_no_disponible(self, request, queryset):
        queryset.update(disponible=False)
    marcar_no_disponible.short_description = "Marcar como no disponibles"

# 🟢 UNA SOLA DEFINICIÓN DE PEDIDO - COMBINANDO AMBAS CONFIGURACIONES
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    # List display - combinado de ambas versiones
    list_display = ['id', 'usuario', 'fecha_creacion', 'total', 'metodo_pago', 'estado_pago', 'estado', 'envio_resumen']
    list_filter = ['estado', 'estado_pago', 'metodo_pago', 'tipo_entrega', 'fecha_creacion']
    search_fields = ['id', 'usuario__username', 'nombre_completo', 'telefono', 'referencia_pago']
    inlines = [ItemPedidoInline]
    readonly_fields = ['fecha_creacion']
    
    fieldsets = (
        ('Información básica', {
            'fields': ('usuario', 'fecha_creacion', 'metodo_pago', 'tipo_entrega')
        }),
        ('Estados', {
            'fields': ('estado', 'estado_pago')
        }),
        ('Montos', {
            'fields': ('subtotal', 'costo_envio', 'iva', 'total')
        }),
        ('Información de entrega', {
            'fields': ('nombre_completo', 'direccion', 'ciudad', 'codigo_postal', 'telefono')
        }),
        ('Pago por transferencia', {
            'fields': ('referencia_pago', 'comprobante_pago', 'fecha_pago', 'observaciones_pago'),
            'classes': ('collapse',)
        }),
    )
    
    # Actions - combinadas de ambas versiones
    actions = [
        'marcar_como_procesando', 
        'marcar_como_enviado', 
        'marcar_como_entregado', 
        'marcar_como_cancelado',
        'marcar_pago_verificado', 
        'marcar_pago_rechazado'
    ]
    
    # Métodos personalizados
    def envio_resumen(self, obj):
        return f"{obj.ciudad}, {obj.nombre_completo}"
    envio_resumen.short_description = 'Destinatario'
    
    # Actions de estado
    def marcar_como_procesando(self, request, queryset):
        queryset.update(estado='procesando')
    marcar_como_procesando.short_description = "Marcar como procesando"
    
    def marcar_como_enviado(self, request, queryset):
        for pedido in queryset:
            if not pedido.numero_seguimiento:
                pedido.numero_seguimiento = f"TRACK-{pedido.id}-{pedido.fecha_creacion.strftime('%Y%m%d')}"
            pedido.estado = 'enviado'
            pedido.save()
    marcar_como_enviado.short_description = "Marcar como enviado"
    
    def marcar_como_entregado(self, request, queryset):
        queryset.update(estado='entregado')
    marcar_como_entregado.short_description = "Marcar como entregado"
    
    def marcar_como_cancelado(self, request, queryset):
        # Devolver stock si se cancela
        for pedido in queryset:
            for item in pedido.items.all():
                producto = item.producto
                producto.existencias += item.cantidad
                producto.vendidos -= item.cantidad
                producto.save()
            pedido.estado = 'cancelado'
            pedido.save()
    marcar_como_cancelado.short_description = "Marcar como cancelado"
    
    # Actions de pago
    def marcar_pago_verificado(self, request, queryset):
        queryset.update(estado_pago='pagado')
    marcar_pago_verificado.short_description = "Marcar pago como verificado"
    
    def marcar_pago_rechazado(self, request, queryset):
        queryset.update(estado_pago='rechazado')
    marcar_pago_rechazado.short_description = "Marcar pago como rechazado"

# 🟢 ELIMINA ESTA LÍNEA (ya está registrado con @admin.register)
# admin.site.register(Pedido, PedidoAdmin)  ← BORRAR

@admin.register(Reseña)
class ReseñaAdmin(admin.ModelAdmin):
    list_display = ['producto', 'usuario', 'calificacion', 'comentario_corto', 'fecha_creacion']
    list_filter = ['calificacion', 'fecha_creacion']
    search_fields = ['producto__nombre', 'usuario__username', 'comentario']
    
    def comentario_corto(self, obj):
        return obj.comentario[:50] + '...' if len(obj.comentario) > 50 else obj.comentario
    comentario_corto.short_description = 'Comentario'

@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'sesion_id', 'activo', 'fecha_creacion', 'items_count', 'total']
    list_filter = ['activo', 'fecha_creacion']
    
    def items_count(self, obj):
        return obj.cantidad_items
    items_count.short_description = 'Items'

@admin.register(ItemCarrito)
class ItemCarritoAdmin(admin.ModelAdmin):
    list_display = ['carrito', 'producto', 'cantidad', 'fecha_agregado']


@admin.register(CarruselImagen)
class CarruselImagenAdmin(admin.ModelAdmin):
    list_display = ['imagen_preview', 'titulo', 'orden', 'activo', 'fecha_creacion']
    list_editable = ['orden', 'activo']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['titulo', 'subtitulo']
    fieldsets = (
        ('Contenido', {
            'fields': ('titulo', 'subtitulo', 'imagen', 'url')
        }),
        ('Configuración', {
            'fields': ('orden', 'activo')
        }),
    )
    
    def imagen_preview(self, obj):
        return obj.imagen_preview()
    imagen_preview.short_description = 'Vista previa'