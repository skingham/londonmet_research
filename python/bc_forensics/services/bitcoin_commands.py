# -*- coding: utf-8 -*-
"""

@package bc_forensics.service
"""

import datetime
import json
import logging
import numbers
import random
from abc import ABC, abstractmethod
from functools import reduce
from typing import List, Optional, Union


logger = logging.getLogger(__name__)


class BitcoinRpcException(Exception):
    pass


class BitcoinCommand(ABC):

    def __init__(self, api_dispatcher):
        self._id = random.randint(1, 999999)
        self._api_dispatcher = api_dispatcher
        self._msg = ''

    async def _rpc(self) -> Union[list, dict, str, float, int, None]:
        logger.info(f"BitcoinCommand._call_api: {self._msg}")

        response_or_exception = await self._api_dispatcher.send(self._msg)
        if isinstance(response_or_exception, Exception):
            msg = str(response_or_exception)
            logger.error(f"{self.__class__.__name__}._call_api(): {msg}")
            raise BitcoinRpcException(f"{msg}")

        assert isinstance(response_or_exception, deribit_v2.Response)
        # Any logging for response id, jsonrpc, testnet, usDidd, usIn, usOut here
        if response_or_exception.error:
            msg = str(response_or_exception.error)
            logger.error(f"{self.__class__.__name__}._call_api(): {msg}")
            raise BitcoinRpcException(msg)
        return response_or_exception.result

    @abstractmethod
    async def invoke(self) -> Union[dict, list, float, int]:
        pass

    @property
    def json(self) -> str:
        return json.dumps(self._msg.model_dump())

    @property
    def request(self) -> deribit_v2.Request:
        return self._msg