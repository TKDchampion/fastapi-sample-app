class DomainException(Exception):
    def __init__(self, msg: str, type: str = "domain_error", code: int = 400):
        self.msg = msg
        self.type = type
        self.code = code
