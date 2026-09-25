# Vault-backed Argo CD deployment (kind)

This guide uses HashiCorp Vault KV v2 and Argo CD Vault Plugin (AVP). Argo CD renders the YAML in `k8s/manifests`, replaces the AVP placeholders from Vault, and applies the resulting Kubernetes Secrets. Application and Cloudflare credentials stay out of Git.

## Cluster components

Vault and Argo CD have been installed in the current `kind-kind` cluster. The Vault release uses the `standard` local-path StorageClass and a 2 GiB persistent volume. Argo CD is v3.5.3; the AVP sidecar is attached to `argocd-repo-server` using the files in `k8s/argocd/`.

Check their status:

```sh
kubectl get pods -n vault
kubectl get pvc -n vault
kubectl get pods -n argocd
```

Vault starts sealed. Initialize and unseal it before Argo CD tries to render the application. For this local kind setup, Vault's chart has TLS disabled on its **internal-only** service; don't reuse these values for a production cluster. The standalone Vault instance must be manually unsealed after a restart.

## Initialize and unlock Vault

Install the Vault CLI (`brew install vault` on macOS), then start a port-forward in one terminal:

```sh
kubectl port-forward -n vault service/vault 8200:8200
```

In a second terminal, initialize Vault once. Save all three unseal keys and the initial root token in a password manager or other secure offline storage. Never commit or paste them into a manifest.

```sh
export VAULT_ADDR=http://127.0.0.1:8200
vault operator init -key-shares=3 -key-threshold=2
```

Unseal with two different keys (run the command twice and enter one key each time), then log in with the initial root token:

```sh
vault operator unseal
vault operator unseal
vault login
```

The `vault-init.json` path is ignored by Git as an extra safeguard, but storing unseal keys in the workspace is discouraged. Keep the durable backup outside the repository.

## Configure Vault access for the Argo CD plugin

Enable KV v2 and Kubernetes authentication, create a policy limited to this app's secrets, and bind it only to the Argo CD repo-server ServiceAccount:

```sh
vault secrets enable -path=secret kv-v2
vault auth enable kubernetes
vault write auth/kubernetes/config kubernetes_host=https://kubernetes.default.svc:443
vault policy write argocd-kisan-bhai-read - <<'EOF'
path "secret/data/kisan-bhai/*" {
  capabilities = ["read"]
}
EOF
vault write auth/kubernetes/role/argocd-repo-server \
  bound_service_account_names=argocd-repo-server \
  bound_service_account_namespaces=argocd \
  policies=argocd-kisan-bhai-read \
  ttl=1h
```

The `vault-auth-delegator` ClusterRoleBinding grants Vault permission to validate the plugin's Kubernetes ServiceAccount token through the TokenReview API.

## Put the values into Vault

Keep the current database username and passwords so they still match the already-initialized MySQL PVC. This copies the existing Kubernetes Secret values into the Vault app path without printing them:

```sh
for key in MYSQL_DATABASE MYSQL_USER MYSQL_PASSWORD MYSQL_ROOT_PASSWORD SECRET_KEY OPENWEATHER_API_KEY; do
  value="$(kubectl -n kisan-bhai get secret kisan-bhai-secrets -o "jsonpath={.data.${key}}" | base64 -D)"
  export "$key=$value"
done

vault kv put secret/kisan-bhai/app \
  MYSQL_DATABASE="$MYSQL_DATABASE" \
  MYSQL_USER="$MYSQL_USER" \
  MYSQL_PASSWORD="$MYSQL_PASSWORD" \
  MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD" \
  SECRET_KEY="$SECRET_KEY" \
  OPENWEATHER_API_KEY="$OPENWEATHER_API_KEY"

unset MYSQL_DATABASE MYSQL_USER MYSQL_PASSWORD MYSQL_ROOT_PASSWORD SECRET_KEY OPENWEATHER_API_KEY value
```

The Tunnel token was found in a local example file, so revoke/rotate it in Cloudflare before using it again. Create a replacement Cloudflare API token limited to the `kisanbhai.shop` zone with `Zone / DNS / Edit` and `Zone / Zone / Read` permissions. Then store the replacement token, the email used for Let's Encrypt, and the new Tunnel token in Vault:

```sh
read -s CLOUDFLARE_API_TOKEN
read ACME_EMAIL
vault kv put secret/kisan-bhai/cloudflare \
  api-token="$CLOUDFLARE_API_TOKEN" email="$ACME_EMAIL"
unset CLOUDFLARE_API_TOKEN ACME_EMAIL

read -s CLOUDFLARE_TUNNEL_TOKEN
vault kv put secret/kisan-bhai/cloudflared TUNNEL_TOKEN="$CLOUDFLARE_TUNNEL_TOKEN"
unset CLOUDFLARE_TUNNEL_TOKEN
```

AVP reads these three paths using the placeholders in `k8s/manifests/vault-secrets.yaml`. The Vault policy intentionally grants read access only to `secret/data/kisan-bhai/*`.

## Configure and sync the Argo CD Application

The Application at `k8s/argocd/application.yaml` points to the current Git remote (`master`, `k8s/manifests`). The source branch must contain these new files before Argo CD can see them. Review and push the changes:

```sh
git status --short
git add .gitignore k8s
git commit -m "Add Vault-backed Argo CD deployment"
git push origin master
```

Then create the Argo CD Application. Automated sync and self-heal are enabled in its manifest:

```sh
kubectl apply -f k8s/argocd/application.yaml
kubectl get applications -n argocd
kubectl describe application kisan-bhai -n argocd
```

If the GitHub repository is private, add repository credentials to Argo CD before creating the Application. The current plugin patch and ConfigMap can be reapplied with:

```sh
kubectl apply -f k8s/argocd/cmp-plugin.yaml
kubectl patch deployment argocd-repo-server -n argocd \
  --type=strategic --patch-file k8s/argocd/repo-server-patch.yaml
```

Use the Argo CD UI locally with `kubectl port-forward -n argocd service/argocd-server 8080:443`. Retrieve the initial admin password with:

```sh
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -D; echo
```

## Cloudflare token hygiene

Only the placeholder remains in `k8s/examples/cloudflare-api-token.example.yaml`. If the exposed token was already committed or used, revoke it in Cloudflare and replace the Tunnel token as well. AVP creates the Kubernetes Secrets from Vault when Argo CD syncs; don't apply the example files or local `secret.yaml` to the cluster through Argo CD.
