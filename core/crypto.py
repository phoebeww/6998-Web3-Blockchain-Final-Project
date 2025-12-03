# core/crypto.py
"""
Cryptographic utilities for digital signatures in the voting system.
Uses RSA public-key cryptography to ensure vote authenticity and integrity.
"""

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from typing import Tuple
import hashlib


def generate_keypair() -> Tuple[str, str]:
    """
    Generate an RSA public-private key pair for signing votes.
    
    Returns:
        tuple: (private_key_pem, public_key_pem) as PEM-encoded strings
    """
    # Generate RSA private key with 2048 bits
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Derive public key from private key
    public_key = private_key.public_key()
    
    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    # Serialize public key to PEM format
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return private_pem, public_pem


def sign_message(message: str, private_key_pem: str) -> str:
    """
    Sign a message using the private key.
    
    Args:
        message: The message to sign
        private_key_pem: PEM-encoded private key
        
    Returns:
        str: Hex-encoded signature
    """
    # Load private key from PEM format
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode('utf-8'),
        password=None,
        backend=default_backend()
    )
    
    # Sign the message
    signature = private_key.sign(
        message.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    # Return as hex string for easy storage
    return signature.hex()


def verify_signature(message: str, signature_hex: str, public_key_pem: str) -> bool:
    """
    Verify that a signature is valid for the given message and public key.
    
    Args:
        message: The original message
        signature_hex: Hex-encoded signature
        public_key_pem: PEM-encoded public key
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    try:
        # Load public key from PEM format
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )
        
        # Decode signature from hex
        signature = bytes.fromhex(signature_hex)
        
        # Verify the signature
        public_key.verify(
            signature,
            message.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    
    except Exception:
        # Signature verification failed
        return False


def hash_public_key(public_key_pem: str) -> str:
    """
    Create a short voter ID from a public key by hashing it.
    
    Args:
        public_key_pem: PEM-encoded public key
        
    Returns:
        str: Hex string (first 16 characters) to use as voter_id
    """
    key_hash = hashlib.sha256(public_key_pem.encode('utf-8')).hexdigest()
    return key_hash[:16]  # Use first 16 characters for brevity

