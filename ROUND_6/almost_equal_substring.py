def find_almost_equal_substring(s, pattern):
    plen = len(pattern)
    for i in range(len(s) - plen + 1):
        substring = s[i:i+plen]
        diff = sum(1 for a, b in zip(substring, pattern) if a != b)
        if diff <= 1:
            return i
    return -1

if __name__ == "__main__":
    # Test cases from user query
    test1_s = "abcdefg"
    test1_pattern = "bcdffg"
    result1 = find_almost_equal_substring(test1_s, test1_pattern)

    test2_s = "ababbababa"
    test2_pattern = "bacaba"
    result2 = find_almost_equal_substring(test2_s, test2_pattern)

    print(result1)
    print(result2)
