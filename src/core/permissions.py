from rest_framework.permissions import SAFE_METHODS, BasePermission

_METHOD_TO_PERM = {
    "GET": "view",
    "HEAD": "view",
    "OPTIONS": "view",
    "POST": "add",
    "PUT": "change",
    "PATCH": "change",
    "DELETE": "delete",
}


class HasModelPermission(BasePermission):
    """
    Проверяет модельные права. Если пользователь не аутентифицирован —
    разрешаем только SAFE (GET/HEAD/OPTIONS).
    Чтобы работало, во ViewSet нужно указать `permission_model = <Model>`.
    """

    def has_permission(self, request, view):
        model = getattr(view, "permission_model", None)
        if model is None:
            return True

        method = request.method.upper()

        # Анонима пускаем только на SAFE-методы
        if not request.user or not request.user.is_authenticated:
            return method in SAFE_METHODS

        # Для аутентифицированных проверяем конкретное право
        codename_suffix = _METHOD_TO_PERM.get(method)
        if codename_suffix is None:
            return False

        app_label = model._meta.app_label
        model_name = model._meta.model_name
        perm_code = f"{app_label}.{codename_suffix}_{model_name}"
        return request.user.has_perm(perm_code)


class DenyReadonlyOnCreate(BasePermission):
    """
    Разрешает POST только аутентифицированным пользователям, которые НЕ в группе 'readonly'.
    Остальные методы не трогаем (True), чтобы ими занимался другой пермишен.
    """

    def has_permission(self, request, view):
        if request.method != "POST":
            return True  # пусть обрабатывает следующий пермишен в списке
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return not user.groups.filter(name="readonly").exists()
