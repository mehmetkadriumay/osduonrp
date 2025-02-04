from subprocess import call
from rich.console import Console
import cibutler.cihelm as cihelm

console = Console()
error_console = Console(stderr=True, style="bold red")


def check_istio():
    helms = ["istio-base", "istio-ingress", "istiod"]
    for chart in helms:
        if cihelm.helm_query(chart):
            console.print(f":thumbs_up: {chart} installed")
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
    call(
        f"helm repo add istio {repo}",
        shell=True,
    )
    call("helm repo update", shell=True)
    call(
        f"helm upgrade --install istio-base istio/base --create-namespace -n {namespace}",
        shell=True,
    )
    call(f"helm upgrade --install istiod istio/istiod -n {namespace}", shell=True)
    call(
        f"helm upgrade --install istio-ingress istio/gateway -n {namespace} --set labels.istio=ingressgateway",
        shell=True,
    )
    if check_istio():
        console.print(
            ":surfer: Done! Istio is now installed in kubernetes cluster. Ready to deploy CImpl OSDU"
        )
        return True
    else:
        error_console.print("There may have been an issue with istio")
        return False
