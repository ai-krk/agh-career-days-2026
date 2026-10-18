"""Reference answer. Import explicitly only after attempting the notebook TODO."""


def freshness_policy(observation, now, max_age_s):
    """Accept integer timestamps aged 0..max_age_s at the supplied frozen clock."""
    timestamp = observation.get("observed_at")
    if type(timestamp) is not int or type(now) is not int or type(max_age_s) is not int:
        return False
    return 0 <= now - timestamp <= max_age_s
