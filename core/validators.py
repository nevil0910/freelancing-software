import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UppercaseValidator:
    """
    Validate that the password contains at least one uppercase letter.
    """
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter (A-Z)."),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _("Your password must contain at least one uppercase letter (A-Z).")


class SpecialCharacterValidator:
    """
    Validate that the password contains at least one special character.
    """
    def validate(self, password, user=None):
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~;]', password):
            raise ValidationError(
                _("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>_-+=[]\\\/`~;)."),
                code='password_no_special',
            )

    def get_help_text(self):
        return _("Your password must contain at least one special character.")

class UsernameValidate:
    USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9._-]{2,30}$')

    @staticmethod
    def normalize_username(value: str) -> str:
        return (value or '').strip().lower()

    @staticmethod
    def validate_username_format(username: str) -> None:
        if not UsernameValidate.USERNAME_REGEX.fullmatch(username):
            raise ValidationError(
                _('Username must be at least 2 characters and contain only letters, numbers, underscores, and hyphens.')
            )