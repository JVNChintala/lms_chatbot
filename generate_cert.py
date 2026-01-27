#!/usr/bin/env python3
"""Generate self-signed SSL certificate for development (with domain & SAN)"""

import subprocess
from pathlib import Path

def generate_self_signed_cert(domain="localhost"):
    """Generate self-signed certificate using OpenSSL with SAN"""

    cert_dir = Path("certs")
    cert_dir.mkdir(exist_ok=True)

    keyfile = cert_dir / "privkey.pem"
    certfile = cert_dir / "fullchain.pem"
    configfile = cert_dir / "openssl.cnf"

    # 🔥 Always remove existing certs
    for f in [keyfile, certfile, configfile]:
        if f.exists():
            f.unlink()

    print(f"Generating self-signed certificate for domain: {domain}")

    # OpenSSL config with SAN
    configfile.write_text(f"""
[req]
default_bits       = 4096
prompt             = no
default_md         = sha256
distinguished_name = dn
x509_extensions    = v3_req

[dn]
C  = US
O  = LMS Chatbot
CN = {domain}

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = {domain}
DNS.2 = localhost
IP.1  = 127.0.0.1
""".strip())

    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:4096",
        "-nodes",
        "-keyout", str(keyfile),
        "-out", str(certfile),
        "-days", "365",
        "-config", str(configfile)
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print("✓ Certificate generated successfully:")
        print(f"  - Key:  {keyfile}")
        print(f"  - Cert: {certfile}")
        print("\n✓ Add to .env:")
        print(f"SSL_KEYFILE={keyfile}")
        print(f"SSL_CERTFILE={certfile}")
        print(f"APP_BASE_URL=https://{domain}:8001")
        return str(keyfile), str(certfile)

    except subprocess.CalledProcessError as e:
        print("✗ OpenSSL error:")
        print(e.stderr.decode())
        return None, None

    except FileNotFoundError:
        print("✗ OpenSSL not found. Install it:")
        print("  - Windows: choco install openssl")
        print("  - Mac: brew install openssl")
        print("  - Linux: sudo apt-get install openssl")
        return None, None


if __name__ == "__main__":
    generate_self_signed_cert(domain="localhost")
