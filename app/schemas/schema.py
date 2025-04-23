from pydantic import BaseModel
from typing import List, Optional, NamedTuple

class CaseDataPrimaryKey(NamedTuple):
    sex: str
    parameter_printas: str
    age_group: str
    bill_date_quarter: str
    cp_instance_id: str
    test_result_id: str
    
class UpdateRecommendation(BaseModel):
    value_text: str
    sex: str
    parameter_printas: str
    bill_date_quarter: str
    age_group: str
    cp_instance_id: str
    test_result_id: str
    l_id: str
    fqdn: str

    def get_primary_keys(self) -> CaseDataPrimaryKey:
        return CaseDataPrimaryKey(
            sex=self.sex,
            parameter_printas=self.parameter_printas,
            age_group=self.age_group,
            bill_date_quarter=self.bill_date_quarter,
            cp_instance_id=self.cp_instance_id,
            test_result_id=self.test_result_id
        )

class CaseData(BaseModel):
    bill_id: str 
    bill_test_id: str
    test_result_id: str
    test_id: Optional[str] = None
    age_in_hours: Optional[int] = None
    age_group: Optional[str] = None
    sex: Optional[str] = None
    cp_instance_id: Optional[str] = None
    l_id: str = None
    fqdn: str = None 
    parameter_id: Optional[str] = None
    parameter_name: Optional[str] = None
    parameter_printas: Optional[str] = None
    parameter_unit: Optional[str] = None
    value_float: Optional[float] = None
    value_text: Optional[str] = None
    nrval_analysis: Optional[str] = None
    help_list: List[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    bill_date_quarter: str = None

    def get_primary_keys(self) -> CaseDataPrimaryKey:
        return CaseDataPrimaryKey(
            sex=self.sex,
            parameter_printas=self.parameter_printas,
            age_group=self.age_group,
            bill_date_quarter=self.bill_date_quarter,
            cp_instance_id=self.cp_instance_id,
            test_result_id=self.test_result_id
        )

