class CommentValidator:
    def __call__(self, value):
        bad_words = ['fuck', 'احمق']  # and other bad words
        for word in bad_words:
            value = value.replace(word, '*' * len(word))
        return value
