"""
Brazilian-specific validators for contact form fields.
Ported from Flask app's validation system.
"""

import re

from django.core.exceptions import ValidationError

# Temporary email domains to block
BLOCKED_EMAIL_DOMAINS = {
    "tempmail.com",
    "throwaway.email",
    "guerrillamail.com",
    "mailinator.com",
    "yopmail.com",
    "sharklasers.com",
    "guerrillamailblock.com",
    "grr.la",
    "dispostable.com",
    "trashmail.com",
    "fakeinbox.com",
    "tempail.com",
    "tempr.email",
    "discard.email",
    "maildrop.cc",
}

# Valid Brazilian DDDs (area codes)
VALID_DDDS = {
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,  # SP
    21,
    22,
    24,  # RJ
    27,
    28,  # ES
    31,
    32,
    33,
    34,
    35,
    37,
    38,  # MG
    41,
    42,
    43,
    44,
    45,
    46,  # PR
    47,
    48,
    49,  # SC
    51,
    53,
    54,
    55,  # RS
    61,  # DF
    62,
    64,  # GO
    63,  # TO
    65,
    66,  # MT
    67,  # MS
    68,  # AC
    69,  # RO
    71,
    73,
    74,
    75,
    77,  # BA
    79,  # SE
    81,
    82,  # PE/AL
    83,  # PB
    84,  # RN
    85,
    88,  # CE
    86,
    89,  # PI
    87,  # PE
    91,
    93,
    94,  # PA
    92,
    97,  # AM
    95,  # RR
    96,  # AP
    98,
    99,  # MA
}


def validate_brazilian_phone(value):
    """Validate Brazilian phone number format."""
    digits = re.sub(r"\D", "", value)

    if len(digits) not in (10, 11):
        raise ValidationError("Telefone deve ter 10 ou 11 dígitos (com DDD).")

    ddd = int(digits[:2])
    if ddd not in VALID_DDDS:
        raise ValidationError(f"DDD {ddd} não é válido.")

    if len(digits) == 11 and digits[2] != "9":
        raise ValidationError("Celulares com 11 dígitos devem começar com 9 após o DDD.")


def validate_email_not_disposable(value):
    """Block disposable/temporary email providers."""
    domain = value.split("@")[-1].lower()
    if domain in BLOCKED_EMAIL_DOMAINS:
        raise ValidationError("Por favor, use um e-mail permanente.")


def validate_name_brazilian(value):
    """Validate Brazilian name: at least 2 words, min 2 chars each."""
    words = value.strip().split()
    if len(words) < 2:
        raise ValidationError("Por favor, informe nome e sobrenome.")
    for word in words:
        if len(word) < 2:
            raise ValidationError("Cada parte do nome deve ter pelo menos 2 caracteres.")
