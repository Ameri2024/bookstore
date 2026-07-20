from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer
from apps.books.models import BookVariant, Pack


class CartViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = CartSerializer

    def get_cart(self, request):
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart

    def retrieve(self, request, pk=None):
        cart = self.get_cart(request)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart = self.get_cart(request)
        book_variant_id = request.data.get('book_variant_id')
        pack_id = request.data.get('pack_id')
        quantity = int(request.data.get('quantity', 1))

        if book_variant_id:
            variant = get_object_or_404(BookVariant, id=book_variant_id, is_active=True)
            item, created = CartItem.objects.get_or_create(cart=cart, book_variant=variant, defaults={'quantity': quantity})
            if not created:
                item.quantity += quantity
                item.save()
        elif pack_id:
            pack = get_object_or_404(Pack, id=pack_id, is_active=True)
            item, created = CartItem.objects.get_or_create(cart=cart, pack=pack, defaults={'quantity': quantity})
            if not created:
                item.quantity += quantity
                item.save()
        else:
            return Response({'error': 'Either book_variant_id or pack_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        cart = self.get_cart(request)
        item_id = request.data.get('item_id')
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'])
    def update_quantity(self, request):
        cart = self.get_cart(request)
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 1))
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        if quantity <= 0:
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        item.quantity = quantity
        item.save()
        return Response(CartItemSerializer(item).data)

    @action(detail=False, methods=['post'])
    def clear_cart(self, request):
        cart = self.get_cart(request)
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            cart = get_object_or_404(Cart, user=request.user)
        else:
            return Response({'error': 'Please log in to place an order.'}, status=status.HTTP_401_UNAUTHORIZED)

        if cart.items.count() == 0:
            return Response({'error': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        for item in cart.items.all():
            if item.book_variant:
                if not item.book_variant.check_stock(item.quantity):
                    return Response({'error': f"Insufficient stock for {item.book_variant}."}, status=status.HTTP_400_BAD_REQUEST)
            elif item.pack:
                if not item.pack.check_stock_for_pack():
                    return Response({'error': f"Insufficient stock for pack {item.pack.name}."}, status=status.HTTP_400_BAD_REQUEST)

        required_fields = ['full_name', 'phone', 'province', 'city', 'address', 'postal_code']
        for field in required_fields:
            if not request.data.get(field):
                return Response({'error': f"'{field}' is required."}, status=status.HTTP_400_BAD_REQUEST)

        total_price = cart.get_total_price()
        final_amount = total_price

        order = Order.objects.create(
            user=request.user,
            full_name=request.data['full_name'],
            phone=request.data['phone'],
            email=request.data.get('email', ''),
            province=request.data['province'],
            city=request.data['city'],
            address=request.data['address'],
            postal_code=request.data['postal_code'],
            total_price=total_price,
            discount_amount=0,
            shipping_cost=0,
            final_amount=final_amount,
        )

        for item in cart.items.all():
            if item.book_variant:
                product_name = str(item.book_variant)
                unit_price = item.book_variant.final_price
                item.book_variant.decrease_stock(item.quantity)
                OrderItem.objects.create(
                    order=order,
                    product_type='book',
                    product_name=product_name,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    total_price=unit_price * item.quantity,
                    book_variant_id=item.book_variant.id
                )
            elif item.pack:
                product_name = item.pack.name
                unit_price = item.pack.final_price
                snapshot = []
                for pack_item in item.pack.items.all():
                    snapshot.append({
                        'book_title': pack_item.book_variant.book.title,
                        'size': pack_item.book_variant.size,
                        'quantity': pack_item.quantity,
                        'price_at_time': pack_item.book_variant.final_price
                    })
                item.pack.decrease_stock_for_pack()
                OrderItem.objects.create(
                    order=order,
                    product_type='pack',
                    product_name=product_name,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    total_price=unit_price * item.quantity,
                    pack_id=item.pack.id,
                    pack_snapshot=snapshot
                )

        cart.items.all().delete()
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)