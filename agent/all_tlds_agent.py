"""All TLDs agent implementation"""

import logging
from collections.abc import Iterator
from concurrent import futures

import tld
from dns import exception as dns_exception
from dns import resolver as dns_resolver
from ostorlab.agent import agent
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent.message import message as m
from ostorlab.agent.mixins import agent_persist_mixin
from ostorlab.runtimes import definitions as runtime_definitions
from rich import logging as rich_logging

logging.basicConfig(
    format="%(message)s",
    datefmt="[%X]",
    level="INFO",
    force=True,
    handlers=[rich_logging.RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)

STORAGE_NAME = "agent_all_tlds_storage"
MAX_CONCURRENT_DNS_QUERIES = 20
DNS_QUERY_TIMEOUT_SECONDS = 5.0


class AllTldsAgent(agent.Agent, agent_persist_mixin.AgentPersistMixin):
    """All TLDs agent."""

    def __init__(
        self,
        agent_definition: agent_definitions.AgentDefinition,
        agent_settings: runtime_definitions.AgentSettings,
    ) -> None:
        agent.Agent.__init__(self, agent_definition, agent_settings)
        agent_persist_mixin.AgentPersistMixin.__init__(self, agent_settings)
        self._dns_resolvers: list[str] = self.args.get("dns_resolvers", [])

    def process(self, message: m.Message) -> None:
        """Generates all possible TLD iteration of a source domain.

        Args:
            message: Domain to process.

        Returns:
            None
        """
        name = message.data.get("name")
        if name is None:
            return

        logger.info("processing name %s", name)
        domain_tld = tld.get_tld(
            name, fix_protocol=True, as_object=True, fail_silently=True
        )
        if not isinstance(domain_tld, tld.Result):
            logger.warning("Failed to get TLD for: %s", name)
            return
        if self.set_add(STORAGE_NAME, domain_tld.domain) is False:
            return
        logger.info("generating tlds for %s", name)
        tlds = tld.get_tld_names()
        domain_names = [f"{domain_tld.domain}{t}" for t in _generate_tlds(tlds=tlds)]
        checker = RegistrationChecker(nameservers=self._dns_resolvers)
        with futures.ThreadPoolExecutor(
            max_workers=MAX_CONCURRENT_DNS_QUERIES
        ) as executor:
            checks = {
                domain_name: executor.submit(checker.is_registered, domain_name)
                for domain_name in domain_names
            }
        registrations = {
            domain_name: check.result() for domain_name, check in checks.items()
        }
        registered_names = [
            domain_name
            for domain_name, is_registered in registrations.items()
            if is_registered is True
        ]
        logger.info(
            "%d of %d tld variants of %s are registered",
            len(registered_names),
            len(domain_names),
            name,
        )
        for domain_name in registered_names:
            self.emit("v3.asset.domain_name", {"name": domain_name})


class RegistrationChecker:
    """Checks in DNS whether a domain name is registered."""

    def __init__(self, nameservers: list[str]) -> None:
        """Builds a resolver that only asks the given DNS servers.

        Args:
            nameservers: IP addresses of the DNS resolvers to ask.
        """
        self._resolver = dns_resolver.Resolver(configure=False)
        self._resolver.nameservers = nameservers
        self._resolver.lifetime = DNS_QUERY_TIMEOUT_SECONDS

    def is_registered(self, domain_name: str) -> bool:
        """Return False only when DNS says the domain does not exist (NXDOMAIN).

        Args:
            domain_name: Domain name to check.

        Returns:
            False if the domain does not exist, True otherwise.
        """
        try:
            self._resolver.resolve(qname=domain_name, rdtype="NS")
        except dns_resolver.NXDOMAIN:
            return False
        except dns_resolver.NoAnswer:
            return True
        except dns_exception.DNSException as e:
            logger.warning(
                "could not check the registration of %s, keeping it: %s",
                domain_name,
                e,
            )
            return True
        return True


def _generate_tlds(tlds) -> Iterator[str]:
    """Generates all TLDs iterations."""
    for root in tlds.values():
        node = root.root
        yield from _get_child_tlds("", node)


def _get_child_tlds(partial_tld, node) -> Iterator[str]:
    """Recursive implementation to compose TLDs with their children."""
    for c_tld, c_node in node.children.items():
        if c_tld == "*":
            # * TLD expect an extra string representing the TLD. This will not brute force them, so we ignore them.
            pass
        elif (
            c_node.children is not None
            and "*" in c_node.children
            or c_node.private is True
        ):
            pass
        else:
            new_tld = f".{c_tld}{partial_tld}"
            if c_node.leaf is True:
                yield new_tld
            else:
                yield from _get_child_tlds(new_tld, c_node)


if __name__ == "__main__":
    logger.info("starting agent ...")
    AllTldsAgent.main()
