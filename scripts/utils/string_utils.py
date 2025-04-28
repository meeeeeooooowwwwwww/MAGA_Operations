#!/usr/bin/env python3
"""
String Utility Module.

Provides functions for string manipulation and processing.
Includes functions for text formatting, validation, and transformations.
"""
import re
import uuid
import random
import string
import hashlib
import unicodedata
import json
from typing import Any, Dict, List, Optional, Union, Pattern, Match, Set, Tuple, Callable

def slugify(text: str, separator: str = "-", lowercase: bool = True, 
           remove_accents: bool = True, allowed_chars: str = "") -> str:
    """
    Convert text to a URL-friendly slug.
    
    Args:
        text (str): Text to slugify
        separator (str, optional): Separator to use
        lowercase (bool, optional): Convert to lowercase
        remove_accents (bool, optional): Remove accent characters
        allowed_chars (str, optional): Additional allowed characters
        
    Returns:
        str: Slug string
    """
    # Convert to lowercase if requested
    if lowercase:
        text = text.lower()
    
    # Remove accents if requested
    if remove_accents:
        text = unicodedata.normalize('NFKD', text)
        text = ''.join([c for c in text if not unicodedata.combining(c)])
    
    # Replace whitespace with separator
    text = re.sub(r'\s+', separator, text)
    
    # Replace other characters with separator
    pattern = rf'[^a-zA-Z0-9{re.escape(separator)}{re.escape(allowed_chars)}]+'
    text = re.sub(pattern, separator, text)
    
    # Remove duplicate separators
    text = re.sub(rf'{re.escape(separator)}+', separator, text)
    
    # Remove leading/trailing separators
    return text.strip(separator)

def truncate(text: str, length: int, suffix: str = "...") -> str:
    """
    Truncate text to specified length.
    
    Args:
        text (str): Text to truncate
        length (int): Maximum length
        suffix (str, optional): Suffix to append
        
    Returns:
        str: Truncated text
    """
    if len(text) <= length:
        return text
    
    return text[:length - len(suffix)] + suffix

def strip_html(html: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        html (str): HTML text
        
    Returns:
        str: Plain text
    """
    return re.sub(r'<[^>]+>', '', html)

def strip_extra_whitespace(text: str) -> str:
    """
    Remove extra whitespace from text.
    
    Args:
        text (str): Text to process
        
    Returns:
        str: Cleaned text
    """
    return re.sub(r'\s+', ' ', text).strip()

def camel_to_snake(text: str) -> str:
    """
    Convert camelCase to snake_case.
    
    Args:
        text (str): Text in camelCase
        
    Returns:
        str: Text in snake_case
    """
    # Handle special case for acronyms (e.g. APIResponse -> api_response)
    text = re.sub(r'([A-Z])([A-Z][a-z])', r'\1_\2', text)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text).lower()

def snake_to_camel(text: str, capitalize_first: bool = False) -> str:
    """
    Convert snake_case to camelCase.
    
    Args:
        text (str): Text in snake_case
        capitalize_first (bool, optional): Capitalize first letter
        
    Returns:
        str: Text in camelCase
    """
    # Split on underscores and capitalize words
    components = text.split('_')
    
    # Capitalize words except first (unless specified)
    if capitalize_first:
        result = ''.join(x.title() for x in components)
    else:
        result = components[0] + ''.join(x.title() for x in components[1:])
    
    return result

def snake_to_kebab(text: str) -> str:
    """
    Convert snake_case to kebab-case.
    
    Args:
        text (str): Text in snake_case
        
    Returns:
        str: Text in kebab-case
    """
    return text.replace('_', '-')

def kebab_to_snake(text: str) -> str:
    """
    Convert kebab-case to snake_case.
    
    Args:
        text (str): Text in kebab-case
        
    Returns:
        str: Text in snake_case
    """
    return text.replace('-', '_')

def split_by_case(text: str) -> List[str]:
    """
    Split camelCase or PascalCase text into words.
    
    Args:
        text (str): Text to split
        
    Returns:
        list: List of words
    """
    # Handle special case for acronyms first
    text = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', text)
    # Split by uppercase letters
    words = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text).split()
    return words

def generate_random_string(length: int = 10, include_digits: bool = True, 
                         include_special: bool = False) -> str:
    """
    Generate random string of specified length.
    
    Args:
        length (int, optional): String length
        include_digits (bool, optional): Include digits
        include_special (bool, optional): Include special characters
        
    Returns:
        str: Random string
    """
    # Define character sets
    chars = string.ascii_letters
    
    if include_digits:
        chars += string.digits
    
    if include_special:
        chars += string.punctuation
    
    # Generate random string
    return ''.join(random.choice(chars) for _ in range(length))

def generate_uuid(version: int = 4, namespace=None, name: str = None) -> str:
    """
    Generate UUID.
    
    Args:
        version (int, optional): UUID version (1, 3, 4, 5)
        namespace: Namespace UUID for versions 3, 5
        name (str, optional): Name for versions 3, 5
        
    Returns:
        str: UUID string
    """
    if version == 1:
        return str(uuid.uuid1())
    elif version == 3 and namespace and name:
        return str(uuid.uuid3(namespace, name))
    elif version == 4:
        return str(uuid.uuid4())
    elif version == 5 and namespace and name:
        return str(uuid.uuid5(namespace, name))
    else:
        if version not in [1, 3, 4, 5]:
            raise ValueError(f"Invalid UUID version: {version}")
        elif version in [3, 5] and (not namespace or not name):
            raise ValueError(f"Namespace and name required for UUID version {version}")
        else:
            raise ValueError("Invalid UUID parameters")

def safe_filename(filename: str, max_length: int = 255) -> str:
    """
    Convert string to safe filename.
    
    Args:
        filename (str): Original filename
        max_length (int, optional): Maximum length
        
    Returns:
        str: Safe filename
    """
    # Remove invalid characters
    safe_name = re.sub(r'[\\/*?:"<>|]', '', filename)
    
    # Replace spaces with underscores
    safe_name = safe_name.replace(' ', '_')
    
    # Truncate if needed
    if len(safe_name) > max_length:
        base, ext = os.path.splitext(safe_name)
        safe_name = f"{base[:max_length - len(ext)]}{ext}"
    
    return safe_name

def pluralize(word: str, count: int = 0, plural_suffix: str = "s") -> str:
    """
    Pluralize word based on count.
    
    Args:
        word (str): Word to pluralize
        count (int, optional): Count
        plural_suffix (str, optional): Plural suffix
        
    Returns:
        str: Pluralized word
    """
    if count == 1:
        return word
    else:
        return f"{word}{plural_suffix}"

def ordinal(n: int) -> str:
    """
    Convert number to ordinal string.
    
    Args:
        n (int): Number
        
    Returns:
        str: Ordinal string
    """
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    
    return f"{n}{suffix}"

def is_valid_email(email: str) -> bool:
    """
    Check if string is valid email address.
    
    Args:
        email (str): Email address
        
    Returns:
        bool: True if valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_url(url: str) -> bool:
    """
    Check if string is valid URL.
    
    Args:
        url (str): URL
        
    Returns:
        bool: True if valid
    """
    pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))

def contains_any(text: str, substrings: List[str], case_sensitive: bool = True) -> bool:
    """
    Check if text contains any of the specified substrings.
    
    Args:
        text (str): Text to check
        substrings (list): Substrings to check for
        case_sensitive (bool, optional): Case sensitive check
        
    Returns:
        bool: True if any substring found
    """
    if not case_sensitive:
        text = text.lower()
        substrings = [s.lower() for s in substrings]
    
    return any(s in text for s in substrings)

def contains_all(text: str, substrings: List[str], case_sensitive: bool = True) -> bool:
    """
    Check if text contains all of the specified substrings.
    
    Args:
        text (str): Text to check
        substrings (list): Substrings to check for
        case_sensitive (bool, optional): Case sensitive check
        
    Returns:
        bool: True if all substrings found
    """
    if not case_sensitive:
        text = text.lower()
        substrings = [s.lower() for s in substrings]
    
    return all(s in text for s in substrings)

def hash_string(text: str, algorithm: str = "sha256") -> str:
    """
    Hash string using specified algorithm.
    
    Args:
        text (str): Text to hash
        algorithm (str, optional): Hash algorithm
        
    Returns:
        str: Hash string
    """
    # Select hash algorithm
    if algorithm == "md5":
        hash_obj = hashlib.md5()
    elif algorithm == "sha1":
        hash_obj = hashlib.sha1()
    elif algorithm == "sha256":
        hash_obj = hashlib.sha256()
    elif algorithm == "sha512":
        hash_obj = hashlib.sha512()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    # Calculate hash
    hash_obj.update(text.encode('utf-8'))
    return hash_obj.hexdigest()

def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text (str): Text to extract from
        
    Returns:
        list: List of URLs
    """
    pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+|[A-Za-z0-9][^\s<>"]*\.(com|org|net|edu|gov)[^\s<>"]*'
    return re.findall(pattern, text)

def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text (str): Text to extract from
        
    Returns:
        list: List of email addresses
    """
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(pattern, text)

def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from text.
    
    Args:
        text (str): Text to extract from
        
    Returns:
        list: List of hashtags
    """
    pattern = r'#[a-zA-Z0-9_]+'
    return re.findall(pattern, text)

def extract_mentions(text: str) -> List[str]:
    """
    Extract @mentions from text.
    
    Args:
        text (str): Text to extract from
        
    Returns:
        list: List of mentions
    """
    pattern = r'@[a-zA-Z0-9_]+'
    return re.findall(pattern, text)

def format_number(number: Union[int, float], decimals: int = 2) -> str:
    """
    Format number with thousands separator and specified decimals.
    
    Args:
        number (int or float): Number to format
        decimals (int, optional): Number of decimal places
        
    Returns:
        str: Formatted number
    """
    return f"{number:,.{decimals}f}"

def format_json(json_data: Union[Dict, List], indent: int = 2) -> str:
    """
    Format JSON data as string.
    
    Args:
        json_data (dict or list): JSON data
        indent (int, optional): Indentation
        
    Returns:
        str: Formatted JSON string
    """
    return json.dumps(json_data, indent=indent, ensure_ascii=False)

def format_size(size_bytes: int) -> str:
    """
    Format byte size as human readable string.
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted size
    """
    # Define size units
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    
    # Calculate unit index
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.2f} {units[i]}"

def mask_email(email: str) -> str:
    """
    Mask email address for privacy.
    
    Args:
        email (str): Email address
        
    Returns:
        str: Masked email
    """
    if not is_valid_email(email):
        return email
    
    # Split email into username and domain
    username, domain = email.split('@')
    
    # Mask username
    if len(username) <= 2:
        masked_username = username[0] + '*' * len(username[1:])
    else:
        masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
    
    return f"{masked_username}@{domain}"

def mask_phone(phone: str) -> str:
    """
    Mask phone number for privacy.
    
    Args:
        phone (str): Phone number
        
    Returns:
        str: Masked phone
    """
    # Remove non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Mask digits
    if len(digits) <= 4:
        return '*' * len(digits)
    else:
        return '*' * (len(digits) - 4) + digits[-4:]

def split_by_length(text: str, length: int) -> List[str]:
    """
    Split text into chunks of specified length.
    
    Args:
        text (str): Text to split
        length (int): Chunk length
        
    Returns:
        list: List of chunks
    """
    return [text[i:i+length] for i in range(0, len(text), length)]

def simplify_whitespace(text: str) -> str:
    """
    Replace all whitespace with single spaces.
    
    Args:
        text (str): Text to process
        
    Returns:
        str: Processed text
    """
    return ' '.join(text.split())

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein (edit) distance between two strings.
    
    Args:
        s1 (str): First string
        s2 (str): Second string
        
    Returns:
        int: Edit distance
    """
    # Create distance matrix
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Initialize first row and column
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    # Fill distance matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j] + 1,      # deletion
                dp[i][j-1] + 1,      # insertion
                dp[i-1][j-1] + cost  # substitution
            )
    
    return dp[m][n]

def string_similarity(s1: str, s2: str) -> float:
    """
    Calculate string similarity as 1 - normalized Levenshtein distance.
    
    Args:
        s1 (str): First string
        s2 (str): Second string
        
    Returns:
        float: Similarity (0-1)
    """
    # Handle empty strings
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    
    # Calculate Levenshtein distance
    distance = levenshtein_distance(s1, s2)
    
    # Normalize by maximum length
    max_len = max(len(s1), len(s2))
    
    return 1.0 - (distance / max_len)

def encode_entities(text: str) -> str:
    """
    Encode HTML entities.
    
    Args:
        text (str): Text to encode
        
    Returns:
        str: Encoded text
    """
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

def decode_entities(text: str) -> str:
    """
    Decode HTML entities.
    
    Args:
        text (str): Text to decode
        
    Returns:
        str: Decoded text
    """
    return text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")

def wrap_text(text: str, width: int = 80, initial_indent: str = "", subsequent_indent: str = "") -> str:
    """
    Wrap text to specified width.
    
    Args:
        text (str): Text to wrap
        width (int, optional): Line width
        initial_indent (str, optional): Initial line indent
        subsequent_indent (str, optional): Subsequent lines indent
        
    Returns:
        str: Wrapped text
    """
    import textwrap
    return textwrap.fill(
        text, 
        width=width, 
        initial_indent=initial_indent, 
        subsequent_indent=subsequent_indent
    )

def find_all(text: str, pattern: str, case_sensitive: bool = True) -> List[int]:
    """
    Find all occurrences of pattern in text.
    
    Args:
        text (str): Text to search in
        pattern (str): Pattern to search for
        case_sensitive (bool, optional): Case sensitive search
        
    Returns:
        list: List of start indices
    """
    # Set flags for case sensitivity
    flags = 0 if case_sensitive else re.IGNORECASE
    
    # Find all occurrences
    return [match.start() for match in re.finditer(re.escape(pattern), text, flags)]

if __name__ == "__main__":
    # Test string utilities
    
    # Test slugify
    print(f"slugify: {slugify('Hello World! This is a test')}")  # hello-world-this-is-a-test
    
    # Test truncate
    print(f"truncate: {truncate('This is a long text that should be truncated', 20)}")  # This is a long text...
    
    # Test case conversions
    print(f"camel_to_snake: {camel_to_snake('camelCaseText')}")  # camel_case_text
    print(f"snake_to_camel: {snake_to_camel('snake_case_text')}")  # snakeCaseText
    
    # Test random string generation
    print(f"random string: {generate_random_string(12, True, True)}")
    
    # Test UUID generation
    print(f"uuid: {generate_uuid()}")
    
    # Test validation
    print(f"is_valid_email: {is_valid_email('test@example.com')}")  # True
    print(f"is_valid_url: {is_valid_url('https://example.com')}")  # True
    
    # Test string manipulations
    print(f"ordinal: {ordinal(1)}, {ordinal(2)}, {ordinal(3)}, {ordinal(4)}, {ordinal(11)}")  # 1st, 2nd, 3rd, 4th, 11th
    
    # Test masking
    print(f"mask_email: {mask_email('john.doe@example.com')}")  # j******e@example.com
    print(f"mask_phone: {mask_phone('(123) 456-7890')}")  # *******7890
    
    # Test similarity
    print(f"string_similarity: {string_similarity('hello', 'helo')}")  # similarity value