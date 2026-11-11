from main import add, is_palindrome


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_palindrome():
    assert is_palindrome("racecar") is True
    assert is_palindrome("Race Car") is True
    assert is_palindrome("hello") is False
