class APIError(Exception):
    pass


class AuthorizationError(APIError):
    pass


class NetworkError(APIError):
    pass
