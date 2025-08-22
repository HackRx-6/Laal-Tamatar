def smallest_starting_index(s: str, pattern: str) -> int:
    n, m = len(s), len(pattern)
    for i in range(n - m + 1):
        diff_count = 0
        for j in range(m):
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
    result1 = smallest_starting_index(s1, pattern1)

    # Test case 2
    s2 = "ababbababa"
    pattern2 = "bacaba"
    result2 = smallest_starting_index(s2, pattern2)

    print([result1, result2])
