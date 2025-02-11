# Project Details

## Key resources and contact points

- **Lead:** Shane Hutchins, [ICS]
- **Status:** Experimental
- **Homepage:** [https://osdu.pages.opengroup.org/ui/cibutler/](https://osdu.pages.opengroup.org/ui/cibutler/)
- **Charter:** N/A
- **Documentation:** [Doc](https://osdu.pages.opengroup.org/ui/cibutler/)
- **Backlog:** 
- **Slack Channel:** [pmc-community-infrastructure](https://og.enterprise.slack.com/archives/C07SDCNAMR9)
- **Meeting Schedule:** N/A

## Background

Build automation for installing and configuring CImpl locally.

### Objectives

### Planned Deliverables

- [x] Installable/packaged utility
- [x] Add scanning to pipeline
- [x] Pages documentation
- [x] Install OSDU
- [x] Automation to add clients
- [x] Automation to add users
- [x] Automation to add users to groups
- [ ] Install Official CImpl helm charts and images
- [ ] Allow different size deployments - support smaller deployments (less services and smaller memory requests) 

#### Long Term Plan

- Install individual CImpl service packages/charts
- Allow configuration of each service - tshirt sizing for services (think replicas, memory and cpu requests). This is an often requested feature - however setting artificially lower memory requests could potentially allow single user development & test environments for developers with smaller amounts of RAM at the potential cost of stability and availability. Configurability in automation and extensive testing will be needed in the future.
- Provide more automation for pipeline usage
- Automated testing
- Support more than just minikube and Docker Desktop

## Status

!!! warning "Experimental"

    CI Butler is in development and should be considered experimental. Please report any issues.

    **Last updated:** {{ git_revision_date }}

## Support needed

- Looking for testers on Mac, Linux and Windows
- Feedback on features and backlog/objectives

### Required skillsets

- Familiarity with OSDU

### What can new joiners get involved in?

- Help test

### What are the gaps?

- to be determined

## Useful links & Reference information

- [https://osdu.pages.opengroup.org/ui/cibutler/project/](https://osdu.pages.opengroup.org/ui/cibutler/)
