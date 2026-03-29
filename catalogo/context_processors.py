# catalogo/context_processors.py
from .models import Carrito, Categoria

def carrito_context(request):
    """
    Context processor para información del carrito
    Este nombre debe coincidir con el que está en settings.py: 'catalogo.context_processors.carrito_context'
    """
    carrito = None
    cantidad_items = 0
    total_carrito = 0
    
    try:
        if request.user.is_authenticated:
            # Usuario autenticado
            carrito = Carrito.objects.filter(usuario=request.user, activo=True).first()
        else:
            # Usuario anónimo (por sesión)
            sesion_id = request.session.session_key
            if sesion_id:
                carrito = Carrito.objects.filter(sesion_id=sesion_id, activo=True).first()
        
        if carrito:
            cantidad_items = carrito.cantidad_items
            total_carrito = carrito.total
    except Exception as e:
        # Si hay error (ej. tablas no creadas aún), simplemente pasamos
        print(f"Error en carrito_context: {e}")
        pass
    
    return {
        'carrito': carrito,
        'carrito_cantidad': cantidad_items,
        'carrito_total': total_carrito,
        'categorias': Categoria.objects.all()[:8],  # Para el menú de navegación
    }