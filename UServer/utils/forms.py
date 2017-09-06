from werkzeug.datastructures import MultiDict

BooleanFields = ['token', 'adr', 'que_down', 'check_fcnt', 'public', 'disable']
IntFields = ['fcnt_up', 'fcnt_down', 'latitude', 'longitude', 'altitude', 'periodicity', 'fcnt']


def get_formdata_from_json(request):
    if request.json:
        formdata = MultiDict(request.json)
        return formdata


def get_formdata_from_json_or_form(request):
    if request.json:
        formdata = MultiDict(request.json)
    else:
        dict = {}
        for item in request.form:
            if item in BooleanFields:
                if request.form[item] == 'True':
                    dict[item] = True
                elif request.form[item] == 'False':
                    dict[item] = False
                else:
                    raise AssertionError('%s must be boolean, True or False' % item)
            elif item in IntFields:
                dict[item] = int(request.form[item])
            else:
                dict[item] = request.form[item]
        formdata = MultiDict(dict)
    return formdata