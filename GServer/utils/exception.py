from binascii import hexlify


class SendByOtherGateway(Exception):
    pass


class KeyDuplicateError(Exception):
    def __init__(self, key_name, key_value, *args):
        self.key_name = key_name
        self.key_value = key_value
        self.args = args

    def __str__(self):
        if isinstance(self.key_value, bytes):
            self.key_value = hexlify(self.key_value).decode()
        return '%s %s %s already exist' % (self.key_name, self.key_value, self.args)


class PermissionDeny(Exception):
    def __init__(self, key_name, key_value):
        self.key_name = key_name
        self.key_value = key_value

    def __str__(self):
        return '%s already registered in APP:%s' % (self.key_name, self.key_value)


class ReadOnlyDeny(Exception):
    def __str__(self):
        return "Attempting to alter read-only value"


class AccessDeny(Exception):
    def __init__(self, gateway, other):
        self.gateway = gateway
        self.other = other

    def __str__(self):
        return '%s has no right to access gateway %s' % (self.gateway, self.other)


class QueOccupied(Exception):
    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        if self.msg is None:
            return 'Queue limit error.'
        else:
            return self.msg