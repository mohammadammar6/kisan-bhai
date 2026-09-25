# Cloudflare Tunnel, Ingress, and HTTPS

This setup routes `kisanbhai.shop` and `www.kisanbhai.shop` through Cloudflare Tunnel to the in-cluster NGINX ingress controller. cert-manager obtains a publicly trusted Let's Encrypt certificate using Cloudflare DNS-01 validation. No inbound router ports or public IP are required.

> For the Argo CD deployment, Cloudflare credentials are rendered from Vault. Follow [README-argocd-vault.md](README-argocd-vault.md) to store them and sync the app. Don't create a competing Cloudflare Secret with `kubectl` when Argo CD manages the application.

## Install the controllers

Run these against the intended kind cluster. The kind-specific ingress-nginx manifest installs the controller and its admission webhook:

```sh
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.15.1/deploy/static/provider/kind/deploy.yaml
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.21.2/cert-manager.yaml
kubectl wait --for=condition=Available deployment/ingress-nginx-controller -n ingress-nginx --timeout=180s
kubectl wait --for=condition=Available deployment/cert-manager -n cert-manager --timeout=180s
kubectl wait --for=condition=Available deployment/cert-manager-webhook -n cert-manager --timeout=180s
```

For DNS-01 self-checks, make cert-manager use public recursive resolvers instead of the kind cluster's CoreDNS forwarder. This avoids failures when the host network's DNS resolver returns `SERVFAIL` for the domain's SOA lookup:

```sh
kubectl -n cert-manager patch deployment cert-manager --type=json -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--dns01-recursive-nameservers=1.1.1.1:53,8.8.8.8:53"},{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--dns01-recursive-nameservers-only"}]'
kubectl -n cert-manager rollout status deployment/cert-manager --timeout=120s
```

These flags are included in the cert-manager controller arguments. Reapply them if you reinstall cert-manager from the upstream manifest.

## Configure certificate issuance

Create a Cloudflare API Token limited to the `kisanbhai.shop` zone, with `Zone / DNS / Edit` and `Zone / Zone / Read` permissions. Keep this token private. Create the Kubernetes Secret without writing it to a tracked YAML file:

```sh
read -s CLOUDFLARE_API_TOKEN
kubectl create secret generic cloudflare-api-token \
  --namespace cert-manager \
  --from-literal=api-token="$CLOUDFLARE_API_TOKEN"
unset CLOUDFLARE_API_TOKEN
```

Edit `cloudflare-issuer.yaml` and replace `REPLACE_WITH_YOUR_EMAIL`, then apply it:

```sh
kubectl apply -f k8s/manifests/cloudflare-issuer.yaml
```

## Deploy the app and Ingress

Apply the app's database Secret first, then deploy the existing app stack and ingress:

```sh
kubectl apply -f k8s/manifests/secret.yaml
kubectl apply -f k8s/manifests/mysql-kisan-bhai.yaml
kubectl apply -f k8s/manifests/redis-kisan-bhai.yaml
kubectl apply -f k8s/manifests/app-kisan-bhai.yaml
kubectl apply -f k8s/manifests/ingress.yaml
```

Check certificate progress with `kubectl describe certificate kisanbhai-shop-tls -n kisan-bhai` and `kubectl get challenges -A`. The Ingress requests a certificate for both the apex and `www` hostname.

## Connect the Cloudflare Tunnel

In Cloudflare Zero Trust, create a remotely managed Tunnel. Under its Public Hostnames, add both `kisanbhai.shop` and `www.kisanbhai.shop` and route each to:

```text
https://ingress-nginx-controller.ingress-nginx.svc.cluster.local:443
```

For the origin TLS settings, set **Origin Server Name** to `kisanbhai.shop` and keep certificate verification enabled. The certificate served by the Ingress covers both requested hostnames. In Cloudflare DNS, the tunnel setup should create proxied CNAME records for both hostnames; remove conflicting A/AAAA records. At the registrar, use the Cloudflare nameservers for the domain.

Create the tunnel connector token Secret and deploy two `cloudflared` replicas:

```sh
kubectl create namespace cloudflare-tunnel
read -s CLOUDFLARE_TUNNEL_TOKEN
kubectl create secret generic cloudflared \
  --namespace cloudflare-tunnel \
  --from-literal=TUNNEL_TOKEN="$CLOUDFLARE_TUNNEL_TOKEN"
unset CLOUDFLARE_TUNNEL_TOKEN
kubectl apply -f k8s/manifests/cloudflared.example.yaml
```

The example file contains only a Namespace and Deployment; it does not replace the real token Secret. Do not commit the real tunnel token.

Once the certificate is `Ready=True`, use Cloudflare SSL/TLS mode **Full (strict)**. Tunnel encrypts the connector path, while the Ingress certificate provides verified TLS at the origin.

## Check status

```sh
kubectl get pods -n ingress-nginx
kubectl get pods -n cert-manager
kubectl get pods -n cloudflare-tunnel
kubectl get ingress,certificate -n kisan-bhai
```
