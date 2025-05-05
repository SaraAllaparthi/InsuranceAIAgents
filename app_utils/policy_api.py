# Stub for policy validation – replace with real API call
VALID_POLICIES = {"DEMO-12345", "DEMO-678910", "DEMO-11111", "99999"}

def validate_policy(policy_no: str) -> bool:
    """Return True if policy number exists in the system."""
    return policy_no in VALID_POLICIES
