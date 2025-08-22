def smallest_almost_equal_index(s, pattern):
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
    s = "ababbababa"
    pattern = "bacaba"
    result = smallest_almost_equal_index(s, pattern)
    print(result)