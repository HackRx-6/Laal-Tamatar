def find_almost_equal(s, pattern):
    n = len(s)
    m = len(pattern)
    for i in range(n - m + 1):
        substring = s[i:i+m]
        # Count differences
        diff_count = sum(1 for x, y in zip(substring, pattern) if x != y)
        if diff_count <= 1:
            return i
    return -1

if __name__ == "__main__":
    s = "ababbababa"
    pattern = "bacaba"
    result = find_almost_equal(s, pattern)
    print(result)