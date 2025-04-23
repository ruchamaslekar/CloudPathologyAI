import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.case_data_search import CaseDataSearchService
from app.schemas.case_data_search import CaseDataSearchField, CaseDataTextSearchField

@pytest.fixture
def mock_query_runner():
    return Mock(run_query_async=AsyncMock())

@pytest.fixture
def mock_case_data_service():
    return Mock(get_case_data_by_bill_id=AsyncMock())

@pytest.fixture
def search_service(mock_query_runner, mock_case_data_service):
    return CaseDataSearchService(
        query_runner=mock_query_runner,
        case_data_service=mock_case_data_service
    )

@pytest.fixture
def sample_case_data():
    return [{
        'sex': 'M',
        'age_group': '20-30',
        'bill_date_quarter': '2024-Q1',
        'value_float': 10.5,
        'parameter_printas': 'TEST_PARAM',
        'cp_instance_id': '1',
        'test_result_id': '1'
    }]

@pytest.mark.asyncio
async def test_get_similar_case_data_no_record(search_service):
    """Test when no current medical case is found"""
    search_service.case_data_service.get_case_data_by_bill_id.return_value = None
    
    result = await search_service.get_similar_case_data("test_bill_id", [])
    
    assert result["success"] is False
    assert result["message"] == "No record found"

@pytest.mark.asyncio
async def test_get_similar_case_data_no_valid_bills(search_service, sample_case_data):
    """Test when no valid bills are found"""
    search_service.case_data_service.get_case_data_by_bill_id.return_value = sample_case_data
    
    # Mock text values search to return empty list
    with patch.object(search_service, '_execute_text_values_search', new_callable=AsyncMock) as mock_text_search:
        mock_text_search.return_value = []
        
        result = await search_service.get_similar_case_data("test_bill_id", ["TEST_PARAM"])
        
        assert result["success"] is False
        assert result["message"] == "No valid bill found"

@pytest.mark.asyncio
async def test_get_similar_case_data_success(search_service, sample_case_data):
    """Test successful case data retrieval"""
    search_service.case_data_service.get_case_data_by_bill_id.return_value = sample_case_data
    
    # Mock valid bill IDs
    valid_bill_ids = ['bill1', 'bill2', 'bill3']
    
    # Mock query results
    mock_query_results = [
        ('TEST_PARAM', [
            {'bill_id': 'bill1', 'value_float': 10.0},
            {'bill_id': 'bill2', 'value_float': 11.0},
            {'bill_id': 'bill3', 'value_float': 10.8}
        ], {'search_range': '8.4 - 12.6'})
    ]
    
    with patch.object(search_service, '_execute_text_values_search', new_callable=AsyncMock) as mock_text_search, \
         patch.object(search_service, '_execute_floating_value_search', new_callable=AsyncMock) as mock_float_search:
        
        mock_text_search.return_value = valid_bill_ids
        mock_float_search.return_value = mock_query_results
        
        result = await search_service.get_similar_case_data("test_bill_id", ["TEST_PARAM"])
        
        assert result["success"] is True
        assert "matching_case" in result
        assert isinstance(result["matching_case"], dict)

def test_process_case_data(search_service, sample_case_data):
    """Test case data processing"""
    result = search_service._process_case_data(sample_case_data)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], CaseDataSearchField)
    assert result[0].value_float == 10.5
    assert result[0].parameter_printas == 'TEST_PARAM'

@pytest.mark.asyncio
async def test_execute_text_values_search(search_service):
    """Test text values search execution"""
    query = CaseDataTextSearchField(
        sex='M',
        age_group='20-30',
        bill_date_quarter='2024-Q1'
    )
    required_fields = ['TEST_PARAM1', 'TEST_PARAM2']
    
    mock_results = [
        {'bill_id': 'bill1'},
        {'bill_id': 'bill2'},
        {'bill_id': 'bill2'}  # Duplicate to test unique
    ]
    search_service.query_runner.run_query_async.return_value = mock_results
    
    result = await search_service._execute_text_values_search(query, required_fields)
    
    assert isinstance(result, list)
    assert len(result) == 2  # Should be unique
    assert 'bill1' in result
    assert 'bill2' in result

@pytest.mark.asyncio
async def test_execute_floating_value_search(search_service, sample_case_data):
    """Test floating value search execution"""
    search_fields = search_service._process_case_data(sample_case_data)
    
    mock_results = [{'bill_id': 'bill1', 'value_float': 10.0}]
    search_service.query_runner.run_query_async.return_value = mock_results
    
    result = await search_service._execute_floating_value_search(search_fields)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert len(result[0]) == 3  # (parameter_printas, results, range_info)
    assert isinstance(result[0][2]['search_range'], str)

def test_find_matching_case_data(search_service):
    """Test matching case data finding logic"""
    current_bill_id = 'current_bill'
    queries_results = [
        ('TEST_PARAM1', [
            {'bill_id': 'bill1', 'value_float': 10.0},
            {'bill_id': 'bill2', 'value_float': 11.0}
        ], {'search_range': '8.4 - 12.6'})
    ]
    
    search_fields = [
        CaseDataSearchField(
            sex='M',
            parameter_printas='TEST_PARAM1',
            age_group='20-30',
            bill_date_quarter='2024-Q1',
            value_float=10.5,
            cp_instance_id='1',
            test_result_id='1'
        )
    ]
    valid_bill_ids = ['bill1', 'bill2']
    
    result = search_service._find_matching_case_data(
        current_bill_id,
        queries_results,
        search_fields,
        valid_bill_ids
    )
    
    assert isinstance(result, dict)
    assert len(result) <= 3  # Should respect default limit

@pytest.mark.asyncio
async def test_execute_text_values_search_empty_fields(search_service):
    """Test text values search with empty required fields"""
    query = CaseDataTextSearchField(
        sex='M',
        age_group='20-30',
        bill_date_quarter='2024-Q1'
    )
    
    result = await search_service._execute_text_values_search(query, [])
    assert isinstance(result, set)
    assert len(result) == 0

@pytest.mark.asyncio
async def test_execute_floating_value_search_with_error(search_service, sample_case_data):
    """Test floating value search with query error handling"""
    search_fields = search_service._process_case_data(sample_case_data)
    search_service.query_runner.run_query_async.side_effect = Exception("Database error")
    
    result = await search_service._execute_floating_value_search(search_fields)
    
    assert isinstance(result, list)
    assert len(result) == 0  # Should return empty list on error

def test_find_matching_case_data_threshold_check(search_service):
    """Test threshold checking in matching case data"""
    current_bill_id = 'current_bill'
    queries_results = [
        ('TEST_PARAM1', [{'bill_id': 'bill1', 'value_float': 10.0}], {'search_range': '8.4 - 12.6'})
    ]
    search_fields = [
        CaseDataSearchField(
            sex='M',
            parameter_printas='TEST_PARAM1',
            age_group='20-30',
            bill_date_quarter='2024-Q1',
            value_float=10.5,
            cp_instance_id='1',
            test_result_id='1'
        )
    ]
    valid_bill_ids = ['bill1']
    
    # Test with very high threshold
    result = search_service._find_matching_case_data(
        current_bill_id,
        queries_results,
        search_fields,
        valid_bill_ids,
        threshold=1.0
    )
    
    assert len(result) == 1  