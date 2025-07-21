"""
Sistema de monitoramento e ajuste dinâmico de thresholds de performance
"""
import time
import logging
import statistics
from datetime import datetime, timedelta
from django.core.cache import cache
from django.utils import timezone
from django.db import connection
from django.conf import settings
from collections import defaultdict, deque
import json
import psutil

logger = logging.getLogger(__name__)

PSUTIL_AVAILABLE = True
try:
    import psutil
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - some system metrics will be unavailable")


class PerformanceThresholdManager:
    """Gerenciador de thresholds de performance com ajuste dinâmico"""
    
    def __init__(self):
        self.thresholds_key = 'performance_thresholds'
        self.metrics_history_key = 'performance_metrics_history'
        self.adjustments_key = 'threshold_adjustments'
        self.config_key = 'threshold_config'
        
        # Configurações padrão
        self.default_config = {
            'learning_window_days': 14,
            'adjustment_sensitivity': 0.1,
            'min_samples_for_adjustment': 50,
            'max_threshold_change': 0.3,
            'adjustment_frequency_hours': 6,
            'confidence_threshold': 0.8,
            'anomaly_detection_enabled': True,
            'auto_adjustment_enabled': True,
        }
        
        # Thresholds padrão
        self.default_thresholds = {
            'response_time': {
                'warning': 500,  # ms
                'critical': 1000,  # ms
                'unit': 'ms',
                'adaptive': True
            },
            'memory_usage': {
                'warning': 70,  # %
                'critical': 85,  # %
                'unit': '%',
                'adaptive': True
            },
            'cpu_usage': {
                'warning': 70,  # %
                'critical': 85,  # %
                'unit': '%',
                'adaptive': True
            },
            'disk_usage': {
                'warning': 80,  # %
                'critical': 90,  # %
                'unit': '%',
                'adaptive': True
            },
            'db_connections': {
                'warning': 80,  # %
                'critical': 95,  # %
                'unit': '%',
                'adaptive': True
            },
            'cache_hit_rate': {
                'warning': 80,  # %
                'critical': 60,  # %
                'unit': '%',
                'adaptive': True,
                'inverted': True  # Menor é pior
            },
            'error_rate': {
                'warning': 1,  # %
                'critical': 5,  # %
                'unit': '%',
                'adaptive': True,
                'inverted': True
            },
            'queue_length': {
                'warning': 100,
                'critical': 500,
                'unit': 'items',
                'adaptive': True
            }
        }
        
        # Histórico de métricas em memória (para análise rápida)
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.last_adjustment = {}
    
    def collect_current_metrics(self):
        """Coletar métricas atuais do sistema"""
        try:
            current_time = timezone.now()
            
            metrics = {
                'timestamp': current_time.isoformat(),
                'response_time': self._get_response_time(),
                'memory_usage': self._get_memory_usage(),
                'cpu_usage': self._get_cpu_usage(),
                'disk_usage': self._get_disk_usage(),
                'db_connections': self._get_db_connections(),
                'cache_hit_rate': self._get_cache_hit_rate(),
                'error_rate': self._get_error_rate(),
                'queue_length': self._get_queue_length(),
            }
            
            # Adicionar ao buffer
            for metric_name, value in metrics.items():
                if metric_name != 'timestamp' and value is not None:
                    self.metrics_buffer[metric_name].append({
                        'timestamp': current_time,
                        'value': value
                    })
            
            # Armazenar histórico
            self._store_metrics_history(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting current metrics: {e}")
            return None
    
    def analyze_performance_patterns(self):
        """Analisar padrões de performance"""
        try:
            config = self._get_config()
            
            # Obter histórico de métricas
            historical_metrics = self._get_historical_metrics(
                config['learning_window_days']
            )
            
            if len(historical_metrics) < config['min_samples_for_adjustment']:
                return {
                    'status': 'insufficient_data',
                    'message': f'Necessário pelo menos {config["min_samples_for_adjustment"]} amostras',
                    'current_samples': len(historical_metrics)
                }
            
            analysis = {}
            
            # Analisar cada métrica
            for metric_name in self.default_thresholds.keys():
                metric_analysis = self._analyze_metric_pattern(
                    metric_name,
                    historical_metrics
                )
                analysis[metric_name] = metric_analysis
            
            # Detectar anomalias
            if config['anomaly_detection_enabled']:
                analysis['anomalies'] = self._detect_anomalies(historical_metrics)
            
            # Calcular confiança geral
            analysis['confidence'] = self._calculate_confidence(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing performance patterns: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def adjust_thresholds(self, analysis=None, force=False):
        """Ajustar thresholds baseado na análise"""
        try:
            if not analysis:
                analysis = self.analyze_performance_patterns()
            
            if analysis.get('status') == 'insufficient_data':
                return analysis
            
            config = self._get_config()
            current_thresholds = self.get_current_thresholds()
            
            adjustments = {}
            
            for metric_name, threshold_config in self.default_thresholds.items():
                if not threshold_config.get('adaptive', True):
                    continue
                
                # Verificar se é hora de ajustar
                if not force and not self._should_adjust_threshold(metric_name, config):
                    continue
                
                metric_analysis = analysis.get(metric_name, {})
                
                if metric_analysis.get('status') != 'success':
                    continue
                
                # Calcular novos thresholds
                new_thresholds = self._calculate_new_thresholds(
                    metric_name,
                    metric_analysis,
                    current_thresholds[metric_name],
                    config
                )
                
                if new_thresholds:
                    adjustments[metric_name] = {
                        'old_warning': current_thresholds[metric_name]['warning'],
                        'old_critical': current_thresholds[metric_name]['critical'],
                        'new_warning': new_thresholds['warning'],
                        'new_critical': new_thresholds['critical'],
                        'confidence': metric_analysis.get('confidence', 0),
                        'reason': metric_analysis.get('adjustment_reason', 'Pattern analysis')
                    }
            
            # Aplicar ajustes se houver confiança suficiente
            applied_adjustments = {}
            if analysis.get('confidence', 0) >= config['confidence_threshold']:
                applied_adjustments = self._apply_adjustments(adjustments)
            
            result = {
                'timestamp': timezone.now().isoformat(),
                'analysis': analysis,
                'proposed_adjustments': adjustments,
                'applied_adjustments': applied_adjustments,
                'confidence': analysis.get('confidence', 0),
                'confidence_threshold': config['confidence_threshold'],
                'auto_applied': len(applied_adjustments) > 0
            }
            
            # Armazenar histórico de ajustes
            self._store_adjustment_history(result)
            
            logger.info(f"Threshold adjustment completed. Applied {len(applied_adjustments)} adjustments")
            return result
            
        except Exception as e:
            logger.error(f"Error adjusting thresholds: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_current_thresholds(self):
        """Obter thresholds atuais"""
        stored_thresholds = cache.get(self.thresholds_key)
        
        if stored_thresholds:
            return stored_thresholds
        
        # Usar thresholds padrão
        cache.set(self.thresholds_key, self.default_thresholds, 60 * 60 * 24 * 30)
        return self.default_thresholds.copy()
    
    def set_threshold(self, metric_name, warning_value, critical_value):
        """Definir threshold manualmente"""
        current_thresholds = self.get_current_thresholds()
        
        if metric_name not in current_thresholds:
            raise ValueError(f"Unknown metric: {metric_name}")
        
        current_thresholds[metric_name]['warning'] = warning_value
        current_thresholds[metric_name]['critical'] = critical_value
        
        cache.set(self.thresholds_key, current_thresholds, 60 * 60 * 24 * 30)
        
        logger.info(f"Manual threshold set for {metric_name}: warning={warning_value}, critical={critical_value}")
        
        return current_thresholds[metric_name]
    
    def check_thresholds(self, metrics=None):
        """Verificar se métricas excedem thresholds"""
        if not metrics:
            metrics = self.collect_current_metrics()
        
        if not metrics:
            return {'status': 'error', 'message': 'Could not collect metrics'}
        
        current_thresholds = self.get_current_thresholds()
        alerts = []
        
        for metric_name, threshold_config in current_thresholds.items():
            if metric_name not in metrics:
                continue
            
            metric_value = metrics[metric_name]
            if metric_value is None:
                continue
            
            warning_threshold = threshold_config['warning']
            critical_threshold = threshold_config['critical']
            is_inverted = threshold_config.get('inverted', False)
            
            # Verificar thresholds
            if is_inverted:
                # Para métricas invertidas (cache hit rate, etc.)
                if metric_value <= critical_threshold:
                    level = 'critical'
                elif metric_value <= warning_threshold:
                    level = 'warning'
                else:
                    level = 'ok'
            else:
                # Para métricas normais
                if metric_value >= critical_threshold:
                    level = 'critical'
                elif metric_value >= warning_threshold:
                    level = 'warning'
                else:
                    level = 'ok'
            
            if level != 'ok':
                alerts.append({
                    'metric': metric_name,
                    'level': level,
                    'value': metric_value,
                    'threshold': critical_threshold if level == 'critical' else warning_threshold,
                    'unit': threshold_config.get('unit', ''),
                    'message': f"{metric_name} is {level}: {metric_value}{threshold_config.get('unit', '')}"
                })
        
        return {
            'timestamp': timezone.now().isoformat(),
            'alerts': alerts,
            'critical_count': len([a for a in alerts if a['level'] == 'critical']),
            'warning_count': len([a for a in alerts if a['level'] == 'warning']),
            'status': 'critical' if any(a['level'] == 'critical' for a in alerts) else 'warning' if alerts else 'ok'
        }
    
    def _get_response_time(self):
        """Obter tempo de resposta médio"""
        try:
            # Usar métricas do cache ou calcular
            cached_response_time = cache.get('avg_response_time')
            if cached_response_time:
                return cached_response_time
            
            # Calcular baseado em queries recentes
            if connection.queries:
                recent_queries = connection.queries[-10:]  # Últimas 10 queries
                avg_time = sum(float(q['time']) * 1000 for q in recent_queries) / len(recent_queries)
                return avg_time
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting response time: {e}")
            return None
    
    def _get_memory_usage(self):
        """Obter uso de memória"""
        try:
            if PSUTIL_AVAILABLE:
                return psutil.virtual_memory().percent
            return None
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return None
    
    def _get_cpu_usage(self):
        """Obter uso de CPU"""
        try:
            if PSUTIL_AVAILABLE:
                return psutil.cpu_percent(interval=1)
            return None
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            return None
    
    def _get_disk_usage(self):
        """Obter uso de disco"""
        try:
            if PSUTIL_AVAILABLE:
                return psutil.disk_usage('/').percent
            return None
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return None
    
    def _get_db_connections(self):
        """Obter percentual de conexões do banco"""
        try:
            # Implementar baseado no banco específico
            # Por enquanto, simular baseado em queries ativas
            active_queries = len(connection.queries)
            max_connections = getattr(settings, 'DATABASES', {}).get('default', {}).get('CONN_MAX_AGE', 100)
            
            if max_connections > 0:
                return (active_queries / max_connections) * 100
            
            return None
        except Exception as e:
            logger.error(f"Error getting DB connections: {e}")
            return None
    
    def _get_cache_hit_rate(self):
        """Obter hit rate do cache"""
        try:
            hits = cache.get('cache_hits', 0)
            misses = cache.get('cache_misses', 0)
            total = hits + misses
            
            if total > 0:
                return (hits / total) * 100
            
            return None
        except Exception as e:
            logger.error(f"Error getting cache hit rate: {e}")
            return None
    
    def _get_error_rate(self):
        """Obter taxa de erro"""
        try:
            # Implementar baseado em logs de erro
            error_count = cache.get('error_count_last_hour', 0)
            total_requests = cache.get('total_requests_last_hour', 1)
            
            return (error_count / total_requests) * 100
        except Exception as e:
            logger.error(f"Error getting error rate: {e}")
            return None
    
    def _get_queue_length(self):
        """Obter tamanho da fila"""
        try:
            # Implementar baseado no sistema de filas usado
            return cache.get('queue_length', 0)
        except Exception as e:
            logger.error(f"Error getting queue length: {e}")
            return None
    
    def _analyze_metric_pattern(self, metric_name, historical_metrics):
        """Analisar padrão de uma métrica específica"""
        try:
            # Extrair valores da métrica
            values = [m[metric_name] for m in historical_metrics if metric_name in m and m[metric_name] is not None]
            
            if len(values) < 10:
                return {'status': 'insufficient_data', 'samples': len(values)}
            
            # Estatísticas básicas
            mean = statistics.mean(values)
            median = statistics.median(values)
            stdev = statistics.stdev(values) if len(values) > 1 else 0
            
            # Percentis
            p95 = self._percentile(values, 95)
            p99 = self._percentile(values, 99)
            
            # Detectar tendência
            trend = self._calculate_trend(values)
            
            # Detectar sazonalidade
            seasonality = self._detect_seasonality(values)
            
            # Sugerir ajustes
            current_thresholds = self.get_current_thresholds()
            current_warning = current_thresholds[metric_name]['warning']
            current_critical = current_thresholds[metric_name]['critical']
            
            is_inverted = current_thresholds[metric_name].get('inverted', False)
            
            # Calcular novos thresholds baseados nos padrões
            if is_inverted:
                # Para métricas invertidas, usar percentis baixos
                suggested_critical = self._percentile(values, 10)
                suggested_warning = self._percentile(values, 25)
            else:
                # Para métricas normais, usar percentis altos
                suggested_critical = p95
                suggested_warning = self._percentile(values, 80)
            
            # Determinar se precisa ajustar
            threshold_deviation = abs(current_warning - suggested_warning) / current_warning
            needs_adjustment = threshold_deviation > 0.2  # 20% de diferença
            
            confidence = min(1.0, len(values) / 100) * (1 - min(0.5, stdev / mean if mean > 0 else 0.5))
            
            return {
                'status': 'success',
                'samples': len(values),
                'mean': mean,
                'median': median,
                'stdev': stdev,
                'p95': p95,
                'p99': p99,
                'trend': trend,
                'seasonality': seasonality,
                'current_warning': current_warning,
                'current_critical': current_critical,
                'suggested_warning': suggested_warning,
                'suggested_critical': suggested_critical,
                'needs_adjustment': needs_adjustment,
                'confidence': confidence,
                'threshold_deviation': threshold_deviation,
                'adjustment_reason': f"Pattern analysis suggests adjustment based on {len(values)} samples"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing metric pattern for {metric_name}: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _detect_anomalies(self, historical_metrics):
        """Detectar anomalias nas métricas"""
        try:
            anomalies = []
            
            for metric_name in self.default_thresholds.keys():
                values = [m[metric_name] for m in historical_metrics if metric_name in m and m[metric_name] is not None]
                
                if len(values) < 20:
                    continue
                
                # Usar Z-score para detectar outliers
                mean = statistics.mean(values)
                stdev = statistics.stdev(values)
                
                if stdev == 0:
                    continue
                
                # Encontrar valores com Z-score > 3
                outliers = []
                for i, value in enumerate(values):
                    z_score = abs(value - mean) / stdev
                    if z_score > 3:
                        outliers.append({
                            'index': i,
                            'value': value,
                            'z_score': z_score,
                            'timestamp': historical_metrics[i].get('timestamp')
                        })
                
                if outliers:
                    anomalies.append({
                        'metric': metric_name,
                        'outliers': outliers,
                        'total_outliers': len(outliers),
                        'outlier_rate': len(outliers) / len(values)
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []
    
    def _calculate_confidence(self, analysis):
        """Calcular confiança geral da análise"""
        try:
            confidences = []
            
            for metric_name, metric_analysis in analysis.items():
                if metric_name in ['anomalies', 'confidence']:
                    continue
                
                if isinstance(metric_analysis, dict) and 'confidence' in metric_analysis:
                    confidences.append(metric_analysis['confidence'])
            
            if not confidences:
                return 0
            
            # Usar média ponderada
            return sum(confidences) / len(confidences)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0
    
    def _should_adjust_threshold(self, metric_name, config):
        """Verificar se deve ajustar threshold"""
        last_adjustment_time = self.last_adjustment.get(metric_name)
        
        if not last_adjustment_time:
            return True
        
        time_since_last = timezone.now() - last_adjustment_time
        min_interval = timedelta(hours=config['adjustment_frequency_hours'])
        
        return time_since_last >= min_interval
    
    def _calculate_new_thresholds(self, metric_name, analysis, current_thresholds, config):
        """Calcular novos thresholds"""
        try:
            if not analysis.get('needs_adjustment', False):
                return None
            
            suggested_warning = analysis['suggested_warning']
            suggested_critical = analysis['suggested_critical']
            
            current_warning = current_thresholds['warning']
            current_critical = current_thresholds['critical']
            
            # Limitar mudanças drásticas
            max_change = config['max_threshold_change']
            
            warning_change = (suggested_warning - current_warning) / current_warning
            critical_change = (suggested_critical - current_critical) / current_critical
            
            # Aplicar limitação
            if abs(warning_change) > max_change:
                warning_change = max_change if warning_change > 0 else -max_change
            
            if abs(critical_change) > max_change:
                critical_change = max_change if critical_change > 0 else -max_change
            
            new_warning = current_warning * (1 + warning_change)
            new_critical = current_critical * (1 + critical_change)
            
            return {
                'warning': new_warning,
                'critical': new_critical
            }
            
        except Exception as e:
            logger.error(f"Error calculating new thresholds for {metric_name}: {e}")
            return None
    
    def _apply_adjustments(self, adjustments):
        """Aplicar ajustes aos thresholds"""
        try:
            current_thresholds = self.get_current_thresholds()
            applied = {}
            
            for metric_name, adjustment in adjustments.items():
                current_thresholds[metric_name]['warning'] = adjustment['new_warning']
                current_thresholds[metric_name]['critical'] = adjustment['new_critical']
                
                self.last_adjustment[metric_name] = timezone.now()
                
                applied[metric_name] = adjustment
            
            # Salvar thresholds atualizados
            cache.set(self.thresholds_key, current_thresholds, 60 * 60 * 24 * 30)
            
            return applied
            
        except Exception as e:
            logger.error(f"Error applying adjustments: {e}")
            return {}
    
    def _store_metrics_history(self, metrics):
        """Armazenar histórico de métricas"""
        try:
            history = cache.get(self.metrics_history_key, [])
            history.append(metrics)
            
            # Manter apenas últimos 30 dias
            cutoff_date = timezone.now() - timedelta(days=30)
            history = [
                m for m in history
                if datetime.fromisoformat(m['timestamp']) > cutoff_date
            ]
            
            cache.set(self.metrics_history_key, history, 60 * 60 * 24 * 30)
            
        except Exception as e:
            logger.error(f"Error storing metrics history: {e}")
    
    def _get_historical_metrics(self, days):
        """Obter histórico de métricas"""
        try:
            history = cache.get(self.metrics_history_key, [])
            
            cutoff_date = timezone.now() - timedelta(days=days)
            
            return [
                m for m in history
                if datetime.fromisoformat(m['timestamp']) > cutoff_date
            ]
            
        except Exception as e:
            logger.error(f"Error getting historical metrics: {e}")
            return []
    
    def _store_adjustment_history(self, adjustment_result):
        """Armazenar histórico de ajustes"""
        try:
            history = cache.get(self.adjustments_key, [])
            history.append(adjustment_result)
            
            # Manter apenas últimos 90 dias
            cutoff_date = timezone.now() - timedelta(days=90)
            history = [
                a for a in history
                if datetime.fromisoformat(a['timestamp']) > cutoff_date
            ]
            
            cache.set(self.adjustments_key, history, 60 * 60 * 24 * 90)
            
        except Exception as e:
            logger.error(f"Error storing adjustment history: {e}")
    
    def _percentile(self, values, percentile):
        """Calcular percentil"""
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * percentile / 100
        f = int(k)
        c = k - f
        
        if f == len(sorted_values) - 1:
            return sorted_values[f]
        
        return sorted_values[f] * (1 - c) + sorted_values[f + 1] * c
    
    def _calculate_trend(self, values):
        """Calcular tendência"""
        if len(values) < 2:
            return 'stable'
        
        # Regressão linear simples
        n = len(values)
        x = list(range(n))
        y = values
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 'stable'
        
        slope = numerator / denominator
        
        # Classificar tendência
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def _detect_seasonality(self, values):
        """Detectar sazonalidade simples"""
        if len(values) < 24:  # Precisa de pelo menos 24 pontos
            return 'insufficient_data'
        
        # Análise simples baseada em padrões horários
        # Implementar análise mais sofisticada se necessário
        return 'none'
    
    def _get_config(self):
        """Obter configuração atual"""
        return cache.get(self.config_key, self.default_config)
    
    def update_config(self, new_config):
        """Atualizar configuração"""
        current_config = self._get_config()
        current_config.update(new_config)
        cache.set(self.config_key, current_config, 60 * 60 * 24 * 30)
        return current_config
    
    def get_status(self):
        """Obter status do sistema de thresholds"""
        try:
            current_metrics = self.collect_current_metrics()
            threshold_check = self.check_thresholds(current_metrics)
            
            config = self._get_config()
            adjustment_history = cache.get(self.adjustments_key, [])
            
            return {
                'timestamp': timezone.now().isoformat(),
                'current_metrics': current_metrics,
                'threshold_check': threshold_check,
                'config': config,
                'auto_adjustment_enabled': config.get('auto_adjustment_enabled', True),
                'last_adjustment': max([
                    datetime.fromisoformat(a['timestamp']) for a in adjustment_history
                ]) if adjustment_history else None,
                'total_adjustments': len(adjustment_history),
                'metrics_buffer_size': {
                    metric: len(buffer) for metric, buffer in self.metrics_buffer.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting threshold manager status: {e}")
            return {'status': 'error', 'message': str(e)}


# Instância global do gerenciador
threshold_manager = PerformanceThresholdManager()
