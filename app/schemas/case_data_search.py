from pydantic import BaseModel

class CaseDataSearchField(BaseModel):
  sex: str
  parameter_printas: str
  age_group: str
  bill_date_quarter: str
  value_float: float
  cp_instance_id: str
  test_result_id: str

class CaseDataTextSearchField(BaseModel): 
  sex: str
  age_group: str
  bill_date_quarter: str 