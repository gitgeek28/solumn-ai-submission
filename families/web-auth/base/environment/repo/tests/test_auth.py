from app.auth import create_token, verify_token


def test_token_round_trip():
    token = create_token("alice", role="admin")
    claims = verify_token(token)
    assert claims["sub"] == "alice"
    assert claims["role"] == "admin"


def test_round_trip_for_several_subjects():
    for subject in ["al", "bob", "dave.ops", "evelyn_r"]:
        assert verify_token(create_token(subject))["sub"] == subject
