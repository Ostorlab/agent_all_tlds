"""Pytest fixtures for the All TLDs agent"""
import random

import pytest
import pathlib

from ostorlab.agent import definitions as agent_definitions
from ostorlab.runtimes import definitions as runtime_definitions

from agent import all_tlds_agent


@pytest.fixture(scope="function", name="all_tlds_agent")
def all_tlds_agent_object():
    with (pathlib.Path(__file__).parent.parent / "ostorlab.yaml").open() as yaml_o:
        definition = agent_definitions.AgentDefinition.from_yaml(yaml_o)
        settings = runtime_definitions.AgentSettings(
            key="agent/ostorlab/all_tlds",
            bus_url="NA",
            bus_exchange_topic="NA",
            args=[],
            healthcheck_port=random.randint(5000, 6000),
            redis_url="redis://guest:guest@localhost:6379",
        )

        agent = all_tlds_agent.AllTldsAgent(definition, settings)
        return agent
