"""Unittests for the AllTlds Agent."""

import dns.resolver
from ostorlab.agent.message import message
from pytest_mock import plugin


def testAgentAllTldsAgent_whenDomainSeenForFirstTime_emitsAllAllTlds(
    all_tlds_agent, agent_mock, agent_persist_mock, mocker: plugin.MockerFixture
):
    """Unittest for emitting all possible TLD for a known domain."""
    mocker.patch("dns.resolver.Resolver.resolve", return_value=mocker.MagicMock())
    msg = message.Message.from_data(
        selector="v3.asset.domain_name", data={"name": "somedomain.com"}
    )
    all_tlds_agent.process(msg)

    assert len(agent_mock) > 100
    assert "somedomain.co" in (a.data.get("name") for a in agent_mock)


def testAgentAllTldsAgent_whenTLDHasStart_isNotIncluded(
    all_tlds_agent, agent_mock, agent_persist_mock, mocker: plugin.MockerFixture
):
    """Unittest for emitting all possible TLD for a known domain."""
    mocker.patch("dns.resolver.Resolver.resolve", return_value=mocker.MagicMock())
    msg = message.Message.from_data(
        selector="v3.asset.domain_name", data={"name": "somedomain.com"}
    )
    all_tlds_agent.process(msg)

    assert len(agent_mock) > 100
    assert "somedomain.mm" not in (a.data.get("name") for a in agent_mock)


def testAgentAllTldsAgent_whenDomainSeenForASecondTime_emitsNothing(
    all_tlds_agent, agent_mock, agent_persist_mock, mocker: plugin.MockerFixture
):
    """Unittest for ensuring a domain is processed only once."""
    mocker.patch("dns.resolver.Resolver.resolve", return_value=mocker.MagicMock())
    msg = message.Message.from_data(
        selector="v3.asset.domain_name", data={"name": "somedomain.com"}
    )
    all_tlds_agent.process(msg)
    previously_sent = len(agent_mock)
    all_tlds_agent.process(msg)
    assert len(agent_mock) - previously_sent == 0


def testAgentAllTldsAgent_whenAllTheGeneratedMessage_emitsNothingInfinite(
    all_tlds_agent, agent_mock, agent_persist_mock, mocker: plugin.MockerFixture
):
    """Unittest for ensuring a domain do not generate non ending TLD combinations."""
    mocker.patch("dns.resolver.Resolver.resolve", return_value=mocker.MagicMock())
    msg = message.Message.from_data(
        selector="v3.asset.domain_name", data={"name": "somedomain.com"}
    )
    all_tlds_agent.process(msg)
    previously_sent = len(agent_mock)
    for emitted_message in agent_mock:
        all_tlds_agent.process(emitted_message)

    assert len(agent_mock) - previously_sent == 0


def testAgentAllTldsAgent_whenDomainHasNoTLD_emitsNothing(
    all_tlds_agent, agent_mock, agent_persist_mock
):
    """Unittest for ensuring a domain is processed only once."""
    msg = message.Message.from_data(
        selector="v3.asset.domain_name", data={"name": "localhost"}
    )

    all_tlds_agent.process(msg)

    assert len(agent_mock) == 0


def testAgentAllTldsAgent_whenVariantsDoNotExist_emitsNothing(
    all_tlds_agent, agent_mock, agent_persist_mock, mocker: plugin.MockerFixture
):
    """A variant whose NS query returns NXDOMAIN is not registered, so it is not emitted."""
    resolve_mock = mocker.patch(
        "dns.resolver.Resolver.resolve", side_effect=dns.resolver.NXDOMAIN()
    )
    msg = message.Message.from_data(
        selector="v3.asset.domain_name", data={"name": "somedomain.com"}
    )

    all_tlds_agent.process(msg)

    assert len(agent_mock) == 0
    assert resolve_mock.call_count > 100
    assert (
        mocker.call(qname="somedomain.co", rdtype="NS") in resolve_mock.call_args_list
    )


def testAgentAllTldsAgent_whenOnlyOneVariantIsRegistered_emitsOnlyIt(
    all_tlds_agent, agent_mock, agent_persist_mock, mocker: plugin.MockerFixture
):
    """Only the variants that DNS knows are emitted."""
    mocker.patch(
        "dns.resolver.Resolver.resolve",
        side_effect=[mocker.MagicMock()] + [dns.resolver.NXDOMAIN()] * 5000,
    )
    msg = message.Message.from_data(
        selector="v3.asset.domain_name", data={"name": "somedomain.com"}
    )

    all_tlds_agent.process(msg)

    assert len(agent_mock) == 1


def testAgentAllTldsAgent_whenVariantExistsWithoutNsRecords_emitsIt(
    all_tlds_agent, agent_mock, agent_persist_mock, mocker: plugin.MockerFixture
):
    """A name that exists without its own NS records (NoAnswer) is not proven unregistered."""
    mocker.patch("dns.resolver.Resolver.resolve", side_effect=dns.resolver.NoAnswer())
    msg = message.Message.from_data(
        selector="v3.asset.domain_name", data={"name": "somedomain.com"}
    )

    all_tlds_agent.process(msg)

    assert len(agent_mock) > 100
    assert "somedomain.co" in (a.data.get("name") for a in agent_mock)


def testAgentAllTldsAgent_whenRegistrationCheckTimesOut_emitsTheVariant(
    all_tlds_agent, agent_mock, agent_persist_mock, mocker: plugin.MockerFixture
):
    """A timed-out check says nothing about the registration, so the variant is kept."""
    mocker.patch(
        "dns.resolver.Resolver.resolve", side_effect=dns.resolver.LifetimeTimeout()
    )
    msg = message.Message.from_data(
        selector="v3.asset.domain_name", data={"name": "somedomain.com"}
    )

    all_tlds_agent.process(msg)

    assert len(agent_mock) > 100
    assert "somedomain.co" in (a.data.get("name") for a in agent_mock)


def testAgentAllTldsAgent_whenCheckingRegistration_queriesPublicResolvers(
    all_tlds_agent, agent_mock, agent_persist_mock, mocker: plugin.MockerFixture
):
    """The check does not depend on the host's resolver, which can be too slow."""
    resolve_mock = mocker.patch.object(
        dns.resolver.Resolver,
        "resolve",
        autospec=True,
        side_effect=dns.resolver.NXDOMAIN(),
    )
    msg = message.Message.from_data(
        selector="v3.asset.domain_name", data={"name": "somedomain.com"}
    )

    all_tlds_agent.process(msg)

    resolver = resolve_mock.call_args.args[0]
    assert resolver.nameservers == ["8.8.8.8", "1.1.1.1"]
