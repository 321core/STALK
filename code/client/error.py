# -*- coding: utf-8 -*-
# error.py


class APIError(Exception):
	pass


class AuthorizationError(APIError):
	pass


class NetworkError(APIError):
	pass
