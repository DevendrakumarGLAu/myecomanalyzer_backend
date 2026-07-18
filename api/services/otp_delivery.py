"""
OTP delivery for the forgot-password flow.

Two channels, each behind a tiny provider class so either can be swapped
without touching the password-reset controller:
- email: SMTP            (EmailOTPProvider)
- sms:   AWS SNS         (SmsOTPProvider) — boto3 is already a project
  dependency (used for S3 uploads elsewhere), so this needs no new package.
"""
import smtplib
from email.mime.text import MIMEText

from decouple import config


class EmailOTPProvider:
    def __init__(self):
        self.host = config("SMTP_HOST", default="smtp.gmail.com")
        self.port = config("SMTP_PORT", default=587, cast=int)
        self.username = config("SMTP_USERNAME", default="")
        self.password = config("SMTP_APP_PASSWORD", default="").replace(" ", "")

    def send(self, to_email, otp):
        if not self.username or not self.password:
            raise RuntimeError("SMTP_USERNAME/SMTP_APP_PASSWORD are not configured")

        message = MIMEText(f"Your password reset OTP is {otp}. It expires shortly — do not share it.")
        message["Subject"] = "Your password reset OTP"
        message["From"] = self.username
        message["To"] = to_email

        with smtplib.SMTP(self.host, self.port, timeout=10) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.username, [to_email], message.as_string())


class SmsOTPProvider:
    def __init__(self):
        self.region = config(
            "AWS_SNS_REGION_NAME",
            default=config("AWS_S3_REGION_NAME", default="us-east-1"),
        )
        self.access_key = config("AWS_ACCESS_KEY_ID", default="")
        self.secret_key = config("AWS_SECRET_ACCESS_KEY", default="")
        self.sender_id = config("AWS_SNS_SENDER_ID", default="")

    def send(self, to_mobile, otp):
        import boto3

        if not self.access_key or not self.secret_key:
            raise RuntimeError("AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY are not configured")

        client = boto3.client(
            "sns",
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

        attributes = {
            "AWS.SNS.SMS.SMSType": {"DataType": "String", "StringValue": "Transactional"},
        }
        if self.sender_id:
            attributes["AWS.SNS.SMS.SenderID"] = {"DataType": "String", "StringValue": self.sender_id}

        # SNS requires E.164 format (e.g. +919876543210) — UserProfile.mobile_number
        # isn't currently validated to that format, so a malformed number will
        # raise here rather than silently failing.
        client.publish(
            PhoneNumber=to_mobile,
            Message=f"Your password reset OTP is {otp}. It expires shortly.",
            MessageAttributes=attributes,
        )


def get_otp_provider(channel):
    if channel == "email":
        return EmailOTPProvider()
    if channel == "sms":
        return SmsOTPProvider()
    raise ValueError(f"Unsupported OTP channel: {channel}")
