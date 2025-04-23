from fastapi import APIRouter, Depends, Query
from auth.auth import get_api_key
from app.services.case_data import CaseDataService, get_case_data_service
from app.services.case_data_search import CaseDataSearchService, get_case_data_search_service
from app.schemas.request import CaseDataRequest, UpdateFeedbackRequest
from app.schemas.schema import UpdateRecommendation
from typing import List

router = APIRouter()

@router.post("/api/case-data")
async def post_case_data(request:CaseDataRequest, service: CaseDataService = Depends(get_case_data_service), api_key: str = Depends(get_api_key)):
    return await service.process_medical_data(request)

@router.get('/api/case-data/{bill_id}')
async def get_case_data_by_bill_id(bill_id: str, service: CaseDataService = Depends(get_case_data_service), api_key: str = Depends(get_api_key)):
    return await service.get_case_data_by_bill_id(bill_id) 
   
@router.put('/api/case-data')
async def put_case_data(request:List[UpdateFeedbackRequest], service: CaseDataService = Depends(get_case_data_service), api_key: str = Depends(get_api_key)):
    return await service.update_bulk_case_data_feedback(request)

@router.put('/api/case-data/recommendation')
async def put_recommendation(request:List[UpdateRecommendation], service: CaseDataService = Depends(get_case_data_service), api_key: str = Depends(get_api_key)):
    return await service.update_bulk_case_data_recommendation(request)

# This is temporary, it will be removed
@router.get('/api/case-data/similar/{bill_id}')
async def get_similar_case_data(bill_id: str, required_fields: List[str] = Query(alias="param", min_length=1), service_search: CaseDataSearchService = Depends(get_case_data_search_service)):
    return await service_search.get_similar_case_data(bill_id, required_fields)