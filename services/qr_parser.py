"""
Parse otpauth:// URIs and extract TOTP/HOTP parameters.
"""
from urllib.parse import urlparse, parse_qs
import re


class QRParser:
    """Parses OTPAuth URIs."""

    @staticmethod
    def parse_otpauth_uri(uri):
        """
        Parse otpauth:// URI and extract parameters.

        Args:
            uri (str): OTPAuth URI string

        Returns:
            dict: Parsed parameters with keys:
                - type: 'totp' or 'hotp'
                - label: Account label (e.g., "user@example.com")
                - secret: Base32-encoded secret
                - issuer: Service issuer name
                - algorithm: Hash algorithm (SHA1, SHA256, etc.)
                - digits: Number of digits (default 6)
                - period: Time period in seconds (default 30, TOTP only)
                - counter: Counter value (HOTP only)

        Raises:
            ValueError: If URI format is invalid
        """

        if not uri or not isinstance(uri, str):
            raise ValueError("URI must be a non-empty string")

        if not uri.startswith("otpauth://"):
            raise ValueError("URI must start with 'otpauth://'")

        # Parse the URI
        parsed_url = urlparse(uri)

        # Extract type (totp or hotp)
        otp_type = parsed_url.netloc.lower()
        if otp_type not in ['totp', 'hotp']:
            raise ValueError(f"Unsupported OTP type: {otp_type}")

        # Extract label and issuer from path
        path = parsed_url.path.lstrip('/')

        # Path format: "issuer:label" or just "label"
        if ':' in path:
            issuer_from_path, label = path.split(':', 1)
            issuer_from_path = issuer_from_path.strip()
        else:
            issuer_from_path = None
            label = path.strip()

        # URL decode the label
        label = QRParser._url_decode(label)

        # Parse query parameters
        params = parse_qs(parsed_url.query)

        # Extract parameters (parse_qs returns lists, get first value)
        secret = QRParser._get_param(params, 'secret')
        issuer = QRParser._get_param(params, 'issuer') or issuer_from_path or 'Unknown'
        algorithm = QRParser._get_param(params, 'algorithm', 'SHA1').upper()
        digits = QRParser._get_param(params, 'digits', '6')
        period = QRParser._get_param(params, 'period', '30')
        counter = QRParser._get_param(params, 'counter', '0')

        # Validate required parameters
        if not secret:
            raise ValueError("Missing required 'secret' parameter")

        if not label:
            raise ValueError("Missing label (account identifier)")

        # Validate secret format (base32)
        if not QRParser._is_valid_base32(secret):
            raise ValueError(f"Invalid secret format: {secret}")

        # Validate algorithm
        valid_algorithms = ['SHA1', 'SHA256', 'SHA512', 'MD5']
        if algorithm not in valid_algorithms:
            raise ValueError(f"Invalid algorithm: {algorithm}. Must be one of: {', '.join(valid_algorithms)}")

        # Validate digits
        try:
            digits_int = int(digits)
            if digits_int < 4 or digits_int > 10:
                raise ValueError("Digits must be between 4 and 10")
        except ValueError:
            raise ValueError(f"Invalid digits value: {digits}")

        # Validate period (for TOTP)
        try:
            period_int = int(period)
            if period_int < 1:
                raise ValueError("Period must be positive")
        except ValueError:
            raise ValueError(f"Invalid period value: {period}")

        # Validate counter (for HOTP)
        try:
            counter_int = int(counter)
            if counter_int < 0:
                raise ValueError("Counter must be non-negative")
        except ValueError:
            raise ValueError(f"Invalid counter value: {counter}")

        # Build result dictionary
        result = {
            'type': otp_type,
            'label': label,
            'secret': secret.upper(),  # Normalize to uppercase
            'issuer': issuer,
            'algorithm': algorithm,
            'digits': str(digits_int),
            'period': str(period_int) if otp_type == 'totp' else None,
            'counter': str(counter_int) if otp_type == 'hotp' else None,
        }

        return result

    @staticmethod
    def _get_param(params_dict, key, default=None):
        """
        Get parameter value from parsed query parameters.

        Args:
            params_dict (dict): Parsed query parameters (from parse_qs)
            key (str): Parameter key
            default: Default value if not found

        Returns:
            str: Parameter value or default
        """
        if key in params_dict and params_dict[key]:
            return params_dict[key][0]
        return default

    @staticmethod
    def _url_decode(text):
        """
        URL decode a string.

        Args:
            text (str): Text to decode

        Returns:
            str: Decoded text
        """
        from urllib.parse import unquote
        return unquote(text)

    @staticmethod
    def _is_valid_base32(value):
        """
        Validate base32 string.

        Args:
            value (str): String to validate

        Returns:
            bool: True if valid base32
        """
        if not value:
            return False

        # Base32 alphabet: A-Z, 2-7, and optional padding (=)
        pattern = r'^[A-Z2-7]+=*$'
        return bool(re.match(pattern, value.upper()))

    @staticmethod
    def build_otpauth_uri(profile_data):
        """
        Build otpauth:// URI from profile data.

        Args:
            profile_data (dict): Profile data with keys:
                - type: 'totp' or 'hotp'
                - label: Account label
                - secret: Base32-encoded secret
                - issuer: Service issuer
                - algorithm: Hash algorithm
                - digits: Number of digits
                - period: Time period (TOTP)
                - counter: Counter (HOTP)

        Returns:
            str: Constructed otpauth:// URI

        Raises:
            ValueError: If required parameters are missing
        """
        required = ['type', 'label', 'secret']
        for key in required:
            if key not in profile_data or not profile_data[key]:
                raise ValueError(f"Missing required field: {key}")

        otp_type = profile_data['type'].lower()
        label = profile_data['label']
        secret = profile_data['secret']
        issuer = profile_data.get('issuer', 'Unknown')
        algorithm = profile_data.get('algorithm', 'SHA1').upper()
        digits = profile_data.get('digits', '6')

        # Build URI
        from urllib.parse import quote

        # Format: otpauth://TYPE/ISSUER:LABEL?secret=SECRET&...
        uri = f"otpauth://{otp_type}/{quote(issuer)}:{quote(label)}"

        params = []
        params.append(f"secret={secret}")
        params.append(f"issuer={quote(issuer)}")
        params.append(f"algorithm={algorithm}")
        params.append(f"digits={digits}")

        if otp_type == 'totp':
            period = profile_data.get('period', '30')
            params.append(f"period={period}")
        elif otp_type == 'hotp':
            counter = profile_data.get('counter', '0')
            params.append(f"counter={counter}")

        uri += "?" + "&".join(params)

        return uri

    @staticmethod
    def validate_uri(uri):
        """
        Validate otpauth:// URI without parsing.

        Args:
            uri (str): URI to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            QRParser.parse_otpauth_uri(uri)
            return True, ""
        except ValueError as err:
            return False, str(err)


def parse_otpauth_uri(uri):
    """
    Convenience function - parses otpauth:// URI.

    Args:
        uri (str): OTPAuth URI string

    Returns:
        dict: Parsed parameters
    """
    return QRParser.parse_otpauth_uri(uri)


def build_otpauth_uri(profile_data):
    """
    Convenience function - builds otpauth:// URI.

    Args:
        profile_data (dict): Profile data

    Returns:
        str: Constructed URI
    """
    return QRParser.build_otpauth_uri(profile_data)


# Example usage
if __name__ == "__main__":
    # Test parsing
    example_uri = "otpauth://totp/GitHub:user%40example.com?secret=JBSWY3DPEBLW64TMMQ======&issuer=GitHub&algorithm=SHA1&digits=6&period=30"

    try:
        parsed = parse_otpauth_uri(example_uri)
        print("Parsed URI:")
        for key, value in parsed.items():
            print(f"  {key}: {value}")

        # Build it back
        rebuilt = build_otpauth_uri(parsed)
        print(f"\nRebuilt URI:\n{rebuilt}")

    except ValueError as e:
        print(f"Error: {e}")