#!/usr/bin/env python3
"""Generate self-signed SSL certificate for development"""

import os
import subprocess
from pathlib import Path

def generate_self_signed_cert():
    """Generate self-signed certificate using OpenSSL"""
    
    cert_dir = Path("certs")
    cert_dir.mkdir(exist_ok=True)
    
    keyfile = cert_dir / "privkey.pem"
    certfile = cert_dir / "fullchain.pem"
    
    if keyfile.exists() and certfile.exists():
        print(f"✓ Certificates already exist:")
        print(f"  - {keyfile}")
        print(f"  - {certfile}")
        return str(keyfile), str(certfile)
    
    print("Generating self-signed certificate...")
    
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:4096",
        "-nodes",
        "-keyout", str(keyfile),
        "-out", str(certfile),
        "-days", "365",
        "-subj", "/CN=localhost/O=LMS Chatbot/C=US"
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✓ Certificate generated successfully:")
        print(f"  - {keyfile}")
        print(f"  - {certfile}")
        print(f"\n✓ Add to .env:")
        print(f"SSL_KEYFILE={keyfile}")
        print(f"SSL_CERTFILE={certfile}")
        print(f"APP_BASE_URL=https://localhost:8001")
        return str(keyfile), str(certfile)
    except subprocess.CalledProcessError as e:
        print(f"✗ Error: {e.stderr.decode()}")
        return None, None
    except FileNotFoundError:
        print("✗ OpenSSL not found. Install it:")
        print("  - Windows: choco install openssl")
        print("  - Mac: brew install openssl")
        print("  - Linux: sudo apt-get install openssl")
        return None, None

if __name__ == "__main__":
    generate_self_signed_cert()
