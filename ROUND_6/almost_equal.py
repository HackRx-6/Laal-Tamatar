def smallest_almost_equal_index(s, pattern):
    m, n = len(pattern), len(s)
    if m > n:
        return -1
    for i in range(n - m + 1):
        diff = 0
        for j in range(m):
            if s[i+j] != pattern[j]:
                diff += 1
                if diff > 1:
                    break
        if diff <= 1:
            return i
    return -1

if __name__ == "__main__":
    # Test cases from the questions data
    s1, pattern1 = "abcdefg", "bcdffg"
    s2, pattern2 = "ababbababa", "bacaba"

    result1 = smallest_almost_equal_index(s1, pattern1)
    result2 = smallest_almost_equal_index(s2, pattern2)

    print(result1)
    print(result2)