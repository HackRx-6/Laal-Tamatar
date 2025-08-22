def smallest_almost_equal_index(s, pattern):
    m, n = len(s), len(pattern)
    if n > m:
        return -1
    
    for i in range(m - n + 1):
        substr = s[i:i+n]
        diff_count = 0
        for a, b in zip(substr, pattern):
            if a != b:
                diff_count += 1
                if diff_count > 1:
                    break
        if diff_count <= 1:
            return i
    return -1

if __name__ == "__main__":
    test_cases = [
        ("abcdefg", "bcdffg"),
        ("ababbababa", "bacaba")
    ]
    results = [smallest_almost_equal_index(s, p) for s, p in test_cases]
    for result in results:
        print(result)
