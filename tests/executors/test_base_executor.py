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
from datetime import timedelta
from unittest import mock

from airflow.executors.base_executor import BaseExecutor
from airflow.models.baseoperator import BaseOperator
from airflow.models.taskinstance import TaskInstanceKey
from airflow.utils import timezone
from airflow.utils.state import State


def test_get_event_buffer():
    executor = BaseExecutor()

    date = timezone.utcnow()
    try_number = 1
    key1 = TaskInstanceKey("my_dag1", "my_task1", date, try_number)
    key2 = TaskInstanceKey("my_dag2", "my_task1", date, try_number)
    key3 = TaskInstanceKey("my_dag2", "my_task2", date, try_number)
    state = State.SUCCESS
    executor.event_buffer[key1] = state, None
    executor.event_buffer[key2] = state, None
    executor.event_buffer[key3] = state, None

    assert len(executor.get_event_buffer(("my_dag1",))) == 1
    assert len(executor.get_event_buffer()) == 2
    assert len(executor.event_buffer) == 0


@mock.patch('airflow.executors.base_executor.BaseExecutor.sync')
@mock.patch('airflow.executors.base_executor.BaseExecutor.trigger_tasks')
@mock.patch('airflow.executors.base_executor.Stats.gauge')
def test_gauge_executor_metrics(mock_stats_gauge, mock_trigger_tasks, mock_sync):
    executor = BaseExecutor()
    executor.heartbeat()
    calls = [
        mock.call('executor.open_slots', mock.ANY),
        mock.call('executor.queued_tasks', mock.ANY),
        mock.call('executor.running_tasks', mock.ANY),
    ]
    mock_stats_gauge.assert_has_calls(calls)


def test_try_adopt_task_instances(dag_maker):
    date = timezone.utcnow()
    start_date = date - timedelta(days=2)

    with dag_maker("test_try_adopt_task_instances"):
        BaseOperator(task_id="task_1", start_date=start_date)
        BaseOperator(task_id="task_2", start_date=start_date)
        BaseOperator(task_id="task_3", start_date=start_date)

    dagrun = dag_maker.create_dagrun(execution_date=date)
    tis = dagrun.task_instances

    assert [ti.task_id for ti in tis] == ["task_1", "task_2", "task_3"]
    assert BaseExecutor().try_adopt_task_instances(tis) == tis
