from wtforms import Form
from wtforms import PasswordField, StringField
from wtforms import validators


class LoginForm(Form):
    # username = StringField('Username', validators=[validators.DataRequired('Username is required'), ])
    username = StringField('Username', validators=[validators.DataRequired('Username is required'), ])
    password = PasswordField('Password', validators=[validators.DataRequired('Password is required'), ])