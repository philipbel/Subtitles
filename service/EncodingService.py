import encodings


class EncodingService(object):
    def __init__(self):
        super().__init__()

        self._encodings = self._get_encodings()

    def _get_encodings(self):
        enc_list = list(set(sorted(encodings.aliases.aliases.values())))
        for i in range(len(enc_list)):
            enc = enc_list[i]
            enc = enc.upper()
            enc = enc.replace('_', '-')
            enc_list[i] = enc
        return sorted(enc_list)

    @property
    def encodings(self):
        return self._encodings
