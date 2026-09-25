"""
Pluggable authentication for openEHR REST clients.

Clients accept any of the following as ``auth_method`` / ``admin_auth_method``
on their config:

- ``None`` — no credentials (e.g. FerroEHR with ``FERROEHR__AUTH__ENABLED=false``)
- :class:`BasicAuth` — HTTP Basic (or a plain ``(username, password)`` tuple)
- :class:`BearerAuth` — ``Authorization: Bearer <token>`` from a static token
  or a token-provider callable (sync or async), e.g. for OIDC access tokens
  that the caller refreshes
- any other :class:`httpx.Auth` implementation

Token *acquisition* (client-credentials flow, refresh tokens, ...) is out of
scope: callers supply the token, or a provider callable that returns a
currently valid one.

Example:
    >>> from oehrpy.client import BearerAuth, FerroEHRClient
    >>> async def get_token() -> str:
    ...     return await my_oidc_session.access_token()
    >>> client = FerroEHRClient(auth_method=BearerAuth(token_provider=get_token))
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator

import httpx

TokenProvider = Callable[[], str | Awaitable[str]]


class BasicAuth(httpx.BasicAuth):
    """HTTP Basic authentication.

    Thin wrapper around :class:`httpx.BasicAuth` that keeps the username
    readable (for logging/debugging) and never exposes the password in
    ``repr``.
    """

    def __init__(self, username: str, password: str) -> None:
        super().__init__(username, password)
        self.username = username

    def __repr__(self) -> str:
        return f"BasicAuth(username={self.username!r})"


class BearerAuth(httpx.Auth):
    """Bearer-token authentication (``Authorization: Bearer <token>``).

    Pass either a static ``token`` or a ``token_provider`` callable. The
    provider is invoked for every request, so it should cache the token and
    only refresh it when it is about to expire. Async providers are only
    supported with the async client (which is what oehrpy uses).

    Args:
        token: A static access token.
        token_provider: Callable returning the current access token (sync or
            async).
    """

    def __init__(
        self,
        token: str | None = None,
        *,
        token_provider: TokenProvider | None = None,
    ) -> None:
        if (token is None) == (token_provider is None):
            raise ValueError("BearerAuth needs exactly one of 'token' or 'token_provider'")
        self._token = token
        self._token_provider = token_provider

    def __repr__(self) -> str:
        kind = "token_provider" if self._token_provider else "token"
        return f"BearerAuth({kind}=***)"

    async def _get_token(self) -> str:
        if self._token is not None:
            return self._token
        assert self._token_provider is not None
        token = self._token_provider()
        if inspect.isawaitable(token):
            token = await token
        return token

    def sync_auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        if self._token is not None:
            token = self._token
        else:
            assert self._token_provider is not None
            token = self._token_provider()  # type: ignore[assignment]
            if inspect.isawaitable(token):
                raise RuntimeError("An async token_provider requires an async client")
        request.headers["Authorization"] = f"Bearer {token}"
        yield request

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        request.headers["Authorization"] = f"Bearer {await self._get_token()}"
        yield request


#: Anything a client config accepts as ``auth_method``.
AuthMethod = httpx.Auth | tuple[str, str] | None

#: Explicitly send no credentials on a single request, overriding the
#: client-wide default (``auth=None`` on an httpx request means "use the
#: client default").
NO_AUTH = httpx.Auth()
