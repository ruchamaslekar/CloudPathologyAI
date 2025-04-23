from fastapi import Depends
from app.services.case_data import CaseDataService, get_case_data_service
from database.query_runner import QueryRunner
from database import get_query_runner
from typing import List, Tuple, Dict
from app.schemas.case_data_search import CaseDataSearchField, CaseDataTextSearchField
from collections import defaultdict

class CaseDataSearchService: 
  def __init__(
    self,
    query_runner: QueryRunner,
    case_data_service: CaseDataService):
      self.query_runner = query_runner
      self.case_data_service = case_data_service    

  async def get_similar_case_data(self, bill_id, required_fields: List): 
    # get current medical report
    current_medical_case = await self.case_data_service.get_case_data_by_bill_id(bill_id)
    if not current_medical_case:
      return {"success": False, "message": "No record found"}

    # get the target case data bill_id list
    search_valid_text_value_fields = CaseDataTextSearchField(
      sex=current_medical_case[0]['sex'], 
      age_group=current_medical_case[0]['age_group'], 
      bill_date_quarter=current_medical_case[0]['bill_date_quarter'])
    valid_bill_ids = await self._execute_text_values_search(search_valid_text_value_fields, required_fields)
    if not valid_bill_ids:
      return {"success": False, "message": "No valid bill found"}
    
    # process the case data
    search_fields: List[CaseDataSearchField] = self._process_case_data(current_medical_case)

    # get the similar case data bill_id list search range like value*0.8 <  < value * 1.2
    results = await self._execute_floating_value_search(search_fields)
    matching_case = self._find_matching_case_data(bill_id, results, search_fields, valid_bill_ids)
    return {"success": True, "matching_case": matching_case}  

  def _process_case_data(self, case_data) -> List[CaseDataSearchField]:
    search_fields: List[CaseDataSearchField] = []
    for case_entry in case_data:
      if case_entry.get('value_float') is not None:
        try:
            # Automatic validation and type conversion
            search_field = CaseDataSearchField(
                sex=case_entry['sex'],
                parameter_printas=case_entry['parameter_printas'],
                age_group=case_entry['age_group'],
                bill_date_quarter=case_entry['bill_date_quarter'],
                value_float=case_entry['value_float'],
                cp_instance_id=case_entry['cp_instance_id'],
                test_result_id=case_entry['test_result_id']
            )
            search_fields.append(search_field)
        except Exception as e:
            print(f"Validation error: {e}")
    
    return search_fields

  async def _execute_text_values_search(self, query: CaseDataTextSearchField, required_fields: List):
    if not required_fields: 
      return set()

    placeholders = ', '.join(['%s'] * len(required_fields))
    
    query_str = f"""
      SELECT bill_id 
      FROM case_data_by_value_text
      WHERE sex = %s
      AND parameter_printas in ({placeholders})
      AND age_group = %s
      AND bill_date_quarter = %s
      LIMIT %s
    """
    parameters = (query.sex, *required_fields, query.age_group, query.bill_date_quarter, 1000)
    print('parameters', parameters)
    try:
      results = await self.query_runner.run_query_async(query_str, parameters)
      unique_bill_ids = list({row['bill_id'] for row in results})
      return unique_bill_ids
    except Exception as e:
      print(f"Error executing text values search: {str(e)}")
      print(f"Query: {query_str}")
      print(f"Parameters: {parameters}")
      raise e
    
  async def _execute_floating_value_search(self, search_field: List[CaseDataSearchField], range_percentage: float = 20) -> List[Tuple[str, List]]:
    search_tasks = []
    for field in search_field:
      query = """
      SELECT 
        bill_id,
        bill_test_id,
        test_result_id,
        test_id, 
        age_in_hours,
        age_group,
        sex,
        cp_instance_id,
        parameter_id,
        parameter_name,
        parameter_printas,
        parameter_unit,
        value_float,
        nrval_analysis,
        help_list
      FROM case_data_by_value_float
      WHERE sex = %s 
      AND parameter_printas = %s 
      AND age_group = %s 
      AND bill_date_quarter = %s
      AND value_float >= %s
      AND value_float <= %s
      """
      value_min = field.value_float * (1 - range_percentage/100)
      value_max = field.value_float * (1 + range_percentage/100)
      parameters = (field.sex, field.parameter_printas, field.age_group, field.bill_date_quarter, value_min, value_max)
      range_info = {
        # 'search_range': (round(value_min, 2), round(value_max, 2)),
        'search_range': str(round(value_min, 2)) + ' - ' + str(round(value_max, 2))
      }
      # Create task but don't await it yet.
      task = self.query_runner.run_query_async(query, parameters)
      search_tasks.append((field.parameter_printas, task, range_info))

    # Execute all tasks concurrently and gather results.
    queries_results = []
    for parameter_printas, task, range_info in search_tasks:
      try: 
        results = await task
        queries_results.append((parameter_printas, results, range_info))
      except Exception as e:
        print(f"Error executing query: {str(e)}")
        continue;
    return queries_results

  def _find_matching_case_data(self, current_bill_id: str, queries_results: List, search_field: List[CaseDataSearchField], valid_bill_ids: List, threshold: float = 0.8, limit: int = 3) -> Dict[str, List[str]]:
    matching_cases = defaultdict(lambda: {"matches": 0, "parameters": set(), "ranges": {}})
    found_cases = []
    
    # Track processed fields for earlier exit
    total_fields = len(search_field)
    required_matches = int(total_fields * threshold)
    processed_fields = 0 

    for parameter_printas, results, range_info in queries_results:
      processed_fields += 1
      remaining_fields = total_fields - processed_fields
      
      search_range = range_info['search_range']
      for row in results: 
        bill_id = row['bill_id']

        # Skip the current medical report
        if bill_id == current_bill_id or bill_id not in valid_bill_ids or bill_id in [case['bill_id'] for case in found_cases]:
          continue

      # Early exit: Check if it's impossible to reach threshold
      case_data = matching_cases[bill_id]
      case_data['matches'] += 1
      case_data['parameters'].add(parameter_printas)

      # Check if this case meets the threshold
      if case_data['matches'] >= required_matches: 
        match_percentage = round(case_data['matches'] / total_fields, 2)  
        found_cases.append({
          'bill_id': bill_id,
          'match_percentage': match_percentage,
          'match_parameter': list(case_data['parameters']),
          })

        if len(found_cases) >= limit:
          return {case['bill_id']: case for case in found_cases}
      elif case_data['matches'] + remaining_fields < required_matches:
        del matching_cases[bill_id]
    return {case['bill_id']: case for case in found_cases}

def get_case_data_search_service(
    query_runner: QueryRunner = Depends(get_query_runner),
    case_data_service: CaseDataService = Depends(get_case_data_service)
):
    return CaseDataSearchService(
        query_runner=query_runner,
        case_data_service=case_data_service
    )