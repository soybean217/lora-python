from binascii import hexlify


class KeyDuplicateError(Exception):
    def __init__(self, key):
        self.key = key

    def __str__(self):
        return self.key + ' already exist'


class ResourceAlreadyExistError(Exception):
    def __init__(self, name, value):
        if isinstance(value, bytes):
            self.value = hexlify(value)
        else:
            self.value = value
        self.name = name

    def __str__(self):
        return '%s %s already exist' % (self.name, self.value)


class PatchError(Exception):
    def __init__(self, resource, key):
        self.resource = resource
        self.key = key

    def __str__(self):
        return '%(resource)s has no attribute named %(name)s or %(name)s is not allowed to wrote by user'\
               % {'name': self.key, 'resource': self.resource}


class FieldNotExist(Exception):
    def __init__(self, form_name, field_name):
        self.form_name = form_name
        self.field_name = field_name

    def __str__(self):
        return '%s has no field named %s' % (self.form_name, self.field_name)


class PasswordError(Exception):
    def __init__(self, name, password):
        self.name = name
        self.password = password

    def __str__(self):
        return "%s and %s don't match" % (self.name, self.password)


class AppSKeyAbsence(Exception):
    def __init__(self, key):
        """
        :param key: str
        :return:
        """
        self.key = key

    def __str__(self):
        return 'AppSKey Absence in %s' % self.key


class SeqNoError(Exception):
    def __init__(self, seqno_gave, seqno_expect):
        """
        :param seqno_gave: int
        :param seqno_expect: int
        :return:
        """
        self.seqno_gave = seqno_gave
        self.seqno_expect = seqno_expect

    def __str__(self):
        return 'Seqno %d is Expected but %d is Got' % (self.seqno_expect, self.seqno_gave)


class ReadOnlyDeny(Exception):
    def __str__(self):
        return "Attempting to alter read-only value"


class QueOccupied(Exception):
    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        if self.msg is None:
            return 'Queue limit error.'
        else:
            return self.msg


class AppDuplicateError(Exception):
    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        if self.msg is None:
            return "AppDuplicateError"
        else:
            return self.msg