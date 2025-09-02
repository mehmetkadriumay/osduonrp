import logging
import cibutler.cihelm as cihelm
from cibutler.shell import run_shell_command
from cibutler.common import console, error_console

logger = logging.getLogger(__name__)


def check_istio():
    """
    Check if istio is installed
    """
    helms = ["istio-base", "istio-ingress", "istiod"]
    for chart in helms:
        if cihelm.helm_query(chart):
            console.print(f":warning: {chart} already installed")
            logger.info(f"{chart} already installed")
        else:
            console.print(f"{chart} not yet installed")
            return False
    return True


def install_istio(
    repo: str = "https://istio-release.storage.googleapis.com/charts",
    namespace: str = "istio-system",
):
    """
    Install istio
    """
    console.print(f":pushpin: Adding helm repo {repo}")
    run_shell_command(f"helm repo add istio {repo}")  # nosec
    run_shell_command("helm repo update")  # nosec

    run_shell_command(
        f"helm upgrade --install istio-base istio/base --create-namespace -n {namespace}",
    )
    run_shell_command(f"helm upgrade --install istiod istio/istiod -n {namespace}")
    run_shell_command(
        f"helm upgrade --install istio-ingress istio/gateway -n {namespace} --set labels.istio=ingressgateway --skip-schema-validation"
    )

    if check_istio():
        console.print(
            ":surfer: Done! Istio is now installed in kubernetes cluster. Ready to deploy CImpl OSDU"
        )
        return True
    else:
        error_console.print("There may have been an issue with istio")
        return False
