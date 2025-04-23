from fastapi import Depends, HTTPException, logger
from app.schemas.request import CaseDataRequest
from database.query_runner import QueryRunner
from app.schemas.schema import CaseData, CaseDataPrimaryKey, UpdateRecommendation
from app.services.case_prompt_generator import CasePromptGeneratorService
from app.schemas.request import UpdateFeedbackRequest
from database import get_query_runner, QueryRunner
from datetime import datetime, timezone
from typing import List
import asyncio
import requests

SYSTEM_CPT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJDbG91ZCBQYXRob2xvZ3kiLCJhdWQiOiJEZWYgMjAwMSIsIm5hbWUiOiJTWVNURU0gKERPIE5PVCBERUxFVEUpIiwidXNlcm5hbWUiOiJzeXN0ZW0iLCJ1c2VyVVVJRCI6IjkxMmQ3NzVmLTI5NGUtNDRlMC1hZmNkLTEwNTk0NjgyNWFhMCIsImhvbWVfY2VudGVyIjoiYzEiLCJ1c2VyUGVybWlzc2lvbnMiOnsiLyI6eyJtb2R1bGVJRCI6Ii8iLCJwZXJtaXNzaW9uIjoxNX0sIi9tYXN0ZXJzIjp7Im1vZHVsZUlEIjoiL21hc3RlcnMiLCJwZXJtaXNzaW9uIjoxNX0sInRlc3RNb2R1bGVUMiI6eyJtb2R1bGVJRCI6InRlc3RNb2R1bGVUMiIsInBlcm1pc3Npb24iOjE1fSwidGVzdHMiOnsibW9kdWxlSUQiOiJ0ZXN0cyIsInBlcm1pc3Npb24iOjE1fSwidXNlcnMiOnsibW9kdWxlSUQiOiJ1c2VycyIsInBlcm1pc3Npb24iOjE1fSwiL3NldHRpbmdzIjp7Im1vZHVsZUlEIjoiL3NldHRpbmdzIiwicGVybWlzc2lvbiI6MTV9LCIvVGVzdE1nbXQiOnsibW9kdWxlSUQiOiIvVGVzdE1nbXQiLCJwZXJtaXNzaW9uIjoxNX0sImRlcHQiOnsibW9kdWxlSUQiOiJkZXB0IiwicGVybWlzc2lvbiI6MTV9LCJkb2N0b3JzIjp7Im1vZHVsZUlEIjoiZG9jdG9ycyIsInBlcm1pc3Npb24iOjE1fSwicGFyYW1zIjp7Im1vZHVsZUlEIjoicGFyYW1zIiwicGVybWlzc2lvbiI6MTV9LCJyb2xlcyI6eyJtb2R1bGVJRCI6InJvbGVzIiwicGVybWlzc2lvbiI6MTV9LCJ0ZXN0TW9kdWxlIjp7Im1vZHVsZUlEIjoidGVzdE1vZHVsZSIsInBlcm1pc3Npb24iOjE1fSwidGVzdE1vZHVsZVNlY29uZCI6eyJtb2R1bGVJRCI6InRlc3RNb2R1bGVTZWNvbmQiLCJwZXJtaXNzaW9uIjoxNX19fQ.6e487g-Onv50tNubc4s2GtZpAy4QnrVaJIdeIVt2QFk"
class CaseDataService: 
  def __init__(self, query_runner: QueryRunner = Depends(get_query_runner)):
    self.query_runner = query_runner
    self.batch_size = 10

  async def insert_case_data(self, m: CaseData):
    try: 
      existing_data = await self._get_case_data_by_primary_key(m.get_primary_keys())
      if not existing_data:
        return await self._insert_case_data(m)
      
      return await self._update_case_data_by_primary_key(m)
    except Exception as e:
      print(f"Error processing case data for bill_id {m.bill_id}: {str(e)}")
      return {
        "success": False, 
        "test_result_id": m.test_result_id,
        "error": str(e)
      }
      
  async def _get_case_data_by_primary_key(self, key: CaseDataPrimaryKey):
    query = """
    select 
      bill_id, bill_test_id, test_id, test_result_id, age_in_hours, age_group, sex, 
      cp_instance_id, l_id, fqdn,
      parameter_id, parameter_name, parameter_printas, parameter_unit, 
      value_float, value_text,
      nrval_analysis, help_list, 
      created_at, updated_at, bill_date_quarter
    from case_data
    where sex = %s 
      and parameter_printas = %s 
      and age_group = %s 
      and bill_date_quarter = %s
      and cp_instance_id = %s 
      and test_result_id = %s
    """
    data = (key.sex, key.parameter_printas, key.age_group, key.bill_date_quarter, key.cp_instance_id, key.test_result_id)
    try: 
      return await self.query_runner.run_query_async(query, data)
    except Exception as e:
      print(f"Error fetching case_data: {str(e)}")
      raise HTTPException(status_code=500, detail=f"Error fetching case_data, ${str(e)}")

  async def _insert_case_data(self, m: CaseData):
    current_time = datetime.now(timezone.utc)
    
    query = """
      INSERT INTO case_data (
        bill_id, bill_test_id, test_id, test_result_id, age_in_hours, age_group, sex, 
        cp_instance_id, l_id, fqdn,
        parameter_id, parameter_name, parameter_printas, parameter_unit, 
        value_float, value_text,
        nrval_analysis, help_list, 
        created_at, updated_at, bill_date_quarter
      ) VALUES (
        %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s,
        %s, %s, 
        %s, %s, %s
      )
      """
    data = (
      m.bill_id, m.bill_test_id, m.test_id, m.test_result_id, m.age_in_hours, m.age_group, m.sex, 
      m.cp_instance_id, m.l_id, m.fqdn,
      m.parameter_id, m.parameter_name, m.parameter_printas, m.parameter_unit,
      m.value_float, m.value_text,
      m.nrval_analysis, m.help_list, 
      current_time, current_time, m.bill_date_quarter
    )
    
    try:
      await self.query_runner.run_query_async(query, data)
      return {"success": True, "test_result_id": m.test_result_id}
    except Exception as e:
      print(f"Error inserting case_data: {str(e)}")
      raise HTTPException(status_code=500, detail=f"Error inserting case_data, ${str(e)}")
      
  async def _update_case_data_by_primary_key(self, m: CaseData):
    current_time = datetime.now(timezone.utc)
    query = """
    update case_data
    set 
      bill_id = %s, bill_test_id = %s, test_id = %s, age_in_hours = %s,
      l_id = %s, fqdn = %s,
      parameter_id = %s, parameter_name = %s, parameter_unit = %s,
      value_float = %s, value_text = %s,
      nrval_analysis = %s, help_list = %s,
      updated_at = %s
    where sex = %s
      and parameter_printas = %s
      and age_group = %s
      and bill_date_quarter = %s
      and cp_instance_id = %s
      and test_result_id = %s
    """
    data = (
      m.bill_id, m.bill_test_id, m.test_id, m.age_in_hours, 
      m.l_id, m.fqdn,
      m.parameter_id, m.parameter_name, m.parameter_unit,
      m.value_float, m.value_text,
      m.nrval_analysis, m.help_list,
      current_time,
      m.sex, m.parameter_printas, m.age_group, m.bill_date_quarter, m.cp_instance_id, m.test_result_id,
      )
    try:
      await self.query_runner.run_query_async(query, data)
      return {"success": True, "test_result_id": m.test_result_id}
    except Exception as e:
      print(f"Error updating case_data: {str(e)}")
      raise HTTPException(status_code=500, detail=f"Error updating case_data, ${str(e)}")
    
  async def get_case_data_by_bill_id(self, bill_id: str):
    query = """
    SELECT * FROM case_data_by_bill_id WHERE bill_id = %s
    """
    data = (bill_id,)
    try:
      result = await self.query_runner.run_query_async(query, data)
      return result
    except Exception as e:
      print(f"Error fetching case_data: {str(e)}")
      raise HTTPException(status_code=500, detail=f"Error fetching case_data, ${str(e)}")

  def update_core_cp_instance_recommendation(self, tresult_object, l_id: str, fqdn: str):
    if (tresult_object is None) or (l_id is None) or (fqdn is None):
      return {"success": False, "message": "Invalid input"}
    
    # Endpoint URL
    t_result_url = f"{fqdn}/api/bills/tresult"

    # Set up headers
    headers = { 
      "Content-Type": "application/json",
      "forward": "yes",
      "l_id": l_id,
      "CPT": SYSTEM_CPT, 
    }

    # Perform the API call
    try:
        response = requests.put(t_result_url, json=tresult_object, headers=headers)
        if response.status_code == 200 and "success" in response.text:
          return {"success": True, "message": "CP Core: Successfully updated value_text"} 
        else:
          return {"success": False, "message": "CP Core: Error updating value_text"}

    except requests.exceptions.RequestException as e:
        print("Request error:", e)
        return {"success": False, "message": f"CP Core: Error updating value_text, ${str(e)}"}

  async def update_bulk_case_data_recommendation(self, queries: List[UpdateRecommendation]):
    # validate each query asynchronously
    validation_tasks = []
    for query in queries:
        validation_tasks.append(
            self._get_case_data_by_primary_key(query.get_primary_keys())
        )
    
    validation_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
    
    update_tasks = []
    test_result_list = []
    
    for idx, existed in enumerate(validation_results):
        # validate each query result
        if isinstance(existed, Exception):
            print(f"Validation failed for query {idx}: {str(existed)}")
            continue
            
        if not existed:
            print(f"Record not found for test_result_id: {queries[idx].test_result_id}")
            continue
          
        if queries[idx].value_text not in existed[0]['help_list']:
            print(f"Invalid value_text for test_result_id: {queries[idx].test_result_id}")
            continue
            
        # update each query
        update_query = """
        UPDATE case_data
        SET value_text = %s
        WHERE sex= %s 
            AND parameter_printas= %s 
            AND age_group = %s 
            AND bill_date_quarter = %s 
            AND cp_instance_id = %s 
            AND test_result_id = %s;
        """
        update_data = (queries[idx].value_text,) + queries[idx].get_primary_keys()
        
        update_tasks.append(
            self.query_runner.run_query_async(update_query, update_data)
        )
        
        test_result_list.append({
            "formatingOptions": 2,
            "value": queries[idx].value_text,
            "oValue": "",
            "test_result_id": queries[idx].test_result_id
        })
    
    # update all queries asynchronously
    if not update_tasks:
        return {"success": False, "message": "No valid updates to perform"}
        
    update_results = await asyncio.gather(*update_tasks, return_exceptions=True)
    success_count = sum(1 for result in update_results if not isinstance(result, Exception))
    
    # update CP Core and CP AI if all queries were successful
    if success_count == len(queries):
        tresult_object = {
            "test_result_list": test_result_list,
            "app": "AI"
        }
        
        tresult_response = self.update_core_cp_instance_recommendation(
            tresult_object, 
            queries[0].l_id,
            queries[0].fqdn
        )
        
        if tresult_response.get('success'):
            return {"success": True, "message": f"Successfully updated CP Core and CP AI: {success_count} / {len(queries)}"}
        return {"success": False, "message": "Error updating CP Core"}
    
    return {"success": False, "message": f"Successfully updated {success_count} / {len(queries)}"}
  
  async def update_bulk_case_data_feedback(self, queries: List[UpdateFeedbackRequest]):
    query = """
    UPDATE case_data
    SET value_text = %s
    WHERE sex= %s 
      AND parameter_printas= %s 
      AND age_group = %s 
      AND bill_date_quarter = %s 
      AND cp_instance_id = %s 
      AND test_result_id = %s;
    """
    parameters = [
      (
        query.value, 
        query.sex, 
        query.parameter_printas,
        self.group_age_in_hours(query.age_in_hours),
        self.bill_date_quarter(query.bill_date),
        query.cp_instance_id,
        query.test_result_id
      ) for query in queries
    ]
    print('parameters', parameters)
    tasks = [
      self.query_runner.run_query_async(query, params)
      for params in parameters
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
    return {"success": True, "message": "Successfully updated value_text"}

  async def process_medical_data(self, request: CaseDataRequest):
    medical_tests = self._prepare_medical_data(request)
    try: 
      results = []
      for i in range(0, len(medical_tests), self.batch_size):
        batch = medical_tests[i:i+self.batch_size]
        tasks = []
        for test in batch:
          tasks.append(self.insert_case_data(test))
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        results.extend(batch_results)

      result = await self.convert_case_data_to_result(medical_tests)
      from app.services.case_data_search import CaseDataSearchService  
      case_data_search_service = CaseDataSearchService(query_runner=self.query_runner, case_data_service=self)
      required_params = await self.extract_required_params(result)
      parameter_names = [item['parameter_name'] for item in required_params] 
      
      if result:
        bill_id = result[0]['bill_id']
        similar_cases = await CaseDataSearchService.get_similar_case_data(case_data_search_service, bill_id, parameter_names)
      else:
        similar_cases = []

      # If no similar cases were found, set it to an empty list
      if not similar_cases:
          similar_cases = []

      recommendations = await CasePromptGeneratorService.generate_llm_prompt(self,result,similar_cases) or []
      await self.update_bulk_case_data_recommendation(recommendations)
      
      return {
        "success": True,
      }
      
    except Exception as e:
      print(f"Error processing case data for bill_id {request.bill_id}: {str(e)}")
      raise HTTPException(status_code=500, detail=f"Error processing case data, ${str(e)}")
      
  def _chunk_list(self, lst: List, chunk_size: int):
    for i in range(0, len(lst), chunk_size):
      yield lst[i:i + chunk_size]
    
  def _prepare_medical_data(self, request: CaseDataRequest):
    medical_tests = []
    common_data = {
      'bill_id': request.bill_id,
      'age_in_hours' : request.age_in_hours,
      'age_group': self.group_age_in_hours(request.age_in_hours),
      'sex': request.sex,
      'cp_instance_id': request.cp_instance_id,
      'l_id': request.l_id,
      'fqdn': request.fqdn,
      'bill_date_quarter': self.bill_date_quarter(request.bill_date),
    }
    
    for test in request.tests:
      test_data = {
        **common_data,
        'test_id': test.test_id,
        'bill_test_id': test.bill_test_id,
      }
      
      for key in test.results:
        try: 
          value_float = float(key.value)
          value_text = None
        except ValueError:
          value_float = None
          value_text = key.value if key.value else None
        medical_test = CaseData(
          **test_data,
          test_result_id=key.test_result_id,
          parameter_id=key.parameter_id,
          parameter_name=key.parameter_name,
          parameter_printas=key.parameter_printas,
          parameter_unit=key.parameter_unit,
          value_float=value_float,
          value_text=value_text,
          nrval_analysis=key.nrval_analysis,
          help_list=key.help_list,
        )      
        medical_tests.append(medical_test)
    return medical_tests

  def group_age_in_hours(self, age_in_hours):
    if age_in_hours < 0:
        return "Invalid age"
    # Neonate Period (0-28 days) with detailed breakdown
    elif age_in_hours <= 24:
        return "0-24h"
    elif age_in_hours <= 168:  # 7 days
        return "1-7d"
    elif age_in_hours <= 672:  # 28 days
        return "8-28d"
    
    # Infant Period (29 days - 1 year)
    elif age_in_hours <= 2160:  # 3 months
        return "1-3m"
    elif age_in_hours <= 4320:  # 6 months
        return "3-6m"
    elif age_in_hours <= 8760:  # 12 months
        return "6-12m"
    
    # Toddler Period (1-3 years)
    elif age_in_hours <= 17520:  # 2 years
        return "1-2y"
    elif age_in_hours <= 26280:  # 3 years
        return "2-3y"
    
    # Child Period (3-12 years)
    elif age_in_hours <= 52560:  # 6 years
        return "3-6y"
    elif age_in_hours <= 78840:  # 9 years
        return "6-9y"
    elif age_in_hours <= 105120:  # 12 years
        return "9-12y"
    
    # Adolescent Period (12-18 years)
    elif age_in_hours <= 131400:  # 15 years
        return "12-15y"
    elif age_in_hours <= 157680:  # 18 years
        return "15-18y"
    
    # Young Adult Period (18-35 years)
    elif age_in_hours <= 218400:  # 25 years
        return "18-25y"
    elif age_in_hours <= 306600:  # 35 years
        return "25-35y"
      
    # Middle-Aged Adult Period (35-65 years)
    elif age_in_hours <= 438000:  # 50 years
        return "35-50y"
    elif age_in_hours <= 569400:  # 65 years
        return "50-65y"
      
    # Senior Period (65+ years)
    elif age_in_hours <= 700800:  # 80 years
        return "65-80y"
    elif age_in_hours <= 832200:  # 95 years
        return "80-95y"
    else:
        return "95y+"

  def bill_date_quarter(self, date=None):
    if date is None:
        date = datetime.now(timezone.utc)
    elif isinstance(date, str):
      try: 
        date = datetime.strptime(date, "%Y-%m-%d")
      except ValueError:
        raise ValueError("Invalid date format, should be yyyy-MM-dd")
    
    year_last_two = str(date.year)[-2:]
    
    month = date.month
    if month <= 3:
        quarter = '01'
    elif month <= 6:
        quarter = '02'
    elif month <= 9:
        quarter = '03'
    else:
        quarter = '04'
    print (f'q{year_last_two}-{quarter}') 
    return f'q{year_last_two}-{quarter}'
  
  async def convert_case_data_to_result(self,case_data_list: List[CaseData]):
    result = []
    
    for case in case_data_list:
        result.append({
            'bill_id': case.bill_id,
            'sex': case.sex,
            'parameter_printas': case.parameter_name,
            'age_group': case.age_group,
            'bill_date_quarter': case.bill_date_quarter,
            'cp_instance_id': case.cp_instance_id,
            'test_result_id': case.test_result_id,
            'age_in_hours': case.age_in_hours,
            'bill_test_id': case.bill_test_id,
            'created_at': case.created_at,
            'fqdn': case.fqdn, 
            'help_list': case.help_list,
            'l_id': case.l_id,
            'nrval_analysis': case.nrval_analysis or '',
            'parameter_id': case.parameter_id,
            'parameter_name': case.parameter_name,
            'parameter_unit': case.parameter_unit,
            'test_id': case.test_id,
            'updated_at': case.updated_at,
            'value_float': case.value_float,
            'value_text': case.value_text
        })
    
    return result
  
  async def extract_required_params(self, result: list):
    if not result:
        logger.error("Error: 'result' is empty or None.")
        return []  
    params_to_get_recommendations_for = []
    try:
        for entry in result:
            if entry.get('help_list') and entry.get('value_text') in ["EMPTY", None] and entry.get('value_float') is None:
                params_to_get_recommendations_for.append({
                    'parameter_name': entry.get('parameter_printas'),
                    'whitelisted_values': entry.get('help_list')
                })
    except (KeyError, Exception) as e:
        logger.error(f"Error while extracting parameters: {str(e)}")
        return [], []
    
    return params_to_get_recommendations_for
  
def get_case_data_service(query_runner: QueryRunner = Depends(get_query_runner)):
    return CaseDataService(query_runner)