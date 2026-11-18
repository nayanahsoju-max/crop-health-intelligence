"""FastAPI entrypoint for crop-health workflows and deployment health checks."""

from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.config import cors_origins_from_environment, load_project_config
from crop_health.weather.service import WeatherService
from crop_health.knowledge_base.service import KnowledgeBase
from crop_health.recommendations.engine import RecommendationEngine
from backend.app.database import create_database_engine, create_session_factory, database_url_from_environment
from backend.app.prediction_repository import PredictionRepository, prediction_to_dict
from backend.app.middleware import JsonRequestSizeLimitMiddleware
from backend.app.prediction_service import (
    ModelUnavailableError,
    PersistenceFailure,
    PredictionWorkflow,
    UploadValidationError,
    save_validated_upload,
)
from PIL import Image, ImageOps


class RecommendationRequest(BaseModel):
    class_id: str = Field(min_length=1, max_length=120)
    confidence: float
    severity: dict | str | None = None
    location: str | None = Field(default=None, max_length=120)


class PredictionRecordCreate(BaseModel):
    class_id: str = Field(min_length=1, max_length=120)
    confidence: float = Field(ge=0, le=1)
    severity: dict | None = None
    weather_context: dict | None = None
    recommendation_result: dict | None = None
    result_metadata: dict | None = None
    model_version: str | None = Field(default=None, max_length=120)
    image_reference: "ImageReference | None" = None

    @field_validator("class_id")
    @classmethod
    def validate_class_id(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("class_id must not be blank")
        return value

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value):
        if value is None:
            return value
        category = value.get("category")
        if category is not None and (not isinstance(category, str) or category not in {"Mild", "Moderate", "Severe"}):
            raise ValueError("severity category must be Mild, Moderate, or Severe")
        percentage = value.get("severity_percentage")
        if percentage is not None and not 0 <= percentage <= 100:
            raise ValueError("severity_percentage must be between 0 and 100")
        return value


class ImageReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filename: str | None = Field(default=None, max_length=255)
    media_type: str | None = Field(default=None, max_length=120)
    sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    storage_uri: str | None = Field(default=None, max_length=2048)


class PredictionSummary(BaseModel):
    class_id: str
    confidence: float
    probabilities: dict[str, float] | None = None


class PredictionResponse(BaseModel):
    status: str
    prediction_status: str
    recommendation_status: str
    prediction: PredictionSummary
    model: dict[str, str]
    severity: dict
    disease_information: dict | None
    general_guidance: list[dict]
    weather_context: dict
    weather_guidance: list[dict]
    recommendation_message: str | None
    explainability: dict
    history: dict
    crop: str | None = None


def require_db_session(request: Request):
    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        raise HTTPException(status_code=503, detail="Database is not configured")
    session = factory()
    try:
        yield session
    finally:
        session.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    load_project_config()
    app.state.weather_service = WeatherService()
    app.state.recommendation_engine = RecommendationEngine(
        knowledge_base=KnowledgeBase(), weather_service=app.state.weather_service
    )
    app.state.prediction_workflow = PredictionWorkflow(recommendation_engine=app.state.recommendation_engine)
    database_url = database_url_from_environment()
    app.state.database_engine = create_database_engine(database_url) if database_url else None
    app.state.session_factory = create_session_factory(app.state.database_engine) if app.state.database_engine else None
    try:
        yield
    finally:
        if app.state.database_engine:
            app.state.database_engine.dispose()


app = FastAPI(
    title="Crop Health Intelligence API",
    version="0.1.0",
    description=(
        "Crop-health prediction, weather context, source-traceable recommendations, "
        "and prediction-history API. Production inference requires separately supplied "
        "classifier checkpoint and class mapping artifacts."
    ),
    lifespan=lifespan,
)
app.add_middleware(JsonRequestSizeLimitMiddleware, max_bytes=1024 * 1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_from_environment(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["system"])
def readiness(request: Request) -> dict:
    """Check DB connectivity; report model asset presence without loading weights."""
    engine = getattr(request.app.state, "database_engine", None)
    database_status = "unavailable"
    if engine is not None:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            database_status = "available"
        except SQLAlchemyError:
            database_status = "unavailable"
    workflow = getattr(request.app.state, "prediction_workflow", None)
    model_status = "unavailable"
    if workflow is not None:
        try:
            workflow.ensure_model_available()
            model_status = "available"
        except ModelUnavailableError:
            pass
    if database_status != "available" or model_status != "available":
        raise HTTPException(status_code=503, detail={
            "status": "not_ready", "checks": {"database": database_status, "model": model_status},
        })
    return {"status": "ready", "checks": {"database": database_status, "model": model_status}}


@app.get("/weather/current", tags=["weather"])
def current_weather(
    request: Request,
    location: Annotated[str, Query(min_length=1, max_length=120)],
) -> dict:
    """Return current conditions or a structured unavailable result."""
    return request.app.state.weather_service.current(location)


@app.post("/recommendations/current", tags=["recommendations"])
def current_recommendation(body: RecommendationRequest, request: Request) -> dict:
    """Return source-traceable disease guidance and optional weather context."""
    return request.app.state.recommendation_engine.recommend(
        {"class_id": body.class_id, "confidence": body.confidence},
        severity=body.severity,
        location=body.location,
    )


@app.post("/predictions", tags=["history"], status_code=201)
def create_prediction_record(
    body: PredictionRecordCreate,
    session: Session = Depends(require_db_session),
) -> dict:
    try:
        record = PredictionRepository(session).create(
            predicted_class_id=body.class_id,
            confidence=body.confidence,
            severity=body.severity,
            weather_context=body.weather_context,
            recommendation_result=body.recommendation_result,
            result_metadata=body.result_metadata,
            model_version=body.model_version,
            image_reference=body.image_reference.model_dump(exclude_none=True) if body.image_reference else None,
        )
    except (ValueError, TypeError, IntegrityError) as exc:
        session.rollback()
        raise HTTPException(status_code=422, detail="Prediction record contains invalid data or violates a constraint.") from exc
    return prediction_to_dict(record)


@app.get("/predictions", tags=["history"])
def prediction_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    class_id: str | None = Query(default=None, min_length=1, max_length=120),
    session: Session = Depends(require_db_session),
) -> list[dict]:
    return [prediction_to_dict(item) for item in PredictionRepository(session).history(
        limit=limit, offset=offset, class_id=class_id)]


@app.get("/predictions/{record_id}", tags=["history"])
def prediction_detail(record_id: str, session: Session = Depends(require_db_session)) -> dict:
    record = PredictionRepository(session).get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Prediction record not found")
    return prediction_to_dict(record)


@app.post("/predict", tags=["inference"], response_model=PredictionResponse)
def predict_crop_leaf(
    request: Request,
    image: UploadFile = File(...),
    crop: str | None = Form(default=None),
    location: str | None = Form(default=None, max_length=120),
    lesion_mask: UploadFile | None = File(default=None),
) -> dict:
    """Run the configured production classifier and persist a crop-leaf result."""
    workflow: PredictionWorkflow = request.app.state.prediction_workflow
    try:
        if crop is None or not str(crop).strip():
            supported = ", ".join(sorted(workflow.crop_to_route.keys())) if hasattr(workflow, "crop_to_route") else "grape, potato, tomato"
            raise UploadValidationError(422, "invalid_crop", f"Crop is required and must be one of: {supported}.")
        with TemporaryDirectory(prefix="crop-health-upload-") as temp_dir:
            image_path = Path(temp_dir) / "upload_image"
            image_metadata = save_validated_upload(image.file, image_path, image.filename, image.content_type,
                                                   workflow.settings)
            mask_path = None
            if lesion_mask is not None:
                mask_path = Path(temp_dir) / "lesion_mask.png"
                save_validated_upload(lesion_mask.file, mask_path, lesion_mask.filename, lesion_mask.content_type,
                                      workflow.settings, role="mask")
                with Image.open(image_path) as source, Image.open(mask_path) as mask:
                    source_size = ImageOps.exif_transpose(source).size
                    mask_size = ImageOps.exif_transpose(mask).size
                if source_size != mask_size:
                    raise UploadValidationError(422, "mask_dimensions_mismatch", "The lesion mask must align with the uploaded image after EXIF orientation.")

            try:
                workflow.ensure_model_available(crop)
            except ModelUnavailableError as exc:
                raise HTTPException(status_code=503, detail={"code": "model_unavailable", "message": str(exc)}) from exc
            factory = getattr(request.app.state, "session_factory", None)
            if factory is None:
                raise HTTPException(status_code=503, detail={"code": "database_unavailable", "message": "Configure DATABASE_URL and apply database migrations before requesting predictions."})
            session = factory()
            try:
                result = workflow.run(image_path, image_metadata, session, crop=crop, location=location, mask_path=mask_path)
            except ModelUnavailableError as exc:
                raise HTTPException(status_code=503, detail={"code": "model_unavailable", "message": str(exc)}) from exc
            except PersistenceFailure as exc:
                raise HTTPException(status_code=503, detail={"code": "persistence_failed", "message": str(exc)}) from exc
            finally:
                session.close()
            return result
    except UploadValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message}) from exc
