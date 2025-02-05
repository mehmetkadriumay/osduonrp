# Install Process

!!! example "CI Butler is in Development"

    CI Butler is in development and this process will be improved in the near future to support the full Community Implementation.

    - This is a high-level map, some details have been left out.
    - More work needs to be done to fully support CImpl.

Currently the high-level process once you start the `cibutler install` command the following happens:

``` mermaid
graph TD
  0(cibutler install) --> 1(Determine CPU Architecture);
  1 --> |Deploy on Minikube with Docker Driver| A;
  1 --> |Deploy on Kubernetes with Docker Desktop| C;
  A[Configure Minikube] --> B[Start Minikube in Docker];
  B --> C[Deploy Istio];
  C --> D[Deploy CImpl];
  D --> E((Wait));
  E --> |Check| G(Is CImpl Installed and Running?);
  G --> |Correctable Errors Found| 9[Apply minor automation corrections];
  9 --> E;
  G --> |Running| H[Update Kubernetes Services];
  G --> |Not Yet| E;
  H --> I[Install Notebook - optional];
  I --> J[Import Reference Data Process into OSDU optional];
  J --> X(( ));
```