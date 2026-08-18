"""Propagation of the DRF actor to the ``django-pghistory`` context.

``pghistory.middleware.HistoryMiddleware`` sets the actor context from
``request.user``, but with DRF + SimpleJWT the user is resolved **inside** the
view (in ``perform_authentication``), after the middleware already ran. So for
JWT-authenticated requests the pghistory context is set explicitly in a
reusable DRF layer.

The actor travels as ``user`` inside the context that PostgreSQL triggers write
to the event table (``pghistory.Context``). If there is no authenticated actor,
no attribution is set → the audit row keeps a ``NULL`` actor (auditable
anomaly: never a false attribution).
"""
from __future__ import annotations

from typing import Any

import pghistory
from rest_framework.request import Request
from rest_framework.response import Response


class PGHistoryContextMixin:
    """DRF mixin that sets the actor in the pghistory context.

    Applies ``pghistory.context(user=<id>)`` for the whole view ``dispatch`` so
    any write (INSERT/UPDATE) on tracked models is attributed to the
    authenticated user. If the request has no authenticated user, no
    attribution is set.

    Lifecycle: the context is **opened** in ``initial`` (once ``request.user``
    is resolved) and **closed** in ``finalize_response`` (always invoked by
    ``dispatch``). Closing explicitly prevents the actor contextvar from
    surviving the request under reused worker threads (Gunicorn) and leaking to
    a later request (cross-attribution).

    Usage: inherit BEFORE the DRF base class, e.g.::

        class CertificateViewSet(PGHistoryContextMixin, viewsets.ModelViewSet):
            ...
    """

    #: pghistory context manager opened for this request (or ``None``).
    _pgh_cm: Any = None

    def initial(self, request: Request, *args: Any, **kwargs: Any) -> None:
        """Open the pghistory actor context after authenticating the request.

        :param request: authenticated DRF request.
        :type request: rest_framework.request.Request
        :param args: dispatch positional args.
        :param kwargs: dispatch keyword args.
        :rtype: None
        """
        super().initial(request, *args, **kwargs)
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            cm = pghistory.context(user=user.pk)
            cm.__enter__()
            self._pgh_cm = cm

    def finalize_response(
        self, request: Request, response: Response, *args: Any, **kwargs: Any
    ) -> Response:
        """Close the actor context opened in ``initial`` (if any).

        :param request: DRF request.
        :type request: rest_framework.request.Request
        :param response: response to finalize.
        :type response: rest_framework.response.Response
        :returns: the finalized response.
        :rtype: rest_framework.response.Response
        """
        response = super().finalize_response(request, response, *args, **kwargs)
        cm = self._pgh_cm
        if cm is not None:
            cm.__exit__(None, None, None)
            self._pgh_cm = None
        return response
