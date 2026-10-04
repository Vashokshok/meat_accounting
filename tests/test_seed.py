import pytest

from scripts.seed import prompt_users


def test_prompt_users_returns_confirmed_credentials(monkeypatch) -> None:
    answers = iter(["staff", ""])
    passwords = iter(["long-passphrase", "long-passphrase"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr("scripts.seed.getpass", lambda _: next(passwords))

    assert prompt_users() == [("staff", "long-passphrase")]


def test_prompt_users_rejects_unconfirmed_password(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "staff")
    passwords = iter(["long-passphrase", "different-passphrase"])
    monkeypatch.setattr("scripts.seed.getpass", lambda _: next(passwords))

    with pytest.raises(ValueError, match="не совпадают"):
        prompt_users()
