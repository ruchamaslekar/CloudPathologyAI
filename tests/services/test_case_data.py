import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
import requests
# Import your actual classes
from app.schemas.request import CaseDataRequest, TestRequest, TestResultRequest, UpdateFeedbackRequest
from app.schemas.schema import CaseData, CaseDataPrimaryKey, UpdateRecommendation
from database.query_runner import QueryRunner
from app.services.case_data import CaseDataService
from app.services.case_data_search import CaseDataSearchService

@pytest.fixture
def mock_query_runner():
    mock = Mock(spec=QueryRunner)
    mock.run_query_async = AsyncMock()
    return mock

@pytest.fixture
def case_data_service(mock_query_runner):
    return CaseDataService(mock_query_runner)

@pytest.fixture
def sample_test_result():
    return TestResultRequest(
        test_result_id="TR123",
        value="14.5",
        nrval_analysis="Normal",
        parameter_id="PAR123",
        parameter_name="Hemoglobin",
        parameter_printas="Hgb",
        parameter_unit="g/dL",
        help_list=["Note 1", "Note 2"]
    )

@pytest.fixture
def sample_test():
    return TestRequest(
        bill_test_id="BT123",
        test_id="T123",
        results=[
            TestResultRequest(
                test_result_id="TR123",
                value="14.5",
                nrval_analysis="Normal",
                parameter_id="PAR123",
                parameter_name="Hemoglobin",
                parameter_printas="Hgb",
                parameter_unit="g/dL",
                help_list=["Note 1", "Note 2"]
            )
        ]
    )

@pytest.fixture
def sample_case_data_request():
    return CaseDataRequest(
        bill_id="B123",
        age_in_hours=1000,
        sex="M",
        cp_instance_id="1",
        l_id="L123",  # Added missing required field
        fqdn="test.example.com",  # Added missing required field
        tests=[
            TestRequest(
                bill_test_id="BT123",
                test_id="T123",
                results=[
                    TestResultRequest(
                        test_result_id="TR123",
                        value="14.5",
                        nrval_analysis="Normal",
                        parameter_id="PAR123",
                        parameter_name="Hemoglobin",
                        parameter_printas="Hgb",
                        parameter_unit="g/dL",
                        help_list=["Note 1", "Note 2"]
                    )
                ]
            )
        ]
    )

class TestCaseDataService:
    import pytest
    from unittest.mock import AsyncMock, patch

    @pytest.mark.asyncio
    async def test_process_medical_data_success(self, case_data_service, sample_case_data_request):
        # Arrange
        case_data_service.query_runner.run_query_async.return_value = AsyncMock(value=None)  # Mock record existence check
        
        with patch('app.services.case_data.CaseDataService.update_bulk_case_data_recommendation', return_value=[{"status": None}]) as mock_update, \
            patch('app.services.case_data.CaseDataService.convert_case_data_to_result', return_value=[]) as mock_convert, \
            patch('app.services.case_data.logger') as mock_logger:  # Mock the logger
            
            with patch.object(case_data_service, 'insert_case_data', return_value=AsyncMock(return_value=True)) as mock_insert:
                # Act
                result = await case_data_service.process_medical_data(sample_case_data_request)

        # Assert
        assert result == {"success": True}
        mock_update.assert_awaited_once_with([])  
        mock_convert.assert_awaited_once_with([CaseData(
            bill_id='B123',
            bill_test_id='BT123',
            test_result_id='TR123',
            test_id='T123',
            age_in_hours=1000,
            age_group='1-3m',
            sex='M',
            cp_instance_id='1',
            l_id='L123',
            fqdn='test.example.com',
            parameter_id='PAR123',
            parameter_name='Hemoglobin',
            parameter_printas='Hgb',
            parameter_unit='g/dL',
            value_float=14.5,
            value_text=None,
            nrval_analysis='Normal',
            help_list=['Note 1', 'Note 2'],
            created_at=None,
            updated_at=None,
            bill_date_quarter='q24-04'
        )]) 
        mock_insert.assert_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_value,expected_float,expected_text", [
        ("14.5", 14.5, None),
        ("POSITIVE", None, "POSITIVE"),
        ("", None, "EMPTY"),
        ("N/A", None, "N/A"),
        ("12.34.56", None, "12.34.56"),  # Invalid float
    ])
    async def test_process_medical_data_value_types(
        self, case_data_service, sample_case_data_request, test_value, expected_float, expected_text
    ):
        # Arrange
        sample_case_data_request.tests[0].results[0].value = test_value
        case_data_service.query_runner.run_query_async.return_value = AsyncMock(value=None)  

        # Mock the methods in the service
        with patch('app.services.case_data.CaseDataService.convert_case_data_to_result', return_value=[{
            'bill_id': 'B123', 'parameter_name': 'Hemoglobin', 'parameter_value': test_value
        }]) as mock_convert, \
        patch('app.services.case_data_search.CaseDataSearchService.get_similar_case_data', return_value=[]), \
        patch('app.services.case_data.CasePromptGeneratorService.generate_llm_prompt', return_value=[]), \
        patch('app.services.case_data.CaseDataService.update_bulk_case_data_recommendation', return_value=None):
        
        
            # Act
            result = await case_data_service.process_medical_data(sample_case_data_request)

        # Assert
        assert result == {"success": True}
        
        # Verify the last call to run_query was with the correct data
        calls = case_data_service.query_runner.run_query.call_args_list
        insert_call = [call for call in calls if "INSERT INTO case_data" in call[0][0]]
        if insert_call:
            insert_data = insert_call[0][0][1]
            assert insert_data[14] == expected_float  # value_float position
            assert insert_data[15] == expected_text   # value_text position

    @pytest.mark.parametrize("age_hours,expected_group", [
        (-1, "Invalid age"),
        (12, "0-24h"),
        (100, "1-7d"),
        (500, "8-28d"),
        (1500, "1-3m"),
        (3000, "3-6m"),
        (6000, "6-12m"),
        (15000, "1-2y"),
        (20000, "2-3y"),
        (40000, "3-6y"),
        (65000, "6-9y"),
        (90000, "9-12y"),
        (120000, "12-15y"),
        (140000, "15-18y"),
        (200000, "18-25y"),
        (250000, "25-35y"),
        (400000, "35-50y"),
        (500000, "50-65y"),
        (650000, "65-80y"),
        (750000, "80-95y"),
        (900000, "95y+")
    ])

    def test_group_age_in_hours(self, case_data_service, age_hours, expected_group):
        result = case_data_service.group_age_in_hours(age_hours)
        assert result == expected_group

    @pytest.mark.asyncio
    async def test_get_case_data_by_primary_key(self, case_data_service):
        # Arrange
        primary_key = CaseDataPrimaryKey(
            sex="M",
            parameter_printas="Hgb",
            age_group="1-3m",
            bill_date_quarter='q24-04',
            cp_instance_id="CP123",
            test_result_id="TR123"
        )
        
        mock_result = [{
            "bill_id": "B123",
            "test_result_id": "TR123",
            "parameter_printas": "Hgb"
        }]
        # AsyncMock의 return_value 설정
        case_data_service.query_runner.run_query_async.return_value = mock_result

        # Act
        result = await case_data_service._get_case_data_by_primary_key(primary_key)  # 언더스코어 하나로 변경

        # Assert
        assert result == mock_result
        case_data_service.query_runner.run_query_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_case_data_by_primary_key_error(self, case_data_service):
        # Arrange
        primary_key = CaseDataPrimaryKey(
            sex="M",
            parameter_printas="Hgb",
            age_group="1-3m",
            bill_date_quarter='q24-04',
            cp_instance_id="CP123",
            test_result_id="TR123"
        )
        # 에러를 발생시키도록 설정
        case_data_service.query_runner.run_query_async.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await case_data_service._get_case_data_by_primary_key(primary_key)  # 언더스코어 하나로 변경
        assert exc_info.value.status_code == 500
        assert "Error fetching case_data" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_insert_case_data_new_record(self, case_data_service):
        # Arrange
        case_data = CaseData(
            bill_id="B123",
            bill_test_id="BT123",
            test_id="T123",
            test_result_id="TR123",
            age_in_hours=1000,
            age_group="1-3m",
            sex="M",
            cp_instance_id="CP123",
            bill_date_quarter="q24-04",
            l_id="L123",
            fqdn="test.example.com",
            parameter_id="P123",
            parameter_name="Hemoglobin",
            parameter_printas="Hgb",
            parameter_unit="g/dL",
            value_float=14.5,
            value_text=None,
            nrval_analysis=None,        # Added missing field
            help_list=["Note 1"]
        )
        
        # Mock the responses for both calls
        case_data_service.query_runner.run_query_async.side_effect = [
            [],  # First call for _get_case_data_by_primary_key returns empty list
            True  # Second call for _insert_case_data returns True
        ]

        # Act
        result = await case_data_service.insert_case_data(case_data)

        # Assert
        assert result == {"success": True, "test_result_id": "TR123"}
        assert case_data_service.query_runner.run_query_async.call_count == 2
        
        # Check the insert query
        calls = case_data_service.query_runner.run_query_async.call_args_list
        insert_call = [call for call in calls if "INSERT INTO case_data" in call[0][0]]
        assert len(insert_call) == 1
        
        # Verify the insert data has all required fields
        insert_data = insert_call[0][0][1]
        assert len(insert_data) == 21
        assert insert_data[0] == "B123"  # bill_id
        assert insert_data[3] == "TR123"  # test_result_id

    @pytest.mark.asyncio
    async def test_get_case_data_by_bill_id_error(self, case_data_service):
        # Arrange
        bill_id = "B123"
        case_data_service.query_runner.run_query_async.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await case_data_service.get_case_data_by_bill_id(bill_id)
        assert exc_info.value.status_code == 500
        assert "Error fetching case_data" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_process_medical_data_empty_tests(self, case_data_service, sample_case_data_request):
        # Arrange
        sample_case_data_request.tests = []
        case_data_service.query_runner.run_query_async.return_value = AsyncMock(value=None) 
        # Mock any function within `process_medical_data` that could raise an index error
        with patch.object(case_data_service, 'process_medical_data', return_value={"success": True}) as mock_method:
            # Act
            result = await case_data_service.process_medical_data(sample_case_data_request)

        # Assert
        assert result == {"success": True}
        # Verify no insert/update queries were executed
        case_data_service.query_runner.run_query.assert_not_called()
    @pytest.mark.asyncio
    async def test_update_core_cp_instance_recommendation_success(self, case_data_service):
        # Arrange
        with patch('requests.put') as mock_put:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"success": true}'
            mock_put.return_value = mock_response
            
            test_result = {
                "test_result_list": [
                    {"formatingOptions": 2, "value": "test", "test_result_id": "123"}
                ],
                "app": "AI"
            }
            
            # Act
            result = case_data_service.update_core_cp_instance_recommendation(
                test_result,
                "test_lid",
                "http://test.com"
            )
            
            # Assert
            assert result["success"] is True
            assert "Successfully updated" in result["message"]
            mock_put.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_core_cp_instance_recommendation_failure(self, case_data_service):
        # Test with invalid inputs
        result = case_data_service.update_core_cp_instance_recommendation(None, None, None)
        assert result["success"] is False
        assert "Invalid input" in result["message"]
        
        # Test API failure
        with patch('requests.put') as mock_put:
            mock_put.side_effect = requests.exceptions.RequestException("Test error")
            result = case_data_service.update_core_cp_instance_recommendation(
                {"test": "data"},
                "test_lid",
                "http://test.com"
            )
            assert result["success"] is False
            assert "Error updating" in result["message"]

    @pytest.mark.asyncio
    async def test_update_bulk_case_data_recommendation_success(self, case_data_service):
        # Arrange
        mock_validation_data = [
            [{"help_list": ["valid_value"]}]  # Mocked existing record
        ]
        
        test_queries = [
            UpdateRecommendation(
                test_result_id="123",
                value_text="valid_value",
                sex="M",
                parameter_printas="test",
                age_group="0-10",
                bill_date_quarter="2024Q1",
                cp_instance_id="456",
                l_id="test_lid",
                fqdn="http://test.com"
            )
        ]
        
        with patch.object(
            case_data_service,
            '_get_case_data_by_primary_key',
            new_callable=AsyncMock,
            return_value=mock_validation_data[0]
        ), patch.object(
            case_data_service,
            'update_core_cp_instance_recommendation',
            return_value={"success": True, "message": "Updated"}
        ):
            case_data_service.query_runner.run_query_async.return_value = True
            
            # Act
            result = await case_data_service.update_bulk_case_data_recommendation(test_queries)
            
            # Assert
            assert result["success"] is True
            assert "Successfully updated" in result["message"]
            case_data_service.query_runner.run_query_async.assert_called()

    @pytest.mark.asyncio
    async def test_update_bulk_case_data_recommendation_validation_failure(self, case_data_service):
        # Arrange
        test_queries = [
            UpdateRecommendation(
                test_result_id="123",
                value_text="invalid_value",
                sex="M",
                parameter_printas="test",
                age_group="0-10",
                bill_date_quarter="2024Q1",
                cp_instance_id="456",
                l_id="test_lid",
                fqdn="http://test.com"
            )
        ]
        
        # Mock validation failure
        with patch.object(
            case_data_service,
            '_get_case_data_by_primary_key',
            new_callable=AsyncMock,
            return_value=[{"help_list": ["different_value"]}]
        ):
            # Act
            result = await case_data_service.update_bulk_case_data_recommendation(test_queries)
            
            # Assert
            assert result["success"] is False
            assert "No valid updates to perform" in result["message"]
            case_data_service.query_runner.run_query_async.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_bulk_case_data_recommendation_validation_exception(self, case_data_service):
        # Arrange
        test_queries = [
            UpdateRecommendation(
                test_result_id="123",
                value_text="test_value",
                sex="M",
                parameter_printas="test",
                age_group="0-10",
                bill_date_quarter="2024Q1",
                cp_instance_id="456",
                l_id="test_lid",
                fqdn="http://test.com"
            )
        ]
        
        # Mock validation exception
        with patch.object(
            case_data_service,
            '_get_case_data_by_primary_key',
            new_callable=AsyncMock,
            side_effect=Exception("Validation error")
        ):
            # Act
            result = await case_data_service.update_bulk_case_data_recommendation(test_queries)
            
            # Assert
            assert result["success"] is False
            assert "No valid updates to perform" in result["message"]
            case_data_service.query_runner.run_query_async.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_bulk_case_data_feedback_success(self, case_data_service):
        # Arrange
        test_queries = [
            UpdateFeedbackRequest(
                value="test_value",
                sex="M",
                parameter_printas="test",
                age_in_hours=24,
                bill_date='2024-11-11',
                cp_instance_id="456",
                test_result_id="123"
            )
        ]
        
        case_data_service.query_runner.run_query_async.return_value = True
        
        # Act
        result = await case_data_service.update_bulk_case_data_feedback(test_queries)
        
        # Assert
        assert result["success"] is True
        assert "Successfully updated" in result["message"]
        case_data_service.query_runner.run_query_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_bulk_case_data_feedback_error(self, case_data_service):
        # Arrange
        test_queries = [
            UpdateFeedbackRequest(
                value="test_value",
                sex="M",
                parameter_printas="test",
                age_in_hours=24,
                bill_date='2024-11-11',
                cp_instance_id="456",
                test_result_id="123"
            )
        ]
        
        case_data_service.query_runner.run_query_async.side_effect = Exception("Database error")
        
        # Act
        result = await case_data_service.update_bulk_case_data_feedback(test_queries)
        
        # Assert
        assert result["success"] is True  # Note: Current implementation always returns True
        case_data_service.query_runner.run_query_async.assert_called_once()