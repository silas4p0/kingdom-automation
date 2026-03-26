import re
from models.token_model import TokenModel


class Tokenizer:
    @staticmethod
    def tokenize(text: str) -> list[TokenModel]:
        tokens: list[TokenModel] = []
        idx = 0
        for line_num, line in enumerate(text.split("\n")):
            words = re.findall(r"\S+", line)
            for w in words:
                t = TokenModel(w, idx)
                t.line_index = line_num
                tokens.append(t)
                idx += 1
        return tokens

    @staticmethod
    def apply_repeat_inheritance(tokens: list[TokenModel]) -> None:
        seen: dict[str, TokenModel] = {}
        for token in tokens:
            key = token.word.lower()
            if key in seen and not token.locked:
                prior = seen[key]
                if prior.locked:
                    token.copy_params_from(prior)
            if token.locked:
                seen[key] = token
