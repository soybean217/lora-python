class DuplicateError(Exception):
    def __init__(self, key_name, key_value):
        self.key_name = key_name
        self.key_value = key_value

    def __str__(self):
        return self.key_name + ' ' +self.key_value + ' already exist'


class KeyDuplicateError(Exception):
    def __init__(self, key_name, key_value):
        self.key_name = key_name
        self.key_value = key_value

    def __str__(self):
        return self.key_name + self.key_value + ' already exist'


class PermissionDeny(Exception):
    def __init__(self, key_name, key_value):
        self.key_name = key_name
        self.key_value = key_value

    def __str__(self):
        return self.key_name + ' already registered in APP:' + self.key_value


class ReadOnlyDeny(Exception):
    def __str__(self):
        return "Attempting to alter read-only value"