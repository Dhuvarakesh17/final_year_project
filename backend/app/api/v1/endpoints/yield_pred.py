from fastapi import APIRouter
from backend.app.schemas.schemas import YieldPredictionRequest, YieldPredictionResponse
from backend.app.services.yield_prediction.yield_engine import CropYieldEngine

router = APIRouter()

@router.post("/predict", response_model=YieldPredictionResponse)
def calculate_yield(request: YieldPredictionRequest):
    data_dict = request.dict()
    res = CropYieldEngine.predict_yield(
        inputs=data_dict,
        weed_canopy_ratio_pct=request.weed_canopy_ratio_pct or 0.0,
        mean_health_score=request.mean_health_score or 100.0,
    )
    return YieldPredictionResponse(**res)

