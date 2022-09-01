"""Unittests for the AllTlds Agent."""

from ostorlab.agent.message import message


def testAgentAllTldsAgent_whenDomainSeenForFirstTime_emitsAllAllTlds(all_tlds_agent, agent_mock, agent_persist_mock):
    """Unittest for emitting all possible TLD for a known domain."""
    msg = message.Message.from_data(selector='v3.asset.domain_name', data={'name': 'somedomain.com'})
    all_tlds_agent.process(msg)

    assert len(agent_mock) > 100
    assert 'somedomain.co' in (a.data.get('name') for a in agent_mock)


def testAgentAllTldsAgent_whenTLDHasStart_isNotIncluded(all_tlds_agent, agent_mock, agent_persist_mock):
    """Unittest for emitting all possible TLD for a known domain."""
    msg = message.Message.from_data(selector='v3.asset.domain_name', data={'name': 'somedomain.com'})
    all_tlds_agent.process(msg)

    assert len(agent_mock) > 100
    assert 'somedomain.mm' not in (a.data.get('name') for a in agent_mock)


def testAgentAllTldsAgent_whenDomainSeenForASecondTime_emitsNothing(all_tlds_agent, agent_mock, agent_persist_mock):
    """Unittest for ensuring a domain is processed only once."""
    msg = message.Message.from_data(selector='v3.asset.domain_name', data={'name': 'somedomain.com'})
    all_tlds_agent.process(msg)
    previously_sent = len(agent_mock)
    all_tlds_agent.process(msg)
    assert len(agent_mock) - previously_sent == 0


def testAgentAllTldsAgent_whenAllTheGeneratedMessage_emitsNothingInfinite(
        all_tlds_agent, agent_mock, agent_persist_mock):
    """Unittest for ensuring a domain do not generated non ending TLD combinations."""
    msg = message.Message.from_data(selector='v3.asset.domain_name', data={'name': 'somedomain.com'})
    all_tlds_agent.process(msg)
    previously_sent = len(agent_mock)
    for emitted_message in agent_mock:
        all_tlds_agent.process(emitted_message)
    assert len(agent_mock) - previously_sent == 0
