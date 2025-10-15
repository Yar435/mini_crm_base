from drf_spectacular.extensions import OpenApiAuthenticationExtension


class VersionedJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    # Полный путь к твоему классу аутентификации
    target_class = 'core.auth.VersionedJWTAuthentication'
    name = 'VersionedJWTAuthentication'  # произвольное имя

    def get_security_definition(self, auto_schema):
        # Маппим на стандартный bearerAuth
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }
