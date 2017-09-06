from passlib.context import CryptContext
from .tokens import TokenManager


class UserManager:
    def __init__(self, app):
        self.enable_email = True
        self.send_password_changed_email = True
        self.send_registered_email = True
        self.enable_confirm_email = True

        self.show_email_does_not_exist = True
        self.enable_retype_password = True
        self.enable_invitation = True
        self.enable_forgot_password = True

        self.password_hash_mode = 'passlib'     # or Flask-Security or plaintext
        self.password_hash = 'bcrypt'
        self.password_salt = app.config['SECRET_KEY']  # for Flask-Security
        self.password_crypt_context = CryptContext(schemes=[self.password_hash])

        self.confirm_email_email_template = 'emails/confirm_email'
        self.forgot_password_email_template = 'emails/forgot_password'
        self.password_changed_email_template = 'emails/password_changed'
        self.registered_email_template = 'emails/registered'
        self.username_changed_email_template = 'emails/username_changed'
        self.invite_email_template = 'emails/invite'

        self.app_name = 'LoRaWAN'

        self.token_manager = TokenManager()
        self.token_manager.setup(app.config.get('SECRET_KEY'))

        self.reset_password_expiration = 2*24*3600
        self.invite_expiration = 30*24*3600
        self.confirm_email_expiration = 2*24*3600

        self.confirm_email_url = '/user/confirm-email'
        self.resend_confirm_email_url = '/user/resend-confirm-email'
        self.reset_password_url = '/user/reset-password'
        self.register_url = '/register'
        self.forgot_password_url = '/user/forgot-password'
