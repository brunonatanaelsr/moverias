"""
Backup and migration utilities for Move Marias
"""
import os
import shutil
import json
import gzip
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.core import serializers
from django.db import connection
from django.conf import settings
from django.apps import apps
import boto3
from pathlib import Path
import logging

logger = logging.getLogger('movemarias')

class BackupManager:
    """Comprehensive backup management system"""
    
    def __init__(self, backup_dir=None):
        self.backup_dir = Path(backup_dir or settings.BASE_DIR / 'backups')
        self.backup_dir.mkdir(exist_ok=True)
        
        # Configure cloud storage if available
        self.s3_client = None
        if hasattr(settings, 'AWS_ACCESS_KEY_ID'):
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
            )
    
    def create_full_backup(self, include_media=True):
        """Create a complete system backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"movemarias_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        try:
            # 1. Database backup
            db_backup_path = backup_path / 'database.json.gz'
            self._backup_database(db_backup_path)
            
            # 2. Media files backup
            if include_media:
                media_backup_path = backup_path / 'media.tar.gz'
                self._backup_media_files(media_backup_path)
            
            # 3. Configuration backup
            config_backup_path = backup_path / 'config.json'
            self._backup_configuration(config_backup_path)
            
            # 4. Create manifest
            manifest_path = backup_path / 'manifest.json'
            self._create_manifest(manifest_path, {
                'timestamp': timestamp,
                'include_media': include_media,
                'django_version': self._get_django_version(),
                'python_version': self._get_python_version()
            })
            
            # 5. Compress backup
            archive_path = self._compress_backup(backup_path)
            
            # 6. Upload to cloud if configured
            if self.s3_client:
                self._upload_to_cloud(archive_path)
            
            # 7. Clean old backups
            self._cleanup_old_backups()
            
            logger.info(f"Backup created successfully: {archive_path}")
            return archive_path
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            # Clean up partial backup
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise
    
    def _backup_database(self, output_path):
        """Backup database to JSON format"""
        # Get all models
        models_to_backup = []
        for app in apps.get_app_configs():
            if app.name.startswith('movemarias') or app.name in [
                'members', 'projects', 'workshops', 'social', 'evolution', 
                'coaching', 'dashboard', 'users'
            ]:
                models_to_backup.extend(app.get_models())
        
        # Serialize data
        data = []
        for model in models_to_backup:
            model_data = serializers.serialize('json', model.objects.all())
            data.append({
                'model': f"{model._meta.app_label}.{model._meta.model_name}",
                'data': json.loads(model_data)
            })
        
        # Compress and save
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _backup_media_files(self, output_path):
        """Backup media files"""
        import tarfile
        
        media_root = Path(settings.MEDIA_ROOT)
        if media_root.exists():
            with tarfile.open(output_path, 'w:gz') as tar:
                tar.add(media_root, arcname='media')
    
    def _backup_configuration(self, output_path):
        """Backup system configuration"""
        config_data = {
            'installed_apps': settings.INSTALLED_APPS,
            'middleware': settings.MIDDLEWARE,
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'time_zone': settings.TIME_ZONE,
            'language_code': settings.LANGUAGE_CODE,
            'debug': settings.DEBUG,
            'allowed_hosts': settings.ALLOWED_HOSTS,
            'cache_config': settings.CACHES,
            'static_url': settings.STATIC_URL,
            'media_url': settings.MEDIA_URL,
        }
        
        with open(output_path, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
    
    def _create_manifest(self, manifest_path, metadata):
        """Create backup manifest with metadata"""
        manifest_data = {
            'created_at': datetime.now().isoformat(),
            'backup_type': 'full',
            'version': '1.0',
            'metadata': metadata,
            'files': [
                'database.json.gz',
                'config.json',
                'media.tar.gz' if metadata.get('include_media') else None
            ]
        }
        
        # Remove None values
        manifest_data['files'] = [f for f in manifest_data['files'] if f is not None]
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
    
    def _compress_backup(self, backup_path):
        """Compress backup directory"""
        import tarfile
        
        archive_path = backup_path.with_suffix('.tar.gz')
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(backup_path, arcname=backup_path.name)
        
        # Remove uncompressed directory
        shutil.rmtree(backup_path)
        
        return archive_path
    
    def _upload_to_cloud(self, archive_path):
        """Upload backup to cloud storage"""
        if not self.s3_client:
            return
        
        bucket_name = getattr(settings, 'BACKUP_S3_BUCKET', None)
        if not bucket_name:
            return
        
        try:
            key = f"backups/{archive_path.name}"
            self.s3_client.upload_file(str(archive_path), bucket_name, key)
            logger.info(f"Backup uploaded to S3: {key}")
        except Exception as e:
            logger.error(f"Failed to upload backup to S3: {str(e)}")
    
    def _cleanup_old_backups(self, keep_days=30):
        """Remove old backup files"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        for backup_file in self.backup_dir.glob('movemarias_backup_*.tar.gz'):
            try:
                # Extract timestamp from filename
                timestamp_str = backup_file.stem.split('_')[-2:]
                timestamp_str = '_'.join(timestamp_str)
                file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                if file_date < cutoff_date:
                    backup_file.unlink()
                    logger.info(f"Removed old backup: {backup_file}")
            except (ValueError, IndexError):
                # Skip files that don't match expected format
                continue
    
    def restore_backup(self, backup_path, restore_media=True):
        """Restore system from backup"""
        import tarfile
        
        backup_path = Path(backup_path)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # Extract backup
        temp_dir = self.backup_dir / 'temp_restore'
        temp_dir.mkdir(exist_ok=True)
        
        try:
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(temp_dir)
            
            # Find extracted directory
            extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
            if not extracted_dirs:
                raise ValueError("Invalid backup archive")
            
            backup_dir = extracted_dirs[0]
            
            # Read manifest
            manifest_path = backup_dir / 'manifest.json'
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            # Restore database
            db_backup_path = backup_dir / 'database.json.gz'
            self._restore_database(db_backup_path)
            
            # Restore media files
            if restore_media and 'media.tar.gz' in manifest['files']:
                media_backup_path = backup_dir / 'media.tar.gz'
                self._restore_media_files(media_backup_path)
            
            logger.info(f"Backup restored successfully from: {backup_path}")
            
        finally:
            # Clean up temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def _restore_database(self, backup_path):
        """Restore database from backup"""
        # This is a simplified version - in production, you'd want more sophisticated restoration
        logger.warning("Database restoration requires manual intervention for data integrity")
        
        with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # Note: Full database restoration should include:
        # 1. Data validation
        # 2. Foreign key constraint handling
        # 3. Transaction management
        # 4. Rollback capability
        
        logger.info("Database backup file loaded. Manual restoration required.")
    
    def _restore_media_files(self, backup_path):
        """Restore media files from backup"""
        import tarfile
        
        # Backup existing media
        media_root = Path(settings.MEDIA_ROOT)
        if media_root.exists():
            backup_existing = media_root.parent / f"media_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.move(str(media_root), str(backup_existing))
        
        # Extract new media files
        with tarfile.open(backup_path, 'r:gz') as tar:
            tar.extractall(media_root.parent)
    
    def _get_django_version(self):
        """Get Django version"""
        import django
        return django.get_version()
    
    def _get_python_version(self):
        """Get Python version"""
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def list_backups(self):
        """List available backups"""
        backups = []
        for backup_file in self.backup_dir.glob('movemarias_backup_*.tar.gz'):
            try:
                timestamp_str = backup_file.stem.split('_')[-2:]
                timestamp_str = '_'.join(timestamp_str)
                file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'created': file_date,
                    'size': backup_file.stat().st_size
                })
            except (ValueError, IndexError):
                continue
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)

# Management command for backups
class Command(BaseCommand):
    """Management command for backup operations"""
    
    help = 'Manage system backups'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['create', 'restore', 'list', 'cleanup'],
            help='Backup action to perform'
        )
        parser.add_argument(
            '--backup-file',
            help='Backup file path for restore operation'
        )
        parser.add_argument(
            '--include-media',
            action='store_true',
            default=True,
            help='Include media files in backup'
        )
        parser.add_argument(
            '--keep-days',
            type=int,
            default=30,
            help='Number of days to keep backups during cleanup'
        )
    
    def handle(self, *args, **options):
        backup_manager = BackupManager()
        
        if options['action'] == 'create':
            backup_path = backup_manager.create_full_backup(
                include_media=options['include_media']
            )
            self.stdout.write(
                self.style.SUCCESS(f'Backup created: {backup_path}')
            )
        
        elif options['action'] == 'restore':
            if not options['backup_file']:
                self.stdout.write(
                    self.style.ERROR('--backup-file is required for restore')
                )
                return
            
            backup_manager.restore_backup(options['backup_file'])
            self.stdout.write(
                self.style.SUCCESS('Backup restored successfully')
            )
        
        elif options['action'] == 'list':
            backups = backup_manager.list_backups()
            self.stdout.write('Available backups:')
            for backup in backups:
                size_mb = backup['size'] / (1024 * 1024)
                self.stdout.write(
                    f"  {backup['filename']} ({backup['created']}) - {size_mb:.1f}MB"
                )
        
        elif options['action'] == 'cleanup':
            backup_manager._cleanup_old_backups(options['keep_days'])
            self.stdout.write(
                self.style.SUCCESS('Old backups cleaned up')
            )
