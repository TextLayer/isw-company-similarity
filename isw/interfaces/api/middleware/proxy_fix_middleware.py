from werkzeug.middleware.proxy_fix import ProxyFix


def init_proxy_fix(app):
    """
    Initialise ProxyFix middleware to handle X-Forwarded headers from ALB
    """
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
