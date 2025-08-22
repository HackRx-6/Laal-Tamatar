def smallest_almost_equal_index(s, pattern):
    m, n = len(s), len(pattern)
    for i in range(m - n + 1):
        substring = s[i:i+n]
        diff_count = 0
        for a, b in zip(substring, pattern):
            if a != b:
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
    result1 = smallest_almost_equal_index(s1, pattern1)
    print(result1)

    # Test case 2
    s2 = "ababbababa"
    pattern2 = "bacaba"
    result2 = smallest_almost_equal_index(s2, pattern2)
    print(result2)
