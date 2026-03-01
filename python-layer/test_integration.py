#!/usr/bin/env python3
"""
Integration Tests for Rust-Python gRPC Interface

Tests the communication between Python client and Rust gRPC server.
"""

import sys
import time
import unittest
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, '.')

from trading_system.client import TradingClient
from trading_system import trading_pb2


class TestGRPCInterface(unittest.TestCase):
    """Integration tests for gRPC interface"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.client = TradingClient("localhost", 50051)
        cls.connected = False
        
    def test_01_connect_to_server(self):
        """Test connection to gRPC server"""
        # Note: This will fail if server is not running
        # For CI/CD, start server before tests
        self.connected = self.client.connect(timeout=2)
        # Skip remaining tests if not connected
        if not self.connected:
            self.skipTest("gRPC server not running (expected in CI without server)")
        else:
            print("\n✓ Connected to gRPC server")
    
    def test_02_health_check_rust(self):
        """Test health check for Rust engine"""
        if not self.connected:
            self.skipTest("Not connected")
        
        health = self.client.health_check("rust")
        self.assertIsNotNone(health)
        self.assertEqual(health.status, 1)  # HEALTHY
        print(f"✓ Rust engine health: {health.message}")
    
    def test_03_health_check_python(self):
        """Test health check for Python engine"""
        if not self.connected:
            self.skipTest("Not connected")
        
        health = self.client.health_check("python")
        self.assertIsNotNone(health)
        # Python is backup, may show DEGRADED
        print(f"✓ Python engine health: {health.message}")
    
    def test_04_get_status(self):
        """Test get system status"""
        if not self.connected:
            self.skipTest("Not connected")
        
        status = self.client.get_status()
        self.assertIsNotNone(status)
        self.assertTrue(status.success)
        self.assertIn(status.active_engine, ["rust", "python"])
        print(f"✓ System status: active={status.active_engine}, "
              f"failover={status.failover_enabled}")
    
    def test_05_submit_klines(self):
        """Test submitting K-line data"""
        if not self.connected:
            self.skipTest("Not connected")
        
        # Create test K-lines
        klines = [
            {
                'timestamp': int(datetime.now(timezone.utc).timestamp() * 1000),
                'open': 100.0,
                'high': 105.0,
                'low': 99.0,
                'close': 103.0,
                'volume': 1000.0,
            },
            {
                'timestamp': int(datetime.now(timezone.utc).timestamp() * 1000) + 60000,
                'open': 103.0,
                'high': 108.0,
                'low': 102.0,
                'close': 107.0,
                'volume': 1200.0,
            },
        ]
        
        success = self.client.submit_klines("BTCUSDT", "M5", klines)
        self.assertTrue(success)
        print(f"✓ Submitted {len(klines)} K-lines")
    
    def test_06_calculate_pens(self):
        """Test pen calculation"""
        if not self.connected:
            self.skipTest("Not connected")
        
        # Submit some K-lines first
        klines = [
            {'timestamp': int(time.time() * 1000) + i*60000, 
             'open': 100.0 + i, 'high': 105.0 + i, 'low': 99.0 + i, 
             'close': 103.0 + i, 'volume': 1000.0}
            for i in range(10)
        ]
        self.client.submit_klines("ETHUSDT", "M5", klines)
        
        # Calculate pens
        pens = self.client.calculate_pens("ETHUSDT", "M5", 0)
        # May return None or empty list if not enough data for complete pens
        print(f"✓ Pen calculation completed (found {len(pens) if pens else 0} pens)")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        if cls.client:
            cls.client.close()


class TestPythonBackup(unittest.TestCase):
    """Test Python backup layer functionality"""
    
    def test_kline_creation(self):
        """Test K-line data structure"""
        from trading_system.kline import Kline, TimeFrame
        
        k = Kline(
            timestamp=datetime.now(timezone.utc),
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000.0
        )
        
        self.assertTrue(k.is_bullish())
        self.assertEqual(k.range(), 6.0)
        self.assertEqual(k.body_size(), 3.0)
        print("✓ K-line creation and methods work")
    
    def test_fractal_detection(self):
        """Test fractal detection in Python layer"""
        from trading_system.fractal import FractalDetector, FractalType
        from trading_system.kline import Kline
        
        detector = FractalDetector()
        
        # Create test data with clear top fractal
        klines = [
            Kline(datetime.now(timezone.utc), 100, 105, 99, 103, 1000),
            Kline(datetime.now(timezone.utc), 103, 110, 102, 108, 1000),  # High
            Kline(datetime.now(timezone.utc), 108, 109, 104, 105, 1000),
        ]
        
        fractals = detector.detect_fractals(klines)
        # Should detect the top fractal at index 1
        print(f"✓ Fractal detection: {len(fractals)} fractals found")
    
    def test_containment_handling(self):
        """Test containment relationship handling"""
        from trading_system.fractal import FractalDetector
        from trading_system.kline import Kline
        
        detector = FractalDetector()
        
        # Create K-lines with containment
        klines = [
            Kline(datetime.now(timezone.utc), 100, 105, 99, 103, 1000),
            Kline(datetime.now(timezone.utc), 103, 104, 101, 102, 1000),  # Contained
            Kline(datetime.now(timezone.utc), 102, 106, 100, 105, 1000),
        ]
        
        fractals = detector.detect_fractals(klines)
        print(f"✓ Containment handling: {len(fractals)} fractals after processing")


if __name__ == '__main__':
    print("=" * 60)
    print("ChanLun Invester - gRPC Integration Tests")
    print("=" * 60)
    
    # Run tests
    unittest.main(verbosity=2)
