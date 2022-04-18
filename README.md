<h1 align="center">Agent all_tlds</h1>

<p align="center">
<img src="https://img.shields.io/badge/License-Apache_2.0-brightgreen.svg">
<img src="https://img.shields.io/github/languages/top/ostorlab/agent_all_tlds">
<img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg">
</p>

_all_tlds agent is a subdomain discovery tool that discovers valid subdomains for websites._

<p align="center">
<img src="https://github.com/Ostorlab/agent_all_tlds/blob/main/images/logo.png" alt="agent-all_tlds" />
</p>

## Getting Started
The all_tlds Agent works collectively with other agents. Its job; from a domain name, discover all subdomains in a fast and efficient way, 
and pass its findings to other agents responsible for scanning the subdomains, for example, the [Nuclei agent](https://github.com/Ostorlab/agent_nuclei)


To perform your first scan, simply run the following command:

```shell
ostorlab scan run --install --agent agent/ostorlab/all_tlds --agent agent/ostorlab/nuclei domain-name your-domain.com
```

This command will download and install agents  `agent/ostorlab/all_tlds` & `agent/ostorlab/nuclei` and target the domain  `your-domain`.
Nuclei Agent will scan for <your-domain>, and waits for all subdomains found by the all_tlds Agent to performe other scans.
You can use any Agent expecting <v3.asset.domain_name> as an in-selector, like Nmap, OpenVas, etc.

For more information, please refer to the [Ostorlab Documentation](https://github.com/Ostorlab/ostorlab/blob/main/README.md)


## Usage

Agent all_tlds can be installed directly from the ostorlab agent store or built from this repository.

 ### Install directly from ostorlab agent store

 ```shell
 ostorlab agent install agent/ostorlab/all_tlds
 ```

### Build directly from the repository

 1. To build the all_tlds agent you need to have [ostorlab](https://pypi.org/project/ostorlab/) installed in your machine. If you have already installed ostorlab, you can skip this step.

```shell
pip3 install ostorlab
```

 2. Clone this repository.

```shell
git clone https://github.com/Ostorlab/agent_all_tlds.git && cd agent_all_tlds
```

 3. Build the agent image using ostorlab cli.

 ```shell
 ostortlab agent build --file=ostorlab.yaml
 ```
 You can pass the optional flag `--organization` to specify your organisation. The organization is empty by default.

 4. Run the agent using on of the following commands:
	 * If you did not specify an organization when building the image:
	  ```shell
	  ostorlab scan run --agent agent//all_tlds --agent agent//nuclei domain-name your-domain.com
	  ```
	 * If you specified an organization when building the image:
	  ```shell
	  ostorlab scan run --agent agent/[ORGANIZATION]/all_tlds --agent agent/[ORGANIZATION]/nuclei  domain-name your-domain.com


## License
[Apache](./LICENSE)
