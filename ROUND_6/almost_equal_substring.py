def find_almost_equal_index(s, pattern):
    plen = len(pattern)
    for i in range(len(s)-plen+1):
        substr = s[i:i+plen]
        # Count differences
        diff_count = sum(1 for a, b in zip(substr, pattern) if a != b)
        if diff_count <= 1:
            return i
    return -1


if __name__ == "__main__":
    # Test 1
    s1 = "abcdefg"
    pattern1 = "bcdffg"
    result1 = find_almost_equal_index(s1, pattern1)

    # Test 2
    s2 = "ababbababa"
    pattern2 = "bacaba"
    result2 = find_almost_equal_index(s2, pattern2)

    print(result1)
    print(result2)
