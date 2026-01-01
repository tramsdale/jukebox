# Test Framework Documentation

## Overview

This pytest framework provides comprehensive testing for the jukebox label generator application, covering all major components and functionality.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest fixtures and configuration
├── test_jukebox_label.py      # JukeBoxLabel class unit tests
├── test_label_generator.py    # LabelGenerator class and PDF generation tests
├── test_models.py             # Database model tests
├── test_flask_app.py          # Flask web application tests
└── test_integration.py        # Integration and performance tests
```

## Test Categories

### 1. Unit Tests (`test_jukebox_label.py`)
Tests for the `JukeBoxLabel` dataclass:
- Label creation with various configurations
- Artist display logic (same/different artists)
- Backward compatibility
- Edge cases (empty values, whitespace)

### 2. Label Generation Tests (`test_label_generator.py`)
Tests for PDF generation functionality:
- LabelGenerator initialization
- PDF creation with various label sets
- Genre configuration
- File handling
- Custom dimensions

### 3. Database Model Tests (`test_models.py`)
Tests for SQLAlchemy models:
- Record creation and validation
- Database persistence
- Model relationships
- Data conversion methods
- Query operations

### 4. Flask Application Tests (`test_flask_app.py`)
Tests for the web interface:
- Route accessibility
- Authentication requirements
- Database integration
- CSV import functionality
- Error handling

### 5. Integration Tests (`test_integration.py`)
End-to-end and performance tests:
- Large batch processing
- Real-world data scenarios
- Performance benchmarks
- Memory usage
- Unicode handling

## Running Tests

### Quick Test Run
```bash
python run_tests.py
```

### All Tests
```bash
uv run pytest
```

### Specific Test Categories
```bash
# Unit tests only
uv run pytest tests/test_jukebox_label.py -v

# Database tests
uv run pytest tests/test_models.py -v

# Integration tests
uv run pytest tests/test_integration.py -v
```

### With Coverage
```bash
uv run pytest --cov=. --cov-report=html tests/
```

### Performance Tests Only
```bash
uv run pytest -m slow tests/
```

## Test Fixtures

### Core Fixtures
- `app`: Flask test application with in-memory database
- `client`: Test client for HTTP requests
- `sample_record`: Pre-configured JukeboxRecord
- `sample_labels`: Set of test JukeBoxLabels
- `temp_output_dir`: Temporary directory for test files
- `label_generator`: Pre-configured LabelGenerator instance

### Database Fixtures
- `populated_db`: Database pre-loaded with test data
- `sample_record_different_artists`: Record with different A/B side artists

### Configuration Fixtures
- `temp_config_dir`: Temporary genre configuration setup

## Key Test Features

### Artist Display Testing
Comprehensive tests for the new artist display functionality:
- Same artists: "The Beatles"
- Different artists: "John Lennon // Plastic Ono Band"
- Legacy compatibility: Falls back to main artist field
- Edge cases: Empty strings, None values

### PDF Generation Testing
- File creation and validation
- Multiple label layouts
- Custom dimensions
- Genre-based styling
- Error handling

### Database Integration Testing
- Model creation and persistence
- Data conversion methods
- Query operations
- Relationship handling

### Performance Testing
- Large batch processing (100+ labels)
- Memory usage validation
- File size validation
- Processing time limits

## Test Data

### Sample Labels
The test suite includes realistic sample data:
- The Beatles - "Hey Jude" / "Revolution" (Rock)
- John Lennon - "Imagine" / "Give Peace a Chance" (Rock, different artists)
- Miles Davis - "So What" / "Kind of Blue" (Jazz)

### Genre Configuration
Test genre configurations include:
- Rock: Red (#FF0000)
- Jazz: Blue (#0000FF)
- Classical: Purple (#800080)
- Default fallback colors

## Expected Test Results

### Core Functionality (Should Pass)
- ✅ JukeBoxLabel creation and artist display
- ✅ PDF generation with basic labels
- ✅ Database model operations
- ✅ Settings validation

### Advanced Features (May Need Adjustment)
- ⚠️ Flask route authentication (requires login system setup)
- ⚠️ Genre configuration edge cases
- ⚠️ Performance benchmarks (depend on system)

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed with `uv sync`
2. **Database Errors**: Check that Flask-SQLAlchemy is properly configured
3. **File Permission Errors**: Ensure write permissions in test directories
4. **Genre Config Errors**: Verify YAML configuration format

### Debug Mode
Run tests with extra verbosity:
```bash
uv run pytest -vv --tb=long tests/test_name.py
```

### Skip Slow Tests
```bash
uv run pytest -m "not slow"
```

## Continuous Integration

The test framework is designed to work with CI/CD pipelines:
- No external dependencies required for core tests
- Temporary files are cleaned up automatically
- Exit codes indicate success/failure
- Coverage reports can be generated

## Adding New Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Example Test Structure
```python
class TestNewFeature:
    """Test cases for new feature."""
    
    def test_basic_functionality(self, fixture_name):
        """Test basic functionality works."""
        # Arrange
        setup_data = fixture_name
        
        # Act
        result = perform_operation(setup_data)
        
        # Assert
        assert result is not None
        assert expected_condition
```

### Best Practices
- Use descriptive test names
- Test both success and failure cases
- Use appropriate fixtures
- Keep tests independent
- Test edge cases and boundaries

## Maintenance

### Regular Updates
- Update test data when features change
- Add tests for new functionality
- Remove obsolete tests
- Update documentation

### Performance Monitoring
- Monitor test execution time
- Update performance benchmarks
- Optimize slow tests
- Add new performance metrics