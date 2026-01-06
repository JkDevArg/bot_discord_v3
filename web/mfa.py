"""
Sistema de autenticación MFA (TOTP)
"""
import pyotp
import qrcode
from io import BytesIO
import base64
from bot.utils.security import generate_recovery_codes


class MFAService:
    """Servicio para gestionar autenticación de dos factores"""
    
    @staticmethod
    def generate_secret() -> str:
        """
        Generar secreto TOTP para un usuario
        
        Returns:
            Secreto base32
        """
        return pyotp.random_base32()
    
    @staticmethod
    def get_totp_uri(secret: str, username: str, issuer: str = "Discord Bot Admin") -> str:
        """
        Generar URI para TOTP (compatible con Google Authenticator, Authy, etc.)
        
        Args:
            secret: Secreto TOTP
            username: Nombre de usuario
            issuer: Nombre de la aplicación
        
        Returns:
            URI TOTP
        """
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name=issuer
        )
    
    @staticmethod
    def generate_qr_code(totp_uri: str) -> str:
        """
        Generar código QR en base64 para escanear con app de autenticación
        
        Args:
            totp_uri: URI TOTP
        
        Returns:
            Imagen QR en base64
        """
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """
        Verificar código TOTP
        
        Args:
            secret: Secreto TOTP del usuario
            token: Código de 6 dígitos ingresado
        
        Returns:
            True si el código es válido
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # Ventana de 30s antes/después
    
    @staticmethod
    def verify_recovery_code(stored_codes: str, input_code: str) -> tuple[bool, str]:
        """
        Verificar código de recuperación
        
        Args:
            stored_codes: Códigos almacenados (JSON string)
            input_code: Código ingresado
        
        Returns:
            Tupla (es_válido, códigos_actualizados)
        """
        import json
        
        try:
            codes = json.loads(stored_codes) if stored_codes else []
        except:
            codes = []
        
        # Normalizar código ingresado
        input_code = input_code.upper().replace('-', '')
        
        for i, code in enumerate(codes):
            if code.replace('-', '') == input_code:
                # Código válido, removerlo (un solo uso)
                codes.pop(i)
                return True, json.dumps(codes)
        
        return False, stored_codes
    
    @staticmethod
    def setup_mfa_for_user(username: str) -> dict:
        """
        Configurar MFA para un usuario nuevo
        
        Args:
            username: Nombre de usuario
        
        Returns:
            Diccionario con secret, qr_code, recovery_codes
        """
        secret = MFAService.generate_secret()
        totp_uri = MFAService.get_totp_uri(secret, username)
        qr_code = MFAService.generate_qr_code(totp_uri)
        recovery_codes = generate_recovery_codes(10)
        
        return {
            'secret': secret,
            'qr_code': qr_code,
            'recovery_codes': recovery_codes,
            'totp_uri': totp_uri
        }
