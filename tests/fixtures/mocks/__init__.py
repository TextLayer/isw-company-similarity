import requests


class DummyJWT:
    def generate_token(self, subject, data, expires_in):
        return "tok123"


class DummyMail:
    def send_email(self, recipients, subject, template_name, template_data):
        return None


class DummyStorage:
    def __init__(self, *args, **kwargs):
        pass

    def get_download_url(self, key, expires_in):
        return "https://s3/url"


class DummyRegistry:
    def __init__(self, sink):
        self.sink = sink

    def defer(self, name, payload):
        self.sink.append((name, payload))


class RespOK:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {"token": {"key": "abc"}}


class RespBad:
    status_code = 400
    text = "BAD"

    def __init__(self):
        self._response = requests.Response()
        self._response.status_code = 400
        self._response._content = b"BAD"

    def raise_for_status(self):
        raise requests.HTTPError(response=self._response)

    def json(self):
        return {"message": "bad"}
