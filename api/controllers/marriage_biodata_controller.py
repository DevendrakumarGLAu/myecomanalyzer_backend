# api/v1/controllers/marriage_biodata_controller.py
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader, select_autoescape
# from weasyprint import HTML
import pdfkit
from fastapi import HTTPException

from marriage_biodata.models import Biodata
from marriage_user_auth.models import MarriageUser
from biodata_templates.models import Template

# autoescape was previously off (Jinja2's default) — every field in the
# request-supplied `data` dict was interpolated into HTML unescaped, letting
# attacker-controlled values break out into <script> tags or attribute values
# (e.g. via personal.photo inside src="...").
env = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape(["html"]))

# wkhtmltopdf option: block it from reading local files (LFI) via a crafted
# field like personal.photo (e.g. "file:///etc/passwd"). Remote image loading
# is intentionally left enabled since photos are a real feature of this PDF —
# see _sanitize_data below for the scheme restriction that covers SSRF instead.
_PDFKIT_OPTIONS = {
    "disable-local-file-access": "",
}

_ALLOWED_URL_SCHEMES = {"http", "https"}


def _sanitize_data(value):
    """
    Recursively strip any string that parses as a URL with a disallowed
    scheme (file://, javascript:, data:, etc.) — autoescaping stops HTML
    injection, but a field like personal.photo placed straight into
    src="{{ personal.photo }}" is a legitimate-looking attribute value, not an
    escaping problem, so a crafted file:// URL there needs its own check.
    """
    if isinstance(value, dict):
        return {k: _sanitize_data(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_data(v) for v in value]
    if isinstance(value, str):
        parsed = urlparse(value)
        if parsed.scheme and parsed.scheme.lower() not in _ALLOWED_URL_SCHEMES:
            return ""
    return value


class MarriageBiodataController:

    @staticmethod
    def save_biodata(payload):
        try:
            user = MarriageUser.objects.get(id=payload.user_id)
        except MarriageUser.DoesNotExist:
            raise HTTPException(status_code=404, detail="MarriageUser not found")

        try:
            template = Template.objects.get(name=payload.template_id)
        except Template.DoesNotExist:
            raise HTTPException(status_code=404, detail="Template not found")

        biodata = Biodata.objects.create(
            user=user,
            template=template,
            data=payload.data
        )

        return {"message": "Saved", "id": biodata.id}

    @staticmethod
    def render_html(template_id, data):
        # save_biodata() checks this, but render_html/generate_pdf didn't —
        # meaning any .html file sitting in templates/ could be rendered, not
        # just ones registered as a real Template.
        if not Template.objects.filter(name=template_id).exists():
            raise HTTPException(status_code=404, detail="Template not found")

        try:
            template = env.get_template(f"{template_id}.html")
        except Exception:
            raise HTTPException(status_code=404, detail="Template not found")

        data = _sanitize_data(data)
        return template.render(**data)

    @staticmethod
    def generate_pdf(template_id, data):
        html = MarriageBiodataController.render_html(template_id, data)

        try:
            pdf = pdfkit.from_string(html, False, options=_PDFKIT_OPTIONS)  # False = return bytes
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"PDF generation failed: {str(e)}"
            )

        return pdf