#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from typing import Any, Dict, List, Optional, Union

from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.sensors.base import BaseSensorOperator


class S3PrefixSensor(BaseSensorOperator):
    """
    Waits for a prefix or all prefixes to exist. A prefix is the first part of a key,
    thus enabling checking of constructs similar to glob ``airfl*`` or
    SQL LIKE ``'airfl%'``. There is the possibility to precise a delimiter to
    indicate the hierarchy or keys, meaning that the match will stop at that
    delimiter. Current code accepts sane delimiters, i.e. characters that
    are NOT special characters in the Python regex engine.

    :param bucket_name: Name of the S3 bucket
    :type bucket_name: str
    :param prefix: The prefix being waited on. Relative path from bucket root level.
    :type prefix: str or list of str
    :param delimiter: The delimiter intended to show hierarchy.
        Defaults to '/'.
    :type delimiter: str
    :param aws_conn_id: a reference to the s3 connection
    :type aws_conn_id: str
    :param verify: Whether or not to verify SSL certificates for S3 connection.
        By default SSL certificates are verified.
        You can provide the following values:

        - ``False``: do not validate SSL certificates. SSL will still be used
                 (unless use_ssl is False), but SSL certificates will not be
                 verified.
        - ``path/to/cert/bundle.pem``: A filename of the CA cert bundle to uses.
                 You can specify this argument if you want to use a different
                 CA cert bundle than the one used by botocore.
    :type verify: bool or str
    """

    template_fields = ('prefix', 'bucket_name')

    def __init__(
        self,
        *,
        bucket_name: str,
        prefix: Union[str, List[str]],
        delimiter: str = '/',
        aws_conn_id: str = 'aws_default',
        verify: Optional[Union[str, bool]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        # Parse
        self.bucket_name = bucket_name
        self.prefix = [prefix] if isinstance(prefix, str) else prefix
        self.delimiter = delimiter
        self.aws_conn_id = aws_conn_id
        self.verify = verify
        self.hook: Optional[S3Hook] = None

    def poke(self, context: Dict[str, Any]):
        self.log.info('Poking for prefix : %s in bucket s3://%s', self.prefix, self.bucket_name)
        return all(self._check_for_prefix(prefix) for prefix in self.prefix)

    def get_hook(self) -> S3Hook:
        """Create and return an S3Hook"""
        if self.hook:
            return self.hook

        self.hook = S3Hook(aws_conn_id=self.aws_conn_id, verify=self.verify)
        return self.hook

    def _check_for_prefix(self, prefix: str) -> bool:
        return self.get_hook().check_for_prefix(
            prefix=prefix, delimiter=self.delimiter, bucket_name=self.bucket_name
        )
