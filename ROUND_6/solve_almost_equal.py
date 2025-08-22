def find_almost_equal_substring(s, pattern):
    plen = len(pattern)
    slen = len(s)

    for i in range(slen - plen + 1):
        diff_count = 0
        for j in range(plen):
            if s[i + j] != pattern[j]:
                diff_count += 1
                if diff_count > 1:
                    break
        if diff_count <= 1:
            return i
    return -1


if __name__ == "__main__":
    # Test case 1
    s1 = "abcdefg"
    pattern1 = "bcdffg"
    result1 = find_almost_equal_substring(s1, pattern1)

    # Test case 2
    s2 = "ababbababa"
    pattern2 = "bacaba"
    result2 = find_almost_equal_substring(s2, pattern2)

    print(result1)
    print(result2)