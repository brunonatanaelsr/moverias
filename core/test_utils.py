"""
Testing utilities for Move Marias
"""
import factory
import factory.fuzzy
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import transaction
from django.core.cache import cache
import tempfile
import shutil
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()

class BaseTestCase(TestCase):
    """Base test case with common setup"""
    
    def setUp(self):
        """Common setup for all tests"""
        cache.clear()
        self.client = Client()
        
        # Create test users
        self.admin_user = UserFactory(
            email='admin@test.com',
            is_staff=True,
            is_superuser=True
        )
        self.regular_user = UserFactory(
            email='user@test.com'
        )
        
        # Create test media directory
        self.temp_media_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up after tests"""
        cache.clear()
        shutil.rmtree(self.temp_media_dir, ignore_errors=True)
    
    def assertEmailSent(self, subject_contains='', to_email=None, count=1):
        """Assert that email was sent"""
        from django.core import mail
        
        emails = mail.outbox
        self.assertEqual(len(emails), count)
        
        if subject_contains:
            self.assertIn(subject_contains, emails[0].subject)
        
        if to_email:
            self.assertIn(to_email, emails[0].to)

class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users"""
    
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f'user{n}@test.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True

class BeneficiaryFactory(factory.django.DjangoModelFactory):
    """Factory for creating test beneficiaries"""
    
    class Meta:
        model = 'members.Beneficiary'
    
    full_name = factory.Faker('name')
    dob = factory.fuzzy.FuzzyDate(
        start_date=date(1950, 1, 1),
        end_date=date(2005, 12, 31)
    )
    nis = factory.Sequence(lambda n: f'{n:011d}')
    phone_1 = factory.Faker('phone_number')
    phone_2 = factory.Maybe(
        'has_second_phone',
        yes_declaration=factory.Faker('phone_number'),
        no_declaration=None
    )
    has_second_phone = factory.Faker('boolean', chance_of_getting_true=30)
    rg = factory.Faker('random_number', digits=9)
    cpf = factory.Faker('cpf', locale='pt_BR')
    address = factory.Faker('address')
    neighbourhood = factory.Faker('city_suffix')
    reference = factory.Faker('text', max_nb_chars=100)

class ProjectEnrollmentFactory(factory.django.DjangoModelFactory):
    """Factory for creating test project enrollments"""
    
    class Meta:
        model = 'projects.ProjectEnrollment'
    
    beneficiary = factory.SubFactory(BeneficiaryFactory)
    project_name = factory.Faker('word')
    weekday = factory.fuzzy.FuzzyInteger(0, 6)
    shift = factory.fuzzy.FuzzyChoice(['MANHA', 'TARDE', 'NOITE'])
    start_time = factory.Faker('time')
    status = factory.fuzzy.FuzzyChoice(['ATIVO', 'DESLIGADO'])

class WorkshopFactory(factory.django.DjangoModelFactory):
    """Factory for creating test workshops"""
    
    class Meta:
        model = 'workshops.Workshop'
    
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text', max_nb_chars=500)
    date = factory.fuzzy.FuzzyDate(
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365)
    )
    start_time = factory.Faker('time')
    end_time = factory.LazyAttribute(
        lambda obj: (
            obj.start_time.replace(
                hour=(obj.start_time.hour + 2) % 24
            )
        )
    )
    location = factory.Faker('address')
    max_participants = factory.fuzzy.FuzzyInteger(10, 50)
    status = factory.fuzzy.FuzzyChoice(['AGENDADO', 'EM_ANDAMENTO', 'CONCLUIDO', 'CANCELADO'])

class APITestMixin:
    """Mixin for API testing"""
    
    def api_login(self, user=None):
        """Login user for API testing"""
        if user is None:
            user = self.regular_user
        self.client.force_login(user)
    
    def assertAPIResponse(self, response, status_code=200, data_keys=None):
        """Assert API response format"""
        self.assertEqual(response.status_code, status_code)
        
        if status_code == 200 and data_keys:
            response_data = response.json()
            for key in data_keys:
                self.assertIn(key, response_data)
    
    def post_json(self, url, data, **kwargs):
        """POST JSON data to API"""
        return self.client.post(
            url, 
            data, 
            content_type='application/json',
            **kwargs
        )

class PerformanceTestMixin:
    """Mixin for performance testing"""
    
    def assertQueryCount(self, num_queries):
        """Context manager to assert query count"""
        from django.test.utils import override_settings
        from django.db import connection
        
        @override_settings(DEBUG=True)
        def decorator(func):
            def wrapper():
                initial_queries = len(connection.queries)
                func()
                final_queries = len(connection.queries)
                query_count = final_queries - initial_queries
                
                if query_count != num_queries:
                    queries = connection.queries[initial_queries:final_queries]
                    query_list = '\n'.join([q['sql'] for q in queries])
                    self.fail(
                        f"Expected {num_queries} queries, got {query_count}:\n{query_list}"
                    )
            return wrapper
        return decorator
    
    def assertMaxExecutionTime(self, max_seconds):
        """Assert maximum execution time"""
        import time
        
        def decorator(func):
            def wrapper():
                start_time = time.time()
                func()
                execution_time = time.time() - start_time
                
                if execution_time > max_seconds:
                    self.fail(
                        f"Execution took {execution_time:.2f}s, "
                        f"expected max {max_seconds}s"
                    )
            return wrapper
        return decorator

class DataTestMixin:
    """Mixin for data testing utilities"""
    
    def create_test_data(self, count=10):
        """Create comprehensive test data"""
        beneficiaries = BeneficiaryFactory.create_batch(count)
        
        # Create enrollments for half of beneficiaries
        for beneficiary in beneficiaries[:count//2]:
            ProjectEnrollmentFactory.create_batch(
                factory.fuzzy.FuzzyInteger(1, 3).fuzz(),
                beneficiary=beneficiary
            )
        
        # Create workshops
        workshops = WorkshopFactory.create_batch(5)
        
        return {
            'beneficiaries': beneficiaries,
            'workshops': workshops
        }
    
    def assert_model_fields(self, instance, expected_data):
        """Assert model instance has expected field values"""
        for field, expected_value in expected_data.items():
            actual_value = getattr(instance, field)
            self.assertEqual(actual_value, expected_value)

# Custom test runner for better test management
class MoveMariasCoverageTestRunner:
    """Custom test runner with coverage reporting"""
    
    def __init__(self, **kwargs):
        self.coverage = None
        try:
            import coverage
            self.coverage = coverage.Coverage()
            self.coverage.start()
        except ImportError:
            pass
    
    def teardown_test_environment(self, **kwargs):
        if self.coverage:
            self.coverage.stop()
            self.coverage.save()
            
            # Generate coverage report
            print("\nCoverage Report:")
            self.coverage.report()

# Management command for running specific test suites
class Command:
    """Custom management command for testing"""
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--suite',
            choices=['unit', 'integration', 'performance', 'all'],
            default='all',
            help='Test suite to run'
        )
        parser.add_argument(
            '--coverage',
            action='store_true',
            help='Run with coverage reporting'
        )
    
    def handle(self, *args, **options):
        suite = options['suite']
        
        test_patterns = {
            'unit': 'tests.test_models',
            'integration': 'tests.test_views',
            'performance': 'tests.test_performance',
            'all': 'tests'
        }
        
        call_command('test', test_patterns[suite])
