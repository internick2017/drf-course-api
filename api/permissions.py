from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user


class IsProductOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission for products - only product owners can edit.
    For now, we'll allow read access to everyone and write access to authenticated users.
    """
    def has_permission(self, request, view):
        # Allow read access to everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow write access to authenticated users
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # For products, object-level permissions are the same as general permissions
        return self.has_permission(request, view)


class IsOrderOwner(permissions.BasePermission):
    """
    Custom permission to only allow order owners to access their orders.
    """
    def has_permission(self, request, view):
        # Only authenticated users can access orders
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Users can only access their own orders
        return obj.user == request.user


class IsOrderItemOwner(permissions.BasePermission):
    """
    Custom permission to only allow order item owners to access their order items.
    """
    def has_permission(self, request, view):
        # Only authenticated users can access order items
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Users can only access order items from their own orders
        return obj.order.user == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit, but allow read access to everyone.
    """
    def has_permission(self, request, view):
        # Allow read access to everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow write access only to admin users
        return request.user and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        # For admin permissions, object-level permissions are the same as general permissions
        return self.has_permission(request, view)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow owners or admins to access objects.
    """
    def has_permission(self, request, view):
        # Only authenticated users can access
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Users can access their own objects or if they are admin
        return obj.user == request.user or request.user.is_staff


class IsAuthenticatedOrReadOnlyForProducts(permissions.BasePermission):
    """
    Custom permission for products - read access for everyone, write for authenticated users.
    """
    def has_permission(self, request, view):
        # Allow read access to everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow write access to authenticated users
        return request.user and request.user.is_authenticated
