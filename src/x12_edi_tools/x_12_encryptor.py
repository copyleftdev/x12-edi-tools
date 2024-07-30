import os
from typing import Union
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from base64 import b64encode, b64decode

class X12EncryptorError(Exception):
    """Custom exception for X12Encryptor errors."""

class X12Encryptor:
    """
    A robust encryptor for X12 EDI data.
    
    This class provides methods to encrypt and decrypt X12 data for secure transmission.
    It uses AES encryption in CBC mode with PKCS7 padding.
    """
    
    def __init__(self, key: Union[str, bytes]):
        """
        Initialize the X12Encryptor with an encryption key.
        
        Args:
            key (Union[str, bytes]): The encryption key. If a string is provided,
                                     it will be encoded to bytes.
        
        Raises:
            X12EncryptorError: If the key is invalid.
        """
        try:
            self.key = key.encode() if isinstance(key, str) else key
            if len(self.key) not in (16, 24, 32):
                raise ValueError("Key must be 16, 24, or 32 bytes long")
        except Exception as e:
            raise X12EncryptorError(f"Invalid encryption key: {str(e)}") from e

    def encrypt(self, x12_content: str) -> str:
        """
        Encrypt the X12 content.
        
        Args:
            x12_content (str): The X12 EDI content as a string.
        
        Returns:
            str: The encrypted X12 content as a base64-encoded string.
        
        Raises:
            X12EncryptorError: If encryption fails.
        """
        try:
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(x12_content.encode()) + padder.finalize()
            
            iv = os.urandom(16)
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            return b64encode(iv + encrypted_data).decode()
        except Exception as e:
            raise X12EncryptorError(f"Encryption failed: {str(e)}") from e

    def decrypt(self, encrypted_content: str) -> str:
        """
        Decrypt the encrypted X12 content.
        
        Args:
            encrypted_content (str): The encrypted X12 content as a base64-encoded string.
        
        Returns:
            str: The decrypted X12 content as a string.
        
        Raises:
            X12EncryptorError: If decryption fails.
        """
        try:
            encrypted_data = b64decode(encrypted_content)
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
            
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            
            return data.decode()
        except Exception as e:
            raise X12EncryptorError(f"Decryption failed: {str(e)}") from e

    def encrypt_file(self, input_file: str, output_file: str) -> None:
        """
        Encrypt an X12 file and save the encrypted content to a new file.
        
        Args:
            input_file (str): Path to the input X12 file.
            output_file (str): Path to save the encrypted output file.
        
        Raises:
            X12EncryptorError: If file encryption fails.
        """
        try:
            with open(input_file, 'r') as f:
                x12_content = f.read()
            encrypted_content = self.encrypt(x12_content)
            with open(output_file, 'w') as f:
                f.write(encrypted_content)
        except Exception as e:
            raise X12EncryptorError(f"File encryption failed: {str(e)}") from e

    def decrypt_file(self, input_file: str, output_file: str) -> None:
        """
        Decrypt an encrypted X12 file and save the decrypted content to a new file.
        
        Args:
            input_file (str): Path to the encrypted input file.
            output_file (str): Path to save the decrypted X12 output file.
        
        Raises:
            X12EncryptorError: If file decryption fails.
        """
        try:
            with open(input_file, 'r') as f:
                encrypted_content = f.read()
            decrypted_content = self.decrypt(encrypted_content)
            with open(output_file, 'w') as f:
                f.write(decrypted_content)
        except Exception as e:
            raise X12EncryptorError(f"File decryption failed: {str(e)}") from e

    def __repr__(self) -> str:
        """Provide a string representation of the encryptor state."""
        return f"X12Encryptor(key_length={len(self.key)})"