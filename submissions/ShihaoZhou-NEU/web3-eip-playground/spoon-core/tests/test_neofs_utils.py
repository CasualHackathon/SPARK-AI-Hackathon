import os

import pytest

from spoon_ai.neofs.utils import (
    _encode_varint,
    _build_serialized_message,
    generate_simple_signature_params,
    sign_with_salt,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, b"\x00"),
        (1, b"\x01"),
        (0xFC, b"\xFC"),
        (0xFD, b"\xFD\xFD\x00"),
        (0xFFFF, b"\xFD\xFF\xFF"),
        (0x10000, b"\xFE\x00\x00\x01\x00"),
        (0xFFFFFFFF, b"\xFE\xFF\xFF\xFF\xFF"),
        (0x100000000, b"\xFF\x00\x00\x00\x00\x01\x00\x00\x00"),
    ],
)
def test_encode_varint(value, expected):
    assert _encode_varint(value) == expected


def test_encode_varint_negative():
    with pytest.raises(ValueError):
        _encode_varint(-1)


def test_build_serialized_message():
    salt = bytes.fromhex("2b62f24c77ec30bac716b116651b9d23")
    payload = b"hello"
    message = _build_serialized_message((salt, payload))
    assert (
        message.hex()
        == "010001f0" "15" "2b62f24c77ec30bac716b116651b9d2368656c6c6f" "0000"
    )


@pytest.mark.skipif(not os.getenv("NEOFS_PRIVATE_KEY_WIF"), reason="requires private key")
def test_sign_with_salt_matches_notebook():
    private_key_wif = os.getenv("NEOFS_PRIVATE_KEY_WIF")
    salt = bytes.fromhex("2b62f24c77ec30bac716b116651b9d23")
    result = sign_with_salt(private_key_wif, b"hello", salt=salt)
    assert result.salt == salt.hex()
    assert len(result.signature) == 128
    assert len(result.public_key) == 66


@pytest.mark.skipif(not os.getenv("NEOFS_PRIVATE_KEY_WIF"), reason="requires private key")
def test_generate_simple_signature_params_structure():
    private_key_wif = os.getenv("NEOFS_PRIVATE_KEY_WIF")
    params = generate_simple_signature_params(private_key_wif)
    assert params["signatureScheme"] == "ECDSA_SHA256"
    assert params["signatureParam"].endswith(tuple("0123456789abcdef"))
    assert len(params["signatureKeyParam"]) == 66
