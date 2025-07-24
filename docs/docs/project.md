# Project Details

## Key resources and contact points

- **Lead:** Shane Hutchins, [ICS]
- **Status:** Experimental
- **Homepage:** [https://osdu.pages.opengroup.org/ui/cibutler/](https://osdu.pages.opengroup.org/ui/cibutler/)
- **Charter:** N/A
- **Documentation:** [Doc](https://osdu.pages.opengroup.org/ui/cibutler/)
- **Backlog:** 
- **Slack Channel:** [cap-cibutler](https://og.enterprise.slack.com/archives/C096DM26UHW)
- **Meeting Schedule:** N/A

## Background

CI Butler (or CIButler) is a user-friendly command-line interface (CLI) tool designed to simplify the local installation of OSDU. It serves as a convenient utility for development, automation, testing, and direct interaction with the OSDU platform.

CI Butler was developed by Shane Hutchins to streamline and accelerate the setup of the Community Implementation of OSDU, aiming to make the platform more accessible and efficient for contributors and developers.

### Objectives

### Planned Deliverables

- [x] Installable/packaged utility
- [x] Add scanning to pipeline
- [x] Pages documentation
- [x] Install OSDU
- [x] Automation to add clients
- [x] Automation to add users
- [x] Automation to add users to groups
- [x] M24 Support
- [x] M25 Support
- [x] [MicroK8s](https://microk8s.io/) Single Node Support
- [ ] [K3s](https://k3s.io/) (an official CNCF sandbox project) Support
- [ ] Cloud based Kubernetes Support (GKE)
- [ ] Add [Rocky Linux](https://rockylinux.org/) Support (currently only tested with [Ubuntu](https://ubuntu.com/))
- [ ] Install Official CImpl helm charts and images
- [ ] Allow different size deployments - support smaller deployments (less services and smaller memory requests) 

#### Long Term Plan

- Install individual CImpl service packages/charts
- Allow configuration of each service - tshirt sizing for services (think replicas, memory and cpu requests). This is an often requested feature - however setting artificially lower memory requests could potentially allow single user development & test environments for developers with smaller amounts of RAM at the potential cost of stability and availability. Configurability in automation and extensive testing will be needed in the future.
- Provide more automation for pipeline usage
- Automated testing
- Support more than just minikube and Docker Desktop
- Additional Cloud based Kubernetes Support (AKS, AWS, ...)

## Status

!!! warning "Experimental"

    CI Butler is currently under development and should be considered experimental. Please report any issues you encounter.

    **Last updated:** {{ git_revision_date }}

## Support Needed

- Looking for testers on Mac, Linux and Windows
- Feedback on features and backlog/objectives

### Required skill sets

- Familiarity with OSDU

### What can new joiners get involved in?

- Help test

### What are the gaps?

- to be determined

## Useful links & Reference information

- [https://osdu.pages.opengroup.org/ui/cibutler/project/](https://osdu.pages.opengroup.org/ui/cibutler/)
