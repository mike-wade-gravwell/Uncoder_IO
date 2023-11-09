"""
Uncoder IO Commercial Edition License
-----------------------------------------------------------------
Copyright (c) 2023 SOC Prime, Inc.

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
from typing import List, Tuple, Dict

from app.converter.backends.opensearch.const import opensearch_query_details
from app.converter.backends.opensearch.mapping import OpenSearchMappings, opensearch_mappings
from app.converter.backends.opensearch.tokenizer import OpenSearchTokenizer
from app.converter.core.models.platform_details import PlatformDetails
from app.converter.core.parser import Parser
from app.converter.core.operator_types.output import SiemContainer, MetaInfoContainer


class OpenSearchParser(Parser):
    details: PlatformDetails = opensearch_query_details
    mappings: OpenSearchMappings = opensearch_mappings
    tokenizer = OpenSearchTokenizer()

    log_source_pattern = r"___source_type___\s*(:|=)\s*(?:\"?(?P<d_q_value>[%a-zA-Z_*:0-9\-/]+)\"|(?P<value>[%a-zA-Z_*:0-9\-/]+))(?:\s+(?:and|or)\s+|\s+)?"
    log_source_key_types = ("index", "event\.category")

    def _parse_log_sources(self, query: str) -> Tuple[str, Dict[str, List[str]]]:
        log_sources = {}
        for source_type in self.log_source_key_types:
            pattern = self.log_source_pattern.replace('___source_type___', source_type)
            while search := re.search(pattern, query, flags=re.IGNORECASE):
                value = search.group(1)
                log_sources.setdefault(source_type, []).append(value)
                pos_start = search.start()
                pos_end = search.end()
                query = query[:pos_start] + query[pos_end:]

        return query, log_sources

    @staticmethod
    def _get_meta_info(source_mapping_ids: List[str], meta_info: dict) -> MetaInfoContainer:
        return MetaInfoContainer(source_mapping_ids=source_mapping_ids)

    def _parse_query(self, query: str) -> Tuple[str, Dict[str, List[str]]]:
        return self._parse_log_sources(query)

    def parse(self, text: str) -> SiemContainer:
        query, log_sources = self._parse_query(text)
        tokens, source_mappings = self.get_tokens_and_source_mappings(query, log_sources)
        return SiemContainer(
            query=tokens,
            meta_info=self._get_meta_info([source_mapping.source_id for source_mapping in source_mappings], {}),
        )