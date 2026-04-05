"""
HTTPS/TLS Configuration for X-IDS API
Enables secure communication with certificate management

Usage:
    from api_server import create_app
    app = create_app()
    app.run(ssl_context='adhoc')  # For development
    # OR
    app.run(ssl_context=('cert.pem', 'key.pem'))  # Production with certificates
"""

import os
import ssl
import logging
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Certificate paths
CERT_DIR = os.getenv('CERT_DIR', './certs')
CERT_FILE = os.path.join(CERT_DIR, 'server.crt')
KEY_FILE = os.path.join(CERT_DIR, 'server.key')
CA_FILE = os.path.join(CERT_DIR, 'ca.crt')


class TLSManager:
    """Manage TLS/SSL certificates and configurations"""
    
    @staticmethod
    def create_self_signed_cert(days: int = 365) -> bool:
        """
        Create self-signed certificate (for development only)
        
        Args:
            days: Certificate validity period
            
        Returns:
            True if successful
        """
        try:
            import subprocess
            
            os.makedirs(CERT_DIR, exist_ok=True)
            
            # Generate private key
            subprocess.run([
                'openssl', 'genrsa',
                '-out', KEY_FILE, '2048'
            ], check=True, capture_output=True)
            
            # Generate self-signed certificate
            subprocess.run([
                'openssl', 'req',
                '-new', '-x509',
                '-key', KEY_FILE,
                '-out', CERT_FILE,
                '-days', str(days),
                '-subj', '/C=US/ST=State/L=City/O=Organization/CN=localhost'
            ], check=True, capture_output=True)
            
            logger.info(f"Self-signed certificate created: {CERT_FILE}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create certificate: {e}")
            return False
    
    @staticmethod
    def get_ssl_context(verify_client: bool = False) -> Optional[ssl.SSLContext]:
        """
        Get configured SSL context
        
        Args:
            verify_client: Require client certificate verification
            
        Returns:
            Configured SSLContext or None if certificates not available
        """
        try:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            
            # Load server certificate and key
            if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
                logger.warning("Certificate files not found, creating self-signed...")
                if not TLSManager.create_self_signed_cert():
                    return None
            
            context.load_cert_chain(CERT_FILE, KEY_FILE)
            
            # Configure SSL options
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.maximum_version = ssl.TLSVersion.TLSv1_3
            
            # Disable weak ciphers
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!eNULL:!EXPORT:!DSS:!DES:!RC4:!3DES:!MD5:!PSK')
            
            # Client certificate verification (mutual TLS)
            if verify_client:
                if os.path.exists(CA_FILE):
                    context.load_verify_locations(CA_FILE)
                    context.verify_mode = ssl.CERT_REQUIRED
                    logger.info("Client certificate verification enabled")
                else:
                    logger.warning("CA certificate not found, skipping client verification")
            
            return context
        
        except Exception as e:
            logger.error(f"Failed to create SSL context: {e}")
            return None
    
    @staticmethod
    def check_certificate_expiry() -> Optional[int]:
        """
        Check certificate expiry date
        
        Returns:
            Days until expiry or None if error
        """
        try:
            import subprocess
            from datetime import datetime
            
            if not os.path.exists(CERT_FILE):
                return None
            
            result = subprocess.run([
                'openssl', 'x509',
                '-in', CERT_FILE,
                '-noout', '-enddate'
            ], capture_output=True, text=True, check=True)
            
            # Parse date: "notAfter=Dec 25 23:59:59 2024 GMT"
            date_str = result.stdout.strip().split('=')[1]
            expiry_date = datetime.strptime(date_str, '%b %d %H:%M:%S %Y %Z')
            days_left = (expiry_date - datetime.utcnow()).days
            
            logger.info(f"Certificate expires in {days_left} days")
            
            if days_left < 30:
                logger.warning(f"Certificate expiring soon: {days_left} days")
            
            return days_left
        
        except Exception as e:
            logger.error(f"Failed to check certificate expiry: {e}")
            return None


class HTTPSServer:
    """HTTPS server configuration helper"""
    
    @staticmethod
    def get_flask_config() -> dict:
        """Get Flask configuration for HTTPS"""
        return {
            'SESSION_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PREFERRED_URL_SCHEME': 'https'
        }
    
    @staticmethod
    def get_fastapi_middleware():
        """Get FastAPI middleware for HTTPS"""
        try:
            from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
            return HTTPSRedirectMiddleware
        except ImportError:
            logger.warning("HTTPSRedirectMiddleware not available")
            return None
    
    @staticmethod
    def get_gunicorn_config() -> dict:
        """Get Gunicorn configuration for HTTPS"""
        return {
            'keyfile': KEY_FILE,
            'certfile': CERT_FILE,
            'ssl_version': 'TLSv1_2',
            'ca_certs': CA_FILE,
            'cert_reqs': 0,  # Set to 1 or 2 for client cert verification
            'suppress_ragged_eof': True
        }


# Example: Gunicorn command line
"""
gunicorn app:app \\
    --certfile=certs/server.crt \\
    --keyfile=certs/server.key \\
    --ssl-version=TLSv1_2 \\
    --bind 0.0.0.0:443 \\
    --workers 4
"""


# Example: Docker configuration
DOCKER_HTTPS_CONFIG = """
# Dockerfile for HTTPS deployment
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY xids-framework ./xids-framework
COPY certs/ ./certs/

ENV CERT_DIR=/app/certs
ENV FLASK_ENV=production

EXPOSE 443

CMD ["gunicorn", "xids-framework.api:app", \\
     "--certfile=/app/certs/server.crt", \\
     "--keyfile=/app/certs/server.key", \\
     "--ssl-version=TLSv1_2", \\
     "--bind=0.0.0.0:443", \\
     "--workers=4", \\
     "--worker-class=gevent", \\
     "--timeout=120"]
"""


if __name__ == "__main__":
    # Test certificate management
    print("Checking TLS configuration...")
    
    # Create self-signed certificate for development
    if not os.path.exists(CERT_FILE):
        print("\n1. Creating self-signed certificate...")
        TLSManager.create_self_signed_cert()
    
    # Check certificate expiry
    print("\n2. Checking certificate expiry...")
    days_left = TLSManager.check_certificate_expiry()
    if days_left:
        print(f"   Certificate expires in {days_left} days")
    
    # Test SSL context
    print("\n3. Testing SSL context creation...")
    context = TLSManager.get_ssl_context()
    if context:
        print(f"   ✓ SSL context created successfully")
        print(f"   TLS Version: {context.minimum_version} - {context.maximum_version}")
    else:
        print("   ✗ Failed to create SSL context")
    
    # Show Flask configuration
    print("\n4. Flask HTTPS Configuration:")
    for key, value in HTTPSServer.get_flask_config().items():
        print(f"   {key}: {value}")
    
    # Show Gunicorn configuration
    print("\n5. Gunicorn Configuration:")
    for key, value in HTTPSServer.get_gunicorn_config().items():
        print(f"   {key}: {value}")
    
    print("\n✅ TLS setup complete")
