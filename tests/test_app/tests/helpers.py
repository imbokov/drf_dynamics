class MockRequest:
    def __init__(self, user=None, query_params=None):
        self.user = user
        self.query_params = query_params
