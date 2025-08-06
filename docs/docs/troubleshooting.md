# Troubleshooting

Things to try when CI Butler installs fail:

* Reset your kubernetes cluster (sometimes docker desktop gets confused) - this is especially true if install is taking a long time.
* Restart docker desktop
* Reboot
* Take defaults when installing
* Try a different version of OSDU/Helm Version/Chart
* Built in diagnostic tools `cibutler diag --help` for repairing or investigating
* Try purging docker containers, images, volumes and networks `cibutler diag purge`
* Package diagnostic logs `cibutler diag package` for sending to support team
* kubernetes commands on failed pods, etc. `kubectl logs <pod>` and `kubectl describe po/<pod>`

Reach out to community for support:
- **Slack Channel:** [cap-cibutler](https://og.enterprise.slack.com/archives/C096DM26UHW)