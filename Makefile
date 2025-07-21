test:
	uv run pytest -v --junit-xml=unit_tests_report.xml tests/unit
	uv run pytest -v tests/integration

microk8s:
	uv run cibutler diag gcloud-instance-create 
	sleep 1
	uv run cibutler diag gcloud-config-ssh --accept-new
	uv run cibutler diag cloud-install-ubuntu-microk8s
	uv run cibutler diag cloud-install-cibutler --target microk8s