def common_prefix_len(str1, str2):
    i = 0
    while i < min(len(str1), len(str2)) and str1[i] == str2[i]:
        i += 1
    return i


def classify_question_locally(opt_a, opt_b, opt_c, opt_d):
    opts = [o.lower().strip() for o in [opt_a, opt_b, opt_c, opt_d] if o]
    if len(opts) < 4:
        return 'grammar'

    pairs_sharing = 0
    for i in range(4):
        for j in range(i + 1, 4):
            if common_prefix_len(opts[i], opts[j]) >= 3:
                pairs_sharing += 1

    if pairs_sharing >= 3:
        return 'grammar'

    grammar_words = {
        'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
        'they', 'them', 'their', 'theirs', 'themselves', 'i', 'me', 'my', 'mine', 'myself',
        'we', 'us', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourselves',
        'who', 'whom', 'whose', 'which', 'that',
        'in', 'on', 'at', 'by', 'for', 'with', 'about', 'between', 'through', 'during',
        'because', 'although', 'though', 'even', 'if', 'unless', 'since', 'until', 'while',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'do', 'does', 'did', 'done', 'doing',
        'have', 'has', 'had', 'having', 'will', 'would', 'shall', 'should',
        'can', 'could', 'may', 'might', 'must',
    }
    if all(o in grammar_words for o in opts):
        return 'grammar'
    return 'vocabulary'
