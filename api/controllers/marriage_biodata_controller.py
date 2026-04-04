# api/v1/controllers/marriage_biodata_controller.py
from jinja2 import Environment, FileSystemLoader
# from weasyprint import HTML
import pdfkit
from fastapi import HTTPException

from marriage_biodata.models import Biodata
from marriage_user_auth.models import MarriageUser

env = Environment(loader=FileSystemLoader("templates"))


class MarriageBiodataController:

    @staticmethod
    def save_biodata(payload):
        try:
            user = MarriageUser.objects.get(id=payload.user_id)
        except user.DoesNotExist:
            raise HTTPException(status_code=404, detail="MarriageUser not found")

        biodata = Biodata.objects.create(
            MarriageUser=MarriageUser,
            template_id=payload.template_id,
            data=payload.data
        )

        return {"message": "Saved", "id": biodata.id}

    @staticmethod
    def render_html(template_id, data):
        try:
            template = env.get_template(f"{template_id}.html")
        except Exception:
            raise HTTPException(status_code=404, detail="Template not found")
        return template.render(**data)

    @staticmethod
    def generate_pdf(template_id, data):
        html = MarriageBiodataController.render_html(template_id, data)

        try:
            pdf = pdfkit.from_string(html, False)  # False = return bytes
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"PDF generation failed: {str(e)}"
            )

        return pdf