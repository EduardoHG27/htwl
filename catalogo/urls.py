# catalogo/urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'catalogo'

urlpatterns = [
    # Página principal
    path('', views.index, name='index'),
    
    # Productos
    path('productos/', views.lista_productos, name='lista_productos'),
    path('producto/<slug:slug>/', views.detalle_producto, name='detalle_producto'),
    
    # Autenticación
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('reenviar-verificacion/', views.reenviar_verificacion, name='reenviar_verificacion'),
    
    # Carrito
    path('carrito/', views.carrito_view, name='carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/actualizar/<int:item_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    
    # Checkout y pedidos
    path('checkout/', views.checkout_view, name='checkout'),
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),
    path('pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('pedido/confirmado/<int:pedido_id>/', views.pedido_confirmado, name='pedido_confirmado'),
    
    # Transferencias
    path('transferencia/<int:pedido_id>/', views.instrucciones_transferencia, name='instrucciones_transferencia'),
    path('transferencia/subir/<int:pedido_id>/', views.subir_comprobante, name='subir_comprobante'),
    
    # Reseñas
    path('reseña/agregar/<int:producto_id>/', views.agregar_reseña, name='agregar_reseña'),
    
    # Exportar catálogo
    path('exportar/excel/', views.exportar_catalogo_excel, name='exportar_excel'),
    path('exportar/csv/', views.exportar_catalogo_csv, name='exportar_csv'),
    path('exportar/pdf/', views.exportar_catalogo_pdf, name='exportar_pdf'),
    
    # API
    path('api/carrito/cantidad/', views.api_carrito_cantidad, name='api_carrito_cantidad'),
    path('api/caja/contenido/<int:producto_id>/', views.obtener_contenido_caja, name='contenido_caja'),
]

# Servir archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)