# Troubleshooting

Things to try when CI Butler installs fail:

* Reset your kubernetes cluster (sometimes docker desktop gets confused) - this is especially true if install is taking a long time.
* Restart docker desktop
* Reboot
* Take defaults when installing
* Try a different version of OSDU/Helm Version/Chart
* Built in diagnostic tools `cibutler diag --help` for repairing or investigating
* Try purging docker containers, images, volumes and networks `cibutler diag purge`
* Package diagnostic logs `cibutler diag inspect` for sending to support team
* kubernetes commands on failed pods, etc. `kubectl logs <pod>` and `kubectl describe po/<pod>`

Reach out to community for support:
- **Slack Channel:** [cap-cibutler](https://og.enterprise.slack.com/archives/C096DM26UHW)


!!! question "Additional Documentation is Available"
    **CI Butler has great built-in help**:

     - `cibutler --help` for overall help
     - `cibutler command --help` for help on a individual command
     - `cibutler diag --help` for help on a diagnostic commands
     - `cibutler diag command --help` for help on a individual diagnostic commands

    There is also a command feference on all the commands and options:

    - See [Command Reference](./commands_reference.md).