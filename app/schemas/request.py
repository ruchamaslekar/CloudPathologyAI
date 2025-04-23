from pydantic import BaseModel, Field
from typing import List, Optional
class TestResultRequest(BaseModel):
    test_result_id: str = Field(..., description='Unique identifier for the test result')
    value: str = Field(None, description='Value of the parameter')
    nrval_analysis: str = Field(None, description='Analysis of the normal range value')
    parameter_id: str = Field(..., description='Unique identifier for the parameter')
    parameter_name: str = Field(None, description='Name of the parameter')
    parameter_printas: str = Field(None, description='How the parameter should be printed')
    parameter_unit: str = Field(None, description='Unit of the parameter')
    help_list: Optional[List[str]] = Field(default_factory=list, description='List of help strings')

class TestRequest(BaseModel):
    bill_test_id: str = Field(..., description='Unique identifier for the bill test')
    test_id: str = Field(None, description='Unique identifier for the test')
    results: Optional[List[TestResultRequest]] = Field(default_factory=list, description='List of test results')

class CaseDataRequest(BaseModel):
    bill_id: str = Field(..., description='Unique identifier for the bill')
    bill_date: str = Field(None, description='Date of the bill, yyyy-MM-dd')
    age_in_hours: int = Field(None, description='Age of the patient in hours')
    sex: str = Field(None, description='Sex of the patient')
    cp_instance_id: str = Field(..., description='Unique identifier for the CP Database')
    l_id: str= Field(None, description='Lab ID')
    fqdn: str= Field(None, description='Domain Name')
    tests: List[TestRequest] = Field(None, min_items=1, description='List of tests')
    
class UpdateFeedbackRequest(BaseModel):
    value: str = Field(..., description='Value of the parameter')
    sex: str = Field(..., description='Sex of the patient')
    parameter_printas: str = Field(..., description='How the parameter should be printed')
    bill_date: str = Field(..., description='Date of the bill, yyyy-MM-dd')
    age_in_hours: int = Field(..., description='Age of the patient in hours')
    cp_instance_id: str = Field(..., description='Unique identifier for the CP Database')
    test_result_id: str = Field(..., description='Unique identifier for the test result')
