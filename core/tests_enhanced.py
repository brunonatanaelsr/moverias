"""
Automated Testing System for Enhanced Features
"""
import unittest
import time
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from django.utils import timezone
from unittest.mock import patch, MagicMock

from core.monitoring import SystemMonitor, DatabaseMonitor, get_system_health, get_database_health
from core.background_jobs import BackgroundJob, JobScheduler, schedule_job, cleanup_cache
from core.validation import CPFValidator, CNPJValidator, PhoneValidator, CEPValidator
from core.cache_system import smart_cache, SmartCache

User = get_user_model()

class MonitoringSystemTests(TestCase):
    """Test monitoring system functionality"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            'admin', 'admin@test.com', 'admin123'
        )
        self.regular_user = User.objects.create_user(
            'user', 'user@test.com', 'user123'
        )
        
    def test_system_health_check(self):
        """Test basic system health check"""
        health_status = get_system_health()
        self.assertIn('status', health_status)
        self.assertIn('data', health_status)
        self.assertIn('timestamp', health_status)
        
    def test_database_health_check(self):
        """Test database health check"""
        db_health = get_database_health()
        self.assertIn('healthy', db_health)
        
    def test_system_monitor_initialization(self):
        """Test SystemMonitor initialization"""
        monitor = SystemMonitor()
        self.assertIsInstance(monitor.thresholds, dict)
        self.assertIn('cpu_percent', monitor.thresholds)
        self.assertIn('memory_percent', monitor.thresholds)
        self.assertIn('disk_percent', monitor.thresholds)
        
    def test_database_monitor_initialization(self):
        """Test DatabaseMonitor initialization"""
        monitor = DatabaseMonitor()
        self.assertIsInstance(monitor.query_times, list)
        self.assertIsInstance(monitor.slow_query_threshold, (int, float))
        
    def test_monitoring_views_authentication(self):
        """Test monitoring views require authentication"""
        # Test dashboard requires staff access
        response = self.client.get(reverse('monitoring_dashboard'))
        self.assertRedirects(response, '/admin/login/?next=/monitoring/dashboard/')
        
        # Test with regular user
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('monitoring_dashboard'))
        self.assertRedirects(response, '/admin/login/?next=/monitoring/dashboard/')
        
        # Test with admin user
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('monitoring_dashboard'))
        self.assertEqual(response.status_code, 200)
        
    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'OK')
        
    def test_detailed_health_check(self):
        """Test detailed health check endpoint"""
        response = self.client.get(reverse('health_detailed'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('checks', data)
        self.assertIn('timestamp', data)

class BackgroundJobsTests(TestCase):
    """Test background jobs system"""
    
    def setUp(self):
        self.job_scheduler = JobScheduler(max_workers=2)
        
    def tearDown(self):
        self.job_scheduler.stop_scheduler()
        
    def test_background_job_creation(self):
        """Test creating a background job"""
        def test_function():
            return "test_result"
        
        job = BackgroundJob('test_job', test_function)
        self.assertEqual(job.job_id, 'test_job')
        self.assertEqual(job.func, test_function)
        self.assertEqual(job.status, 'pending')
        
    def test_job_scheduling(self):
        """Test job scheduling"""
        def test_function():
            return "test_result"
        
        job = schedule_job('test_job', test_function, priority=1)
        self.assertEqual(job.job_id, 'test_job')
        self.assertEqual(job.priority, 1)
        
    def test_job_execution(self):
        """Test job execution"""
        def test_function():
            return "test_result"
        
        job = schedule_job('test_job', test_function)
        self.job_scheduler.start_scheduler()
        
        # Wait for job to complete
        max_wait = 10
        while job.status == 'pending' and max_wait > 0:
            time.sleep(0.1)
            max_wait -= 1
        
        self.assertIn(job.status, ['completed', 'running'])
        
    def test_job_failure_handling(self):
        """Test job failure handling"""
        def failing_function():
            raise Exception("Test error")
        
        job = schedule_job('failing_job', failing_function)
        self.job_scheduler.start_scheduler()
        
        # Wait for job to fail
        max_wait = 10
        while job.status == 'pending' and max_wait > 0:
            time.sleep(0.1)
            max_wait -= 1
        
        self.assertEqual(job.status, 'failed')
        self.assertIsNotNone(job.error)
        
    def test_cleanup_cache_job(self):
        """Test cleanup cache job"""
        # Set some cache data
        cache.set('test_key', 'test_value')
        self.assertEqual(cache.get('test_key'), 'test_value')
        
        # Run cleanup job
        result = cleanup_cache()
        self.assertTrue(result['success'])
        
    def test_job_statistics(self):
        """Test job statistics"""
        def test_function():
            return "test_result"
        
        # Create multiple jobs
        for i in range(5):
            schedule_job(f'test_job_{i}', test_function)
        
        stats = self.job_scheduler.get_job_statistics()
        self.assertIn('total_jobs', stats)
        self.assertIn('status_counts', stats)
        self.assertIn('queue_size', stats)
        self.assertEqual(stats['total_jobs'], 5)

class ValidationSystemTests(TestCase):
    """Test validation system"""
    
    def test_cpf_validator(self):
        """Test CPF validation"""
        validator = CPFValidator()
        
        # Valid CPF (using a real valid CPF calculation)
        valid_cpf = "11144477735"  # This is a valid CPF number
        self.assertTrue(validator.validate(valid_cpf))
        
        # Invalid CPF
        invalid_cpf = "12345678900"
        self.assertFalse(validator.validate(invalid_cpf))
        
        # Invalid format
        invalid_format = "123.456.789-01"
        self.assertFalse(validator.validate(invalid_format))
        
    def test_cnpj_validator(self):
        """Test CNPJ validation"""
        validator = CNPJValidator()
        
        # Valid CNPJ (using a real valid CNPJ calculation)
        valid_cnpj = "11222333000181"  # This is a valid CNPJ number
        self.assertTrue(validator.validate(valid_cnpj))
        
        # Invalid CNPJ
        invalid_cnpj = "12345678000100"
        self.assertFalse(validator.validate(invalid_cnpj))
        
    def test_phone_validator(self):
        """Test phone validation"""
        validator = PhoneValidator()
        
        # Valid phones
        valid_phones = [
            "11999999999",
            "(11) 99999-9999",
            "+55 11 99999-9999"
        ]
        
        for phone in valid_phones:
            self.assertTrue(validator.validate(phone))
            
        # Invalid phones
        invalid_phones = [
            "123456789",
            "abc123456789",
            "11 9999-9999"  # Missing digit
        ]
        
        for phone in invalid_phones:
            self.assertFalse(validator.validate(phone))
            
    def test_cep_validator(self):
        """Test CEP validation"""
        validator = CEPValidator()
        
        # Valid CEPs
        valid_ceps = [
            "01234567",
            "01234-567"
        ]
        
        for cep in valid_ceps:
            self.assertTrue(validator.validate(cep))
            
        # Invalid CEPs
        invalid_ceps = [
            "0123456",
            "012345678",
            "abcdefgh"
        ]
        
        for cep in invalid_ceps:
            self.assertFalse(validator.validate(cep))

class CacheSystemTests(TestCase):
    """Test cache system functionality"""
    
    def setUp(self):
        self.cache_service = SmartCache()
        
    def test_cache_service_initialization(self):
        """Test cache service initialization"""
        self.assertIsInstance(self.cache_service.prefix, str)
        self.assertIsInstance(self.cache_service.default_timeout, int)
        
    def test_smart_cache_decorator(self):
        """Test smart cache decorator"""
        @smart_cache(timeout=60)
        def test_function(x):
            return x * 2
        
        # First call should cache the result
        result1 = test_function(5)
        self.assertEqual(result1, 10)
        
        # Second call should return cached result
        result2 = test_function(5)
        self.assertEqual(result2, 10)
        
    def test_cache_invalidation(self):
        """Test cache invalidation"""
        # Set cache data
        self.cache_service.set('test_key', 'test_value')
        self.assertEqual(self.cache_service.get('test_key')['value'], 'test_value')
        
        # Invalidate cache
        self.cache_service.delete('test_key')
        self.assertIsNone(self.cache_service.get('test_key'))
        
    def test_cache_warming(self):
        """Test cache warming"""
        def warm_function():
            return "warmed_data"
        
        # Warm cache
        result = self.cache_service.get_or_set('warm_key', warm_function, timeout=60)
        self.assertEqual(result, "warmed_data")
        
        # Check if data was cached
        cached_result = self.cache_service.get('warm_key')
        self.assertEqual(cached_result['value'], "warmed_data")

class IntegrationTests(TestCase):
    """Integration tests for all systems"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            'admin', 'admin@test.com', 'admin123'
        )
        
    def test_monitoring_dashboard_integration(self):
        """Test monitoring dashboard integration"""
        self.client.force_login(self.admin_user)
        
        # Test dashboard loads
        response = self.client.get(reverse('monitoring_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Test API endpoints
        response = self.client.get(reverse('api_system_health'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('system', data)
        self.assertIn('database', data)
        
    def test_background_jobs_integration(self):
        """Test background jobs integration with monitoring"""
        self.client.force_login(self.admin_user)
        
        # Schedule a test job
        def test_job():
            return "integration_test"
        
        job = schedule_job('integration_test', test_job)
        
        # Check job status via API
        response = self.client.get(reverse('api_background_jobs'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('stats', data)
        self.assertIn('recent_jobs', data)
        
    def test_validation_integration(self):
        """Test validation system integration"""
        # Test CPF validation in forms
        cpf_validator = CPFValidator()
        valid_cpf = "12345678901"
        self.assertTrue(cpf_validator.validate(valid_cpf))
        
        # Test cache integration
        cache_service = SmartCache()
        cache_service.set('validation_test', 'cached_value')
        self.assertEqual(cache_service.get('validation_test')['value'], 'cached_value')
        
    def test_system_health_integration(self):
        """Test system health integration"""
        # Test system health
        health_status = get_system_health()
        self.assertIn('status', health_status)
        
        # Test database health
        db_health = get_database_health()
        self.assertIn('healthy', db_health)
        
        # Test monitoring widget
        response = self.client.get(reverse('monitoring_widget'))
        self.assertEqual(response.status_code, 200)

class PerformanceTests(TestCase):
    """Performance tests for new systems"""
    
    def test_monitoring_performance(self):
        """Test monitoring system performance"""
        start_time = time.time()
        
        # Run multiple health checks
        for _ in range(10):
            get_system_health()
            get_database_health()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(execution_time, 5.0)
        
    def test_cache_performance(self):
        """Test cache system performance"""
        cache_service = SmartCache()
        
        start_time = time.time()
        
        # Set multiple cache entries
        for i in range(100):
            cache_service.set(f'test_key_{i}', f'test_value_{i}')
        
        # Get multiple cache entries
        for i in range(100):
            cache_service.get(f'test_key_{i}')
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(execution_time, 2.0)
        
    def test_validation_performance(self):
        """Test validation system performance"""
        cpf_validator = CPFValidator()
        
        start_time = time.time()
        
        # Validate multiple CPFs
        for i in range(1000):
            cpf_validator.validate(f"{i:011d}")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(execution_time, 1.0)

# Test runner utility
def run_all_tests():
    """Run all tests and return results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        MonitoringSystemTests,
        BackgroundJobsTests,
        ValidationSystemTests,
        CacheSystemTests,
        IntegrationTests,
        PerformanceTests
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return {
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success': result.wasSuccessful()
    }

if __name__ == '__main__':
    run_all_tests()
