"""
Uncoder IO Commercial Edition License
-----------------------------------------------------------------
Copyright (c) 2024 SOC Prime, Inc.

This file is part of the Uncoder IO Commercial Edition ("CE") and is
licensed under the Uncoder IO Non-Commercial License (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://github.com/UncoderIO/UncoderIO/blob/main/LICENSE

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-----------------------------------------------------------------
"""

import re

from app.translator.core.models.functions.base import ParsedFunctions
from app.translator.core.models.query_container import RawQueryContainer, TokenizedQueryContainer
from app.translator.core.parser import PlatformQueryParser
from app.translator.platforms.base.spl.functions import SplFunctions
from app.translator.platforms.base.spl.tokenizer import SplTokenizer

TSTATS_FUNC = "tstats"


class SplQueryParser(PlatformQueryParser):
    log_source_pattern = r"^___source_type___\s*=\s*(?:\"(?P<d_q_value>[%a-zA-Z_*:0-9\-/]+)\"|(?P<value>[%a-zA-Z_*:0-9\-/]+))(?:\s+(?:and|or)\s+|\s+)?"  # noqa: E501
    rule_name_pattern = r"`(?P<name>(?:[:a-zA-Z*0-9=+%#\-_/,;`?~‘\'.<>$&^@!\]\[()\s])*)`"  # noqa: RUF001
    log_source_key_types = ("index", "source", "sourcetype", "sourcecategory")

    platform_functions: SplFunctions = None
    tokenizer = SplTokenizer()

    wrapped_with_comment_pattern = r"^\s*```(?:|\n|.)*```"

    def _parse_log_sources(self, query: str) -> tuple[dict[str, list[str]], str]:
        log_sources = {}
        for source_type in self.log_source_key_types:
            log_sources.setdefault(source_type, [])
            pattern = self.log_source_pattern.replace("___source_type___", source_type)
            while search := re.search(pattern, query, flags=re.IGNORECASE):
                group_dict = search.groupdict()
                value = group_dict.get("d_q_value") or group_dict.get("value")
                log_sources.setdefault(source_type, []).append(value)
                pos_start = search.start()
                pos_end = search.end()
                query = query[:pos_start] + query[pos_end:]
                query = query.replace("()", "")

        return log_sources, query

    def _parse_query(self, query: str) -> tuple[str, dict[str, list[str]], ParsedFunctions]:
        if re.match(self.rule_name_pattern, query):
            search = re.search(self.rule_name_pattern, query, flags=re.IGNORECASE)
            query = query[: search.start()] + query[search.end() :]
        query = query.strip()
        log_sources, query = self._parse_log_sources(query)
        query, functions = self.platform_functions.parse(query)
        return query, log_sources, functions

    @staticmethod
    def __is_tstats_query(query: str) -> bool:
        return bool(re.match(r"\s*\|\s+tstats", query))

    def parse(self, raw_query_container: RawQueryContainer) -> TokenizedQueryContainer:
        if self.__is_tstats_query(raw_query_container.query):
            return self.platform_functions.parse_tstats_func(raw_query_container)

        query, log_sources, functions = self._parse_query(raw_query_container.query)
        query_tokens = self.get_query_tokens(query)
        query_field_tokens, function_field_tokens, function_field_tokens_map = self.get_field_tokens(
            query_tokens, functions.functions
        )
        source_mappings = self.get_source_mappings(query_field_tokens + function_field_tokens, log_sources)
        meta_info = raw_query_container.meta_info
        meta_info.query_fields = query_field_tokens
        meta_info.function_fields = function_field_tokens
        meta_info.function_fields_map = function_field_tokens_map
        meta_info.source_mapping_ids = [source_mapping.source_id for source_mapping in source_mappings]
        return TokenizedQueryContainer(tokens=query_tokens, meta_info=meta_info, functions=functions)
