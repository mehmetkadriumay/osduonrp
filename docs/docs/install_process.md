# Install Process

!!! example "CI Butler is in Development"

    CI Butler is in development and this process is likely to be improved in the near future.

The high-level process once you start the `cibutler install` command the following happens:

``` mermaid
graph TD
  A[Configure Minikube] --> B[Start Minikube in Docker];
  B --> C[Deploy istio];
  C --> D[Deploy CImpl];
  D --> E[Wait];
  E --> |Check| G[Is CImpl Installed and Running?];
  G --> |Running| H[Update Kubernetes Services];
  G --> |Not Yet| E;
  H --> I[Install Notebook - optional];
  I --> J[Import Reference Data into OSDU - optional];
```