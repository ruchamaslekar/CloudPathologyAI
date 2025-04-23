import os
import pytest
from unittest.mock import AsyncMock, patch
from app.services.case_prompt_generator import CasePromptGeneratorService

class TestLLMPrompt:

    def setup_method(self):
        result = [] 
        self.generator = CasePromptGeneratorService(result)

    @pytest.mark.asyncio
    async def test_convert_age_to_years(self):
        assert await self.generator.convert_age_to_years(0) == 0.0, "0 hours should return 0 years"
        assert await self.generator.convert_age_to_years(8760) == 1.0, "8760 hours should return 1 year"

    @pytest.mark.asyncio
    async def test_extract_params(self):
        result = [
            {'parameter_printas': 'Cholesterol', 'help_list': ['Normal', 'Elevated'], 'value_text': 'EMPTY', 'value_float': None, 'nrval_analysis': 'within'},
            {'parameter_printas': 'Blood Pressure', 'value_text': '120', 'value_float': 120, 'nrval_analysis': 'above'},
            {'parameter_printas': 'Glucose', 'help_list': ['Low', 'Normal', 'High'], 'value_text': None, 'value_float': None, 'nrval_analysis': 'below'}
        ]
        
        params_to_get_recommendations_for, all_params_list = await self.generator.extract_params(result)
        
        expected_params = [
            {'parameter_name': 'Cholesterol', 'whitelisted_values': ['Normal', 'Elevated']},
            {'parameter_name': 'Glucose', 'whitelisted_values': ['Low', 'Normal', 'High']}
        ]
        expected_all_params = [
            {'name': 'Blood Pressure', 'value': 120, 'reference_range': 'above'}
        ]

        assert params_to_get_recommendations_for == expected_params, "params_to_get_recommendations_for does not match expected output"
        assert all_params_list == expected_all_params, "all_params_list does not match expected output"

    @pytest.mark.asyncio
    async def test_build_case_data(self):
        result = [{'age_in_hours': 17520, 'sex': 'male'}]
        all_params_list = [{'name': 'Blood Pressure', 'value': 120, 'reference_range': 'above'}, {'name': 'Cholesterol', 'value': 200, 'reference_range': 'within'}]

        case_data = await self.generator.build_case_data(result, all_params_list)
        expected_case_data = {'age': 2.0, 'sex': 'male', 'parameters': all_params_list}

        assert case_data == expected_case_data

    @pytest.mark.asyncio
    @patch('app.services.case_prompt_generator.CasePromptGeneratorService.extract_params', new_callable=AsyncMock)
    @patch('app.services.case_prompt_generator.CasePromptGeneratorService.build_case_data', new_callable=AsyncMock)
    async def test_generate_llm_prompt_no_case_data(self, mock_build_case_data, mock_extract_params):
        mock_extract_params.return_value = (['param1'], ['param2'])
        mock_build_case_data.return_value = None
        
        result = [{'parameter_printas': 'test_param', 'help_list': ['value1'], 'value_text': 'EMPTY'}]
        recommendations = await self.generator.generate_llm_prompt(self,result)
        
        assert recommendations is None, "Recommendations should be None when case data is missing."

    @pytest.mark.asyncio
    @patch('app.services.case_prompt_generator.CasePromptGeneratorService.extract_params', new_callable=AsyncMock)
    async def test_generate_llm_prompt_empty_result(self, mock_extract_params):
        mock_extract_params.return_value = ([], [])
        
        result = []
        recommendations = await self.generator.generate_llm_prompt(self,result)
        
        assert recommendations is None, "Recommendations should be None for empty result input."

    @pytest.mark.asyncio
    async def test_process_llm_response_with_valid_data(self):
        # Mock LLM response with valid content
        llm_response = AsyncMock()
        llm_response.content = '{"predictions": [{"parameter_name": "Cholesterol", "prediction": "Elevated"}]}'

        # Mock result list
        result = [
            {
                'parameter_name': 'Cholesterol',
                'sex': 'male',
                'age_group': '30-40',
                'bill_date_quarter': 'Q1',
                'cp_instance_id': 'id_123',
                'test_result_id': 'tr_456',
                'l_id': 'l_789',
                'fqdn': 'test.fqdn.com'
            }
        ]

        # Patch `extract_predictions_from_response` to return the predictions
        with patch('app.services.case_prompt_generator.CasePromptGeneratorService.extract_predictions_from_response', return_value={"predictions": [{"parameter_name": "Cholesterol", "prediction": "Elevated"}]}):
            recommendations = await self.generator.process_llm_response(llm_response, result)

        # Expected recommendation
        assert recommendations is not None
        assert len(recommendations) == 1
        recommendation = recommendations[0]
        assert recommendation.value_text == "Elevated"
        assert recommendation.parameter_printas == "Cholesterol"

    @pytest.mark.asyncio
    async def test_process_llm_response_empty_llm_response(self):
        llm_response = None  # Simulate empty LLM response
        result = [
            {
                'parameter_name': 'Cholesterol',
                'sex': 'male',
                'age_group': '30-40'
            }
        ]

        recommendations = await self.generator.process_llm_response(llm_response, result)
        assert recommendations is None, "Expected None for empty llm_response"

    @pytest.mark.asyncio
    async def test_process_llm_response_empty_result(self):
        llm_response = AsyncMock()
        llm_response.content = '{"predictions": [{"parameter_name": "Cholesterol", "prediction": "Normal"}]}'
        result = [] 

        recommendations = await self.generator.process_llm_response(llm_response, result)
        assert recommendations is None, "Expected None for empty result"

    @pytest.mark.asyncio
    async def test_process_llm_response_key_error_handling(self):
        llm_response = AsyncMock()
        llm_response.content = '{"predictions": [{"param": "Cholesterol", "prediction": "Normal"}]}'  # Incorrect key

        result = [
            {
                'parameter_name': 'Cholesterol',
                'sex': 'male',
                'age_group': '30-40'
            }
        ]

        with patch('app.services.case_prompt_generator.CasePromptGeneratorService.extract_predictions_from_response', return_value={"predictions": [{"param": "Cholesterol", "prediction": "Normal"}]}):
            recommendations = await self.generator.process_llm_response(llm_response, result)

        assert recommendations is None, "Expected None when KeyError is encountered in predictions"

    @pytest.mark.asyncio
    async def test_generate_prompt_with_empty_similar_cases(self):
        # Mock environment variable
        with patch.dict(os.environ, {"PROMPT_TEXT": "Patient age: {age}, sex: {sex}. Parameters: {analyzed_parameters}. Requirements: {prediction_requirements}. Similar Cases: {similar_cases_data}"}):
            case_data = {
                "age": 35,
                "sex": "female",
                "parameters": [{"parameter_name": "Cholesterol", "value": 200}]
            }
            params_to_get_recommendations_for = [
                {"parameter_name": "Cholesterol", "whitelisted_values": [150, 200]}
            ]
            similar_cases = {}
            prompt = await self.generator.generate_prompt(case_data, params_to_get_recommendations_for, similar_cases)
            assert prompt is not None
            assert "Similar Cases: []" in prompt 


    @pytest.mark.asyncio
    async def test_build_case_data_missing_age(self):
        result = [{'sex': 'female'}]
        all_params_list = [{'name': 'Param1', 'value': 1}]
        case_data = await self.generator.build_case_data(result, all_params_list)
        assert case_data is None, "Should return None if age_in_hours is missing."

    @pytest.mark.asyncio
    async def test_extract_predictions_invalid_json(self):
        response_text = "Invalid JSON response"
        predictions = await self.generator.extract_predictions_from_response(response_text)
        assert predictions is None

    @patch.dict(os.environ, {"PROMPT_TEXT": "Prompt template {age}, {sex}"})
    @pytest.mark.asyncio
    async def test_generate_prompt_valid(self):
        case_data = {"age": 25, "sex": "male", "parameters": []}
        params_to_get_recommendations_for = []
        similar_cases = []
        prompt = await self.generator.generate_prompt(case_data, params_to_get_recommendations_for, similar_cases)
        assert "25" in prompt

    @pytest.mark.asyncio
    async def test_extract_predictions_from_invalid_response(self):
        llm_response = '{"invalid_json": "missing_end_bracket"'
        result = await self.generator.extract_predictions_from_response(llm_response)
        assert result is None, "Should return None for invalid JSON in response."

    @pytest.mark.asyncio
    async def test_build_case_data_with_empty_params(self):
        result = [{'age_in_hours': 17520, 'sex': 'male'}]
        all_params_list = []
        case_data = await self.generator.build_case_data(result, all_params_list)
        assert case_data is None, "Should return None for empty all_params_list."

    @pytest.mark.asyncio
    async def test_generate_prompt_missing_env_variable(self):
        os.environ.pop("PROMPT_TEXT", None)
        case_data = {'age': 30, 'sex': 'male', 'parameters': []}
        prompt = await self.generator.generate_prompt(case_data, [], [])
        assert prompt is None, "Should return None when PROMPT_TEXT is missing."

    @pytest.mark.asyncio
    async def test_generate_prompt_with_similar_cases(self):
        os.environ["PROMPT_TEXT"] = "Age: {age}, Sex: {sex}, Similar Cases: {similar_cases_data}"
        case_data = {'age': 30, 'sex': 'male', 'parameters': []}
        similar_cases = {
            'matching_case': {
                'case1': {'bill_id': '123', 'match_percentage': 95, 'match_parameter': ['param1']}
            }
        }
        prompt = await self.generator.generate_prompt(case_data, [], similar_cases)
        assert "Similar Cases" in prompt, "Prompt should include similar cases data."

    @pytest.mark.asyncio
    async def test_generate_llm_prompt_with_invalid_data(self):
        result = [{'parameter_printas': 'test_param', 'help_list': ['value1'], 'value_text': 'EMPTY'}]
        recommendations = await self.generator.generate_llm_prompt(self, result)
        assert recommendations is None, "Recommendations should be None if data is invalid"

    @pytest.mark.asyncio
    async def test_build_case_data_invalid_data(self):
        result = [{'age_in_hours': 'invalid', 'sex': 'male'}]  # invalid age data
        all_params_list = [{'name': 'Blood Pressure', 'value': 120, 'reference_range': 'above'}]
        
        case_data = await self.generator.build_case_data(result, all_params_list)
        assert case_data is None, "Case data should be None if age is invalid"
    
    @pytest.mark.asyncio
    async def test_generate_prompt_missing_age(self):
        case_data = {'sex': 'male', 'parameters': []}  # Missing age
        prompt = await self.generator.generate_prompt(case_data, [], [])
        assert prompt is None, "Prompt should be None if age is missing"

    @pytest.mark.asyncio
    async def test_generate_prompt_with_valid_data(self):
        case_data = {'age': 45, 'sex': 'female', 'parameters': [{'parameter_name': 'Blood Pressure', 'value': 120}]}
        params_to_get_recommendations_for = [{'parameter_name': 'Blood Pressure', 'whitelisted_values': [110, 120]}]
        similar_cases = {}
        prompt = await self.generator.generate_prompt(case_data, params_to_get_recommendations_for, similar_cases)
        assert prompt is not None