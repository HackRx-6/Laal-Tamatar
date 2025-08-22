def smallest_almost_equal_index(s, pattern):
    len_s = len(s)
    len_p = len(pattern)
    for i in range(len_s - len_p + 1):
        substring = s[i:i + len_p]
        difference = sum(1 for a, b in zip(substring, pattern) if a != b)
        if difference <= 1:
            return i
    return -1

if __name__ == '__main__':
    s = 'ababbababa'
    pattern = 'bacaba'
    result = smallest_almost_equal_index(s, pattern)
    print(result)