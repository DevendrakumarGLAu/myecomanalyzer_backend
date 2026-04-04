

from fastapi import APIRouter, Response
from api.controllers.marriage_biodata_controller import MarriageBiodataController
from api.schemas.marriage_biodata_schema import BiodataSchema


router = APIRouter()
@router.post("/save")
def save_biodata(payload: BiodataSchema):
    return MarriageBiodataController.save_biodata(payload)


@router.post("/preview-html")
def preview_html(payload: BiodataSchema):
    html = MarriageBiodataController.render_html(payload.template_id, payload.data)
    return Response(content=html, media_type="text/html")


@router.post("/preview-pdf")
def preview_pdf(payload: BiodataSchema):
    pdf = MarriageBiodataController.generate_pdf(payload.template_id, payload.data)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=preview.pdf"}
    )
    