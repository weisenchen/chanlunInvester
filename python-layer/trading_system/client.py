"""
gRPC Client - Python to Rust Communication
"""

import grpc
from typing import Optional, List
from . import trading_pb2
from . import trading_pb2_grpc


class TradingClient:
    """gRPC client for trading service"""
    
    def __init__(self, host: str = "localhost", port: int = 50051):
        self.host = host
        self.port = port
        self.channel = None
        self.stub = None
    
    def connect(self, timeout: int = 5):
        """Connect to the gRPC server"""
        target = f"{self.host}:{self.port}"
        self.channel = grpc.insecure_channel(target)
        self.stub = trading_pb2_grpc.TradingServiceStub(self.channel)
        
        # Test connection
        try:
            grpc.channel_ready_future(self.channel).result(timeout=timeout)
            print(f"✓ Connected to {target}")
            return True
        except grpc.FutureTimeoutError:
            print(f"✗ Connection timeout to {target}")
            return False
    
    def close(self):
        """Close the connection"""
        if self.channel:
            self.channel.close()
    
    def health_check(self, service: str = "rust") -> Optional[trading_pb2.HealthCheckResponse]:
        """Check service health"""
        try:
            request = trading_pb2.HealthCheckRequest(service=service)
            response = self.stub.HealthCheck(request)
            return response
        except grpc.RpcError as e:
            print(f"Health check failed: {e}")
            return None
    
    def get_status(self) -> Optional[trading_pb2.GetStatusResponse]:
        """Get system status"""
        try:
            request = trading_pb2.GetStatusRequest()
            response = self.stub.GetStatus(request)
            return response
        except grpc.RpcError as e:
            print(f"Get status failed: {e}")
            return None
    
    def submit_klines(self, symbol: str, timeframe: str, klines: List[dict]) -> bool:
        """Submit K-line data"""
        try:
            # Convert timeframe string to enum
            tf_enum = getattr(trading_pb2, f"TimeFrame_{timeframe.upper()}", 
                             trading_pb2.TimeFrame_TIMEFRAME_UNSPECIFIED)
            
            # Convert klines to protobuf
            pb_klines = [
                trading_pb2.Kline(
                    timestamp=int(k.get('timestamp', 0)),
                    open=k.get('open', 0.0),
                    high=k.get('high', 0.0),
                    low=k.get('low', 0.0),
                    close=k.get('close', 0.0),
                    volume=k.get('volume', 0.0),
                    turnover=k.get('turnover')
                )
                for k in klines
            ]
            
            request = trading_pb2.SubmitKlinesRequest(
                symbol=symbol,
                timeframe=tf_enum,
                klines=pb_klines
            )
            
            response = self.stub.SubmitKlines(request)
            return response.success
        except grpc.RpcError as e:
            print(f"Submit klines failed: {e}")
            return False
    
    def calculate_pens(self, symbol: str, timeframe: str, last_n: int = 0) -> Optional[List[trading_pb2.Pen]]:
        """Calculate pens for a symbol"""
        try:
            tf_enum = getattr(trading_pb2, f"TimeFrame_{timeframe.upper()}",
                             trading_pb2.TimeFrame_TIMEFRAME_UNSPECIFIED)
            
            request = trading_pb2.CalculatePensRequest(
                symbol=symbol,
                timeframe=tf_enum,
                last_n=last_n
            )
            
            response = self.stub.CalculatePens(request)
            if response.success:
                return list(response.pens)
            return None
        except grpc.RpcError as e:
            print(f"Calculate pens failed: {e}")
            return None


def test_connection():
    """Test gRPC connection"""
    client = TradingClient()
    
    if client.connect():
        # Test health check
        health = client.health_check("rust")
        if health:
            print(f"Health status: {health.status} ({health.message})")
        
        # Test get status
        status = client.get_status()
        if status:
            print(f"System status: active_engine={status.active_engine}, "
                  f"failover={status.failover_enabled}")
        
        client.close()
        return True
    return False


if __name__ == "__main__":
    print("Testing gRPC client...")
    test_connection()
