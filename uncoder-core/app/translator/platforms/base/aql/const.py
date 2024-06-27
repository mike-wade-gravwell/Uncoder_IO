UTF8_PAYLOAD_PATTERN = r"UTF8\(payload\)"
NUM_VALUE_PATTERN = r"(?P<num_value>\d+(?:\.\d+)*)"
SINGLE_QUOTES_VALUE_PATTERN = (
    r"""'(?P<s_q_value>(?:[:a-zA-Zа-яА-Я\*0-9=+%#\-\/\\|,;_<>`~".$&^@!?\(\)\{\}\[\]\s]|'')*)'"""  # noqa: RUF001
)
TABLE_PATTERN = r"\s+FROM\s+[a-zA-Z.\-*]+"
TABLE_GROUP_PATTERN = r"\s+FROM\s+(?P<table>[a-zA-Z.\-*]+)"
