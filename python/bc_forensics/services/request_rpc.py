# -*- coding: utf-8 -*-
"""

@package bc_forensics.service
"""

import json
import logging
import requests
from typing import List, Optional, Union


logger = logging.getLogger(__name__)


def execute_bitcoin_rpc(
        rpc_json: dict,
        rpc_user: str,
        rpc_password: str,
        rpc_host: str = "localhost",
        rpc_port: int = 18443) -> dict:
    """ """
    url = f"http://{rpc_host}:{rpc_port}"
    headers = {'content-type': 'application/json'}

    try:
        response = requests.post(url, json=rpc_json, headers=headers, auth=(rpc_user, rpc_password))
        if response.status_code == 200:
            return response.json()
        else:
            return "Error: Unable to fetch block count"
    except requests.RequestException as e:
        return f"Error: {e}"
