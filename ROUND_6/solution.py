#!/usr/bin/env python3
import json

def smallest_almost_equal_index(s: str, pattern: str) -> int:
    n, m = len(s), len(pattern)
    if m > n:
        return -1
    for i in range(n - m + 1):
        diff = 0
        # Early exit if more than 1 difference
        for a, b in zip(s[i:i+m], pattern):
            if a != b:
                diff += 1
                if diff > 1:
                    break
        if diff <= 1:
            return i
    return -1


def run_cases():
    cases = [
        ("abcdefg", "bcdffg"),
        ("ababbababa", "bacaba"),
    ]
    results = [smallest_almost_equal_index(s, p) for s, p in cases]
    # As per requirement, output as JSON array (convert to strings for uniform API response)
    print(json.dumps([str(x) for x in results]))


if __name__ == "__main__":
    try:
        run_cases()
    except Exception as e:
        # Ensure we don't crash silently
        print(json.dumps({"error": str(e)}))
