from object.asserts import Assertions
from frequency_plan import FrequencyPlan
from utils.exception import ReadOnlyDeny
from utils.db0 import db0, ConstDB0
from binascii import hexlify
from utils.log import logger, ConstLog


class FieldApp:
    user_id = 'user_id'
    app_eui = 'app_eui'
    freq_plan = 'freq_plan'


class Application:
    fields = (FieldApp.user_id, FieldApp.freq_plan)
    _vars_can_write = ()
    _assert_switcher = {
        FieldApp.app_eui: Assertions.a_eui,
        FieldApp.user_id: Assertions.a_positive_int,
        FieldApp.freq_plan: FrequencyPlan.assert_isinstanceof,
    }

    def __setattr__(self, key, value):
        if hasattr(self, key):
            if key not in self._vars_can_write:
                raise ReadOnlyDeny
        self._assert_switcher[key](value)
        self.__dict__[key] = value

    def __init__(self, user_id, app_eui, freq_plan):
        self.user_id = user_id
        self.app_eui = app_eui
        self.freq_plan = freq_plan

    @staticmethod
    def assert_isinstanceof(value):
        assert isinstance(value, Application), '%r is not a valid Application' % value

    class objects:
        @staticmethod
        def get(app_eui):
            info = db0.hmget(ConstDB0.app + hexlify(app_eui).decode(), Application.fields)
            logger.info(info)
            try:
                user = int(info[0])
                freq_plan = info[1]
                if freq_plan is not None:
                    freq_plan = FrequencyPlan(freq_plan.decode())
                else:
                    freq_plan = FrequencyPlan.EU863_870
                app = Application(user_id=user, app_eui=app_eui, freq_plan=freq_plan)
                return app
            except TypeError as error:
                logger.debug(ConstLog.application + str(error))
