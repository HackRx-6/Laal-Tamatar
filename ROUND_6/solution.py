import json

def smallest_almost_equal_index(s: str, pattern: str) -> int:
    n, m = len(s), len(pattern)
    if m > n:
        return -1
    # Brute-force check each window of length m
    for i in range(n - m + 1):
        diff = 0
        for j in range(m):
            if s[i + j] != pattern[j]:
                diff += 1
                if diff > 1:
                    break
        if diff <= 1:
            return i
    return -1

if __name__ == "__main__":
    try:
        s1 = "abcdefg"
        p1 = "bcdffg"
        s2 = "ababbababa"
        p2 = "bacaba"
        ans1 = smallest_almost_equal_index(s1, p1)
        ans2 = smallest_almost_equal_index(s2, p2)
        print(json.dumps([ans1, ans2]))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
