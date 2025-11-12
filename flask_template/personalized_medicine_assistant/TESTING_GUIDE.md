# PMA Testing Guide
## How to Run Tests for Personalized Medical Assistant

### Prerequisites
```powershell
# Ensure you're in the project directory
cd "c:\Users\NIHITH\OneDrive\Documents\PMA - Personalized Medical Assistant\flask_template\personalized_medicine_assistant"

# Activate virtual environment (if not already active)
.\.venv\Scripts\Activate.ps1
```

---

## 1. Running All Tests

### Basic Test Run
```powershell
python manage.py test
```

### Verbose Test Run (Recommended)
```powershell
python manage.py test --verbosity=2
```

### Keep Test Database (for debugging)
```powershell
python manage.py test --keepdb --verbosity=2
```

---

## 2. Running Specific Test Suites

### Unit Tests Only

**Patients App:**
```powershell
python manage.py test patients.tests
```

**Doctors App:**
```powershell
python manage.py test doctors.tests
```

**ML Prediction App:**
```powershell
python manage.py test ml_prediction.tests
```

### API Tests
```powershell
python manage.py test tests.test_api
```

### Integration Tests
```powershell
python manage.py test tests.test_integration
```

### Performance Tests
```powershell
python manage.py test tests.test_performance
```

---

## 3. Running Specific Test Classes

### Example: Run only Patient Profile tests
```powershell
python manage.py test patients.tests.PatientProfileModelTest
```

### Example: Run only Authentication API tests
```powershell
python manage.py test tests.test_api.AuthenticationAPITest
```

---

## 4. Running Specific Test Methods

### Example: Run single test
```powershell
python manage.py test patients.tests.PatientProfileModelTest.test_bmi_calculation
```

### Example: Run multiple specific tests
```powershell
python manage.py test patients.tests.PatientProfileModelTest.test_bmi_calculation doctors.tests.DoctorProfileModelTest.test_doctor_profile_creation
```

---

## 5. Running Tests with Coverage

### Generate Coverage Report
```powershell
# Run tests with coverage tracking
python -m coverage run --source='.' manage.py test

# View coverage report in terminal
python -m coverage report

# View only files with missing coverage
python -m coverage report --skip-covered

# Generate HTML coverage report
python -m coverage html

# Open HTML report in browser
start htmlcov\index.html
```

### Coverage for Specific App
```powershell
# Run tests with coverage for patients app only
python -m coverage run --source='patients' manage.py test patients

# Generate report
python -m coverage report
```

---

## 6. Test Filtering and Pattern Matching

### Run tests matching a pattern
```powershell
# Run all tests with "API" in the name
python manage.py test --pattern="*api*"

# Run all tests with "performance" in the name
python manage.py test --pattern="*performance*"
```

### Run tests in parallel (faster)
```powershell
python manage.py test --parallel
```

---

## 7. Debugging Failed Tests

### Run with Python debugger
```powershell
python manage.py test --debug-mode patients.tests.PatientProfileModelTest
```

### Run with more verbosity
```powershell
python manage.py test --verbosity=3
```

### Show print statements in tests
```powershell
python manage.py test --verbosity=2 --debug-mode
```

---

## 8. Performance Testing

### Run only fast tests
```powershell
python manage.py test tests.test_api tests.test_integration
```

### Run performance tests with timing
```powershell
python manage.py test tests.test_performance --verbosity=2
```

---

## 9. Continuous Integration

### Complete CI/CD Test Command
```powershell
# Run all tests with coverage and generate reports
python -m coverage run --source='.' manage.py test --verbosity=2
python -m coverage report --fail-under=50
python -m coverage html
python -m coverage xml
```

---

## 10. Common Test Commands Summary

| Command | Description |
|---------|-------------|
| `python manage.py test` | Run all tests |
| `python manage.py test --verbosity=2` | Run with detailed output |
| `python manage.py test patients` | Test specific app |
| `python manage.py test --keepdb` | Keep test database |
| `python manage.py test --parallel` | Run tests in parallel |
| `python -m coverage run` | Run with coverage tracking |
| `python -m coverage report` | Show coverage report |
| `python -m coverage html` | Generate HTML report |

---

## 11. Test Structure

```
personalized_medicine_assistant/
├── patients/
│   └── tests.py              # Patient app unit tests (15 tests)
├── doctors/
│   └── tests.py              # Doctor app unit tests (21 tests)
├── ml_prediction/
│   └── tests.py              # ML prediction tests (12 tests)
└── tests/
    ├── __init__.py
    ├── test_api.py           # Backend API tests (20 tests)
    ├── test_integration.py   # Integration tests (8 tests)
    └── test_performance.py   # Performance tests (14 tests)
```

**Total: 90 comprehensive test cases**

---

## 12. Test Coverage Goals

| Component | Current Coverage | Target Coverage |
|-----------|-----------------|-----------------|
| **Models** | 93-100% | Maintain 90%+ |
| **Views** | 33-52% | Increase to 70% |
| **APIs** | 89% | Maintain 85%+ |
| **Overall** | 59% | Target 75% |

---

## 13. Troubleshooting

### Issue: Tests fail with database errors
```powershell
# Delete test database and recreate
python manage.py test --keepdb=False
```

### Issue: Import errors
```powershell
# Ensure all dependencies are installed
pip install -r requirements.txt
pip install coverage pytest pytest-django
```

### Issue: MySQL connection errors
- Verify MySQL service is running
- Check database credentials in `settings.py`
- Ensure test database permissions are set

### Issue: Slow test execution
```powershell
# Run tests in parallel
python manage.py test --parallel=4

# Run only specific test suites
python manage.py test patients doctors
```

---

## 14. Best Practices

### Writing New Tests
1. **Use descriptive test names**: `test_patient_can_book_appointment_with_available_doctor`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Keep tests isolated**: Each test should be independent
4. **Use setUp and tearDown**: For common test data
5. **Test edge cases**: Not just happy paths

### Test Data Management
- Use factories or fixtures for complex test data
- Clean up test data in tearDown methods
- Use unique identifiers to avoid conflicts

### Performance Considerations
- Keep unit tests fast (< 1 second each)
- Use mocking for external dependencies
- Run performance tests separately

---

## 15. Quick Start Example

```powershell
# Clone and setup
cd "c:\Users\NIHITH\OneDrive\Documents\PMA - Personalized Medical Assistant\flask_template\personalized_medicine_assistant"
.\.venv\Scripts\Activate.ps1

# Run all tests with coverage
python -m coverage run --source='.' manage.py test --verbosity=2

# View results
python -m coverage report --skip-covered

# Generate HTML report
python -m coverage html
start htmlcov\index.html
```

---

## 16. Resources

- **Test Report**: See `TEST_REPORT.md` for detailed results
- **HTML Coverage**: Open `htmlcov/index.html` in browser
- **Django Testing Docs**: https://docs.djangoproject.com/en/5.2/topics/testing/
- **Coverage.py Docs**: https://coverage.readthedocs.io/

---

## Contact & Support

For questions or issues with tests:
1. Check `TEST_REPORT.md` for known issues
2. Review test code comments
3. Check Django and coverage documentation

**Last Updated:** November 7, 2025  
**Test Suite Version:** 1.0  
**Python Version:** 3.13.7  
**Django Version:** 5.2.6
