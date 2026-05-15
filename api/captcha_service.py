import base64
import hashlib
import hmac
import random
import string
import uuid
from datetime import timedelta
from io import BytesIO

from django.db import transaction
from django.utils import timezone

from users.auth_models import CaptchaChallenge


class CaptchaService:
    CODE_LENGTH = 6
    EXPIRE_MINUTES = 5
    MAX_ATTEMPTS = 5
    IMAGE_WIDTH = 240
    IMAGE_HEIGHT = 70
    RIGHT_MARGIN = 12
    LEFT_MARGIN = 10

    @classmethod
    def _generate_code(cls) -> str:
        characters = string.ascii_uppercase + string.digits
        return "".join(random.choices(characters, k=cls.CODE_LENGTH))

    @classmethod
    def _hash_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @classmethod
    def _render_image(cls, code: str) -> str:
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError as exc:
            raise RuntimeError("Pillow is required to generate captcha images.") from exc

        image = Image.new("RGB", (cls.IMAGE_WIDTH, cls.IMAGE_HEIGHT), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        try:
            # Try to load a system font with larger size for better readability
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
                "/System/Library/Fonts/Arial.ttf",  # macOS
                "C:\\Windows\\Fonts\\arial.ttf",  # Windows
                "/Library/Fonts/Arial.ttf",  # macOS alternative
            ]
            font = None
            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(font_path, 36)  # Larger font size
                    break
                except (OSError, IOError):
                    continue

            # Fallback to default font if system fonts not available
            if font is None:
                font = ImageFont.load_default()

        except Exception:
            font = None

        # for index, char in enumerate(code):
        #     x = 8 + index * 32 + random.randint(-3, 3)  # Increased spacing for larger font
        #     y = 8 + random.randint(-3, 3)  # Adjusted vertical positioning
        #     draw.text((x, y), char, fill=(0, 0, 0), font=font)
        x_cursor = 10
        for index, char in enumerate(code):
            # get exact bbox of character
            bbox = draw.textbbox((0, 0), char, font=font)
            char_width = bbox[2] - bbox[0]
            char_height = bbox[3] - bbox[1]

            x = x_cursor + random.randint(-2, 2)
            y = (cls.IMAGE_HEIGHT - char_height) // 2 + random.randint(-3, 3)

            draw.text((x, y), char, fill=(0, 0, 0), font=font)
            # advance cursor based on real width
            x_cursor += char_width + 10

        for _ in range(6):
            start = (
                random.randint(0, cls.IMAGE_WIDTH),
                random.randint(0, cls.IMAGE_HEIGHT),
            )
            end = (
                random.randint(0, cls.IMAGE_WIDTH),
                random.randint(0, cls.IMAGE_HEIGHT),
            )
            draw.line(
                [start, end],
                fill=(random.randint(120, 180), random.randint(120, 180), random.randint(120, 180)),
                width=1,
            )

        for _ in range(40):
            x = random.randint(0, cls.IMAGE_WIDTH - 1)
            y = random.randint(0, cls.IMAGE_HEIGHT - 1)
            draw.point((x, y), fill=(random.randint(100, 220), random.randint(100, 220), random.randint(100, 220)))

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"

    @classmethod
    def generate_captcha(cls, ip_address: str | None = None) -> dict[str, object]:
        code = cls._generate_code()
        expires_at = timezone.now() + timedelta(minutes=cls.EXPIRE_MINUTES)
        challenge = CaptchaChallenge.objects.create(
            code_hash=cls._hash_code(code),
            expires_at=expires_at,
            ip_address=ip_address,
        )

        return {
            "captcha_id": str(challenge.challenge_id),
            "captcha_image": cls._render_image(code),
            "expires_in": cls.EXPIRE_MINUTES * 60,
        }

    @classmethod
    def verify_captcha(cls, challenge_id: str, answer: str) -> tuple[bool, int]:
        try:
            parsed_id = uuid.UUID(challenge_id)
        except Exception:
            return False, 0

        with transaction.atomic():
            challenge = (
                CaptchaChallenge.objects.select_for_update()
                .filter(challenge_id=parsed_id)
                .first()
            )
            if not challenge:
                return False, 0

            if challenge.used or challenge.is_expired() or challenge.attempts >= cls.MAX_ATTEMPTS:
                return False, 0

            if challenge.verified:
                return False, 0

            challenge.attempts += 1
            correct = hmac.compare_digest(challenge.code_hash, cls._hash_code(answer))
            if correct:
                challenge.verified = True
                challenge.save(update_fields=["attempts", "verified"])
                return True, cls.get_captcha_ttl(challenge_id)

            challenge.save(update_fields=["attempts"])
            return False, cls.get_captcha_ttl(challenge_id)

    @classmethod
    def validate_captcha(cls, challenge_id: str) -> bool:
        try:
            parsed_id = uuid.UUID(challenge_id)
        except Exception:
            return False

        challenge = CaptchaChallenge.objects.filter(challenge_id=parsed_id).first()
        return bool(
            challenge
            and challenge.verified
            and not challenge.used
            and not challenge.is_expired()
        )

    @classmethod
    def get_captcha_ttl(cls, challenge_id: str) -> int:
        try:
            parsed_id = uuid.UUID(challenge_id)
        except Exception:
            return 0

        challenge = CaptchaChallenge.objects.filter(challenge_id=parsed_id).first()
        if not challenge or challenge.is_expired():
            return 0

        remaining = challenge.expires_at - timezone.now()
        return max(0, int(remaining.total_seconds()))

    @classmethod
    def mark_captcha_used(cls, challenge_id: str) -> None:
        try:
            parsed_id = uuid.UUID(challenge_id)
        except Exception:
            return

        with transaction.atomic():
            challenge = (
                CaptchaChallenge.objects.select_for_update()
                .filter(challenge_id=parsed_id)
                .first()
            )
            if not challenge or challenge.used:
                return

            challenge.mark_used()
