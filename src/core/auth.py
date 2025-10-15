from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class TokenObtainPairWithVersionSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["token_version"] = getattr(getattr(user, "security", None), "token_version", 1)
        return token


class VersionedJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        claim_ver = int(validated_token.get("token_version", 0))
        current_ver = int(getattr(getattr(user, "security", None), "token_version", 1))
        if claim_ver != current_ver:
            raise exceptions.AuthenticationFailed("Token revoked", code="token_revoked")
        return user
