import logging
from django.conf import settings
from kavenegar import APIException, HTTPException, KavenegarAPI

logger = logging.getLogger(__name__)
DEFAULT_TEMPLATE = "verify"


class KavenegarService:
    def __init__(self):
        self.api = KavenegarAPI(settings.KAVENEGAR_API_KEY)

    def _is_available(self):
        if self.api is None:
            logger.error("Kavenegar API client is not initialized.")
            return False
        return True

    def send_verification_code(self, receptor: str, token: str, template: str = DEFAULT_TEMPLATE) -> bool:
        if not self._is_available():
            return False
        try:
            self.api.verify_lookup({"receptor": receptor, "token": token, "template": template})
            logger.info("OTP sent successfully.", extra={"phone_number": receptor})
            return True
        except (APIException, HTTPException) as exc:
            logger.error("Kavenegar error: %s", exc)
        except Exception:
            logger.exception("Unexpected error while sending verification code.")
        return False

    def send_custom_sms(self, receptor: str, message: str) -> bool:
        if not self._is_available():
            return False
        try:
            self.api.sms_send({"receptor": receptor, "message": message})
            logger.info("Custom SMS sent successfully.", extra={"phone_number": receptor})
            return True
        except (APIException, HTTPException) as exc:
            logger.error("Kavenegar error: %s", exc)
        except Exception:
            logger.exception("Unexpected error while sending SMS.")
        return False