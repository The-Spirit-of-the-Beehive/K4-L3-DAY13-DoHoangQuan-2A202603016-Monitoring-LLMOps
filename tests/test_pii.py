from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out

def test_scrub_cccd() -> None:
    cccd_samples = (
        "001234567890",
        "079123456789",
        "001 234 567 890",
        "001-234-567-890",
        "0012-3456-7890",
    )

    for cccd in cccd_samples:
        out = scrub_text(f"Số CCCD của tôi là {cccd}")
        assert cccd not in out
        assert "REDACTED_CCCD" in out


def test_scrub_credit_card() -> None:
    card_samples = (
        "1234567812345678",        # 16 số liền
        "4111 2222 3333 4444",    # 16 số có khoảng trắng
        "5500-0000-0000-0004",    # 16 số có dấu gạch ngang
        "3782 822463 10005",      # Thẻ Amex 15 số
    )

    for card in card_samples:
        out = scrub_text(f"Thanh toán qua thẻ: {card}")
        assert card not in out
        assert "REDACTED_CREDIT_CARD" in out


def test_scrub_passport() -> None:
    passports = ("C1234567", "B98765432")
    for passport in passports:
        out = scrub_text(f"Hộ chiếu số {passport}")
        assert passport not in out
        assert "REDACTED_PASSPORT" in out


def test_scrub_multiple_pii_in_one_sentence() -> None:
    raw_text = (
        "Khách hàng nguyen.van.a@gmail.com, SDT: 0987654321, "
        "CCCD: 001234567890 thanh toán bằng thẻ 4111-2222-3333-4444."
    )
    out = scrub_text(raw_text)

    # Đảm bảo không còn dữ liệu nhạy cảm thô
    assert "nguyen.van.a@gmail.com" not in out
    assert "0987654321" not in out
    assert "001234567890" not in out
    assert "4111-2222-3333-4444" not in out

    # Đảm bảo đã gắn cờ redact tương ứng
    assert "REDACTED_EMAIL" in out
    assert "REDACTED_PHONE_VN" in out
    assert "REDACTED_CCCD" in out
    assert "REDACTED_CREDIT_CARD" in out
