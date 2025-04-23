import json
import logging
import os
from app.llm_api.openai_client import generate_text
from app.schemas.schema import UpdateRecommendation

class CasePromptGeneratorService:
    def __init__(self, result: list):
        self.result = result
        self.all_params_list = []
        self.params_to_get_recommendations_for = []
        self.case_data = {}
        
    async def generate_llm_prompt(self, result: list, similar_cases:list):
        
        try:
           
            params_to_get_recommendations_for, all_params_list = await CasePromptGeneratorService.extract_params(self,result)
            
            case_data = await CasePromptGeneratorService.build_case_data(self,result, all_params_list)

            prompt = await CasePromptGeneratorService.generate_prompt(self,case_data, params_to_get_recommendations_for,similar_cases)
            llm_response = await generate_text(prompt)

            recommendations =  await CasePromptGeneratorService.process_llm_response(self,llm_response, result)
            if recommendations:
                recommendations_json = [recommendation.dict() for recommendation in recommendations]
                logging.info("Final Recommendations in JSON format: %s", json.dumps(recommendations_json, indent=4))
            else:
                logging.info("No recommendations found.")

        except Exception as e:
            error_type = "ValueError" if isinstance(e, ValueError) else "Unexpected error"
            logging.error("%s: %s", error_type, str(e))
            return None
    
        return recommendations

    async def extract_params(self, result: list):
        """Extract and organize parameters from result."""
        if not result:
            logging.error("Error: 'result' is empty or None.")
            return [] 
        
        params_to_get_recommendations_for = []
        all_params_list = []
        try:
            for entry in result:
                if entry.get('help_list') and entry.get('value_text') in ["EMPTY", None] and entry.get('value_float') is None:
                    params_to_get_recommendations_for.append({
                        'parameter_name': entry.get('parameter_printas'),
                        'whitelisted_values': entry.get('help_list')
                    })
                else:
                    all_params_list.append({
                        'name': entry.get('parameter_printas', ''),
                        'value': entry.get('value_float', None),
                        'reference_range': entry.get('nrval_analysis', '')
                    })
        except (KeyError, Exception) as e:
            logging.error("Error while extracting parameters: %s", str(e))
            return [], []
        
        return params_to_get_recommendations_for, all_params_list

    async def build_case_data(self, result: list, all_params_list: list):
        """Build the case data dictionary."""
        try:
            if not result or result[0] is None:
                logging.error("Error: 'result' list is empty or first item is None.")
                return None 
            
            if not all_params_list:
                logging.error("Error: 'all_params_list' is empty or None.")
                return None
            
            age_in_hours = result[0].get('age_in_hours')

            if age_in_hours is None:
                logging.error("Error: 'age_in_hours' is missing in the first item of 'result'.")
                return None
            
            case_data = {
                'age': await CasePromptGeneratorService.convert_age_to_years(self,age_in_hours),
                'sex': result[0].get('sex'),
                'parameters': all_params_list
            }
        except Exception as e:
            logging.error("Unexpected error while building case data: %s", str(e))
            return None
        
        return case_data

    async def process_llm_response(self, llm_response, result: list):
        """Process the LLM response to extract recommendations."""
        if not llm_response or not result:
            logging.error("Error: LLM response or result is empty or None.")
            return None
    
        try:
            response_text = llm_response.content
            predictions = await CasePromptGeneratorService.extract_predictions_from_response(self,response_text)
            result_dict = {item['parameter_name']: item for item in result}
            unique_recommendations = {}
            for prediction in predictions['predictions']:
                parameter_name = prediction['parameter_name']
                if parameter_name not in unique_recommendations:
                    recommendation = UpdateRecommendation(
                        value_text=prediction['prediction'],
                        sex=result_dict.get(parameter_name, {}).get('sex', ''),
                        parameter_printas=parameter_name,
                        age_group=result_dict.get(parameter_name, {}).get('age_group', ''),
                        bill_date_quarter=result_dict.get(parameter_name, {}).get('bill_date_quarter', ''),
                        cp_instance_id=result_dict.get(parameter_name, {}).get('cp_instance_id', ''),
                        test_result_id=result_dict.get(parameter_name, {}).get('test_result_id', ''),
                        l_id=result_dict.get(parameter_name, {}).get('l_id', ''),
                        fqdn=result_dict.get(parameter_name, {}).get('fqdn', '')
                    )
                    unique_recommendations[parameter_name] = recommendation
            return list(unique_recommendations.values())  
        
        except (KeyError, ValueError) as e:
            logging.error("Error extracting predictions: %s", str(e))
            return None

    async def extract_predictions_from_response(self, response_text: str):
        """Extract the prediction part of the LLM response."""
        if not response_text:
            logging.error("Error: response_text is empty or None.")
            return None
        try:
            start_index = response_text.find('```json') + len('```json')
            end_index = response_text.find('```', start_index)

            if start_index == -1 or end_index == -1:
                logging.error("Error: No valid JSON block found in the response.")
                return None
            
            json_part = response_text[start_index:end_index].strip()  

        except (json.JSONDecodeError, TypeError) as e:
            logging.error("Error decoding JSON: %s", str(e))
            return None  
        
        return json.loads(json_part)

    async def convert_age_to_years(self, age_in_hours: int) -> float:
        """Convert age from hours to years."""
        try:
            hours_in_a_year = 8760 
        
        except (TypeError, ZeroDivisionError) as e:
            logging.error("Error converting age to years: %s", str(e))
            return 0
        
        return age_in_hours / hours_in_a_year

    async def generate_prompt(self, case_data, params_to_get_recommendations_for,similar_cases):
        try:
            if not case_data:
                logging.error("Error: 'case_data' is missing or empty.")
                return None  

            if not params_to_get_recommendations_for:
                logging.warning("Warning: 'params_to_get_recommendations_for' is empty.")

            age = case_data.get('age') 
            sex = case_data.get('sex')
            analyzed_parameters = case_data.get('parameters', [])

            # Handle similar cases data
            if similar_cases and 'matching_case' in similar_cases:
                similar_cases_data = [
                    {
                        "case_id": case['bill_id'],
                        "match_percentage": case['match_percentage'],
                        "match_parameters": case['match_parameter']
                    }
                    for case in similar_cases['matching_case'].values()
                ]
            else:
                similar_cases_data = []  # No similar cases found

            if age is None or sex is None:
                logging.error("Error: Missing required 'age' or 'sex' in case_data.")
                return None
            
            prediction_requirements = [{
                "parameter_name": param.get("parameter_name"),
                "whitelisted_values": param.get("whitelisted_values")
            } for param in params_to_get_recommendations_for]

            prompt_template = os.getenv("PROMPT_TEXT")
            if not prompt_template:
                logging.error("Error: 'PROMPT_TEXT' environment variable is missing.")
                return None

            if similar_cases_data:
                prompt = prompt_template.format(
                    age=age,
                    sex=sex,
                    analyzed_parameters=json.dumps(analyzed_parameters),
                    prediction_requirements=json.dumps(prediction_requirements),
                    similar_cases_data=json.dumps(similar_cases_data)
                )
            else:
                prompt = prompt_template.format(
                    age=age,
                    sex=sex,
                    analyzed_parameters=json.dumps(analyzed_parameters),
                    prediction_requirements=json.dumps(prediction_requirements),
                    similar_cases_data="[]"
                )

        except (KeyError, ValueError, TypeError) as e:
            logging.error("Error generating prompt:", str(e))
            return None
        
        return prompt