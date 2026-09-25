# KISAN BHAI — Local Fixed Version

Flask + MySQL + Redis + OpenWeather farmer companion.

## Local macOS setup

1. Create the database/user:

```sql
CREATE DATABASE kisan_bhai;
CREATE USER 'kisan'@'localhost' IDENTIFIED BY 'Kisan@12345';
GRANT ALL PRIVILEGES ON kisan_bhai.* TO 'kisan'@'localhost';
FLUSH PRIVILEGES;
```

2. Start services:

```bash
brew services start mysql
brew services start redis
redis-cli ping
```

Expected: `PONG`

3. Create environment:

```bash
cp .env.example .env
```

Put your real OpenWeather key only in `.env`:

```env
OPENWEATHER_API_KEY=YOUR_KEY
```

4. Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

5. Seed data:

```bash
python seed.py
```

6. Start:

```bash
python run.py
```

Open http://localhost:5000

## Health check

Open:

http://localhost:5000/health

Expected:

```json
{"app":"ok","mysql":"ok","redis":"ok"}
```

## Redis test

```bash
python -c "import redis; r=redis.from_url('redis://127.0.0.1:6379/0'); r.set('kisan_test','hello'); print(r.get('kisan_test'))"
```

Expected: `hello`

## Docker

Docker Compose is included separately. Docker uses `mysql` and `redis` hostnames; local macOS execution uses `127.0.0.1`.

The Python base image supports Linux `amd64` and `arm64`. Build a multi-platform OCI image archive with Buildx:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag kisan-bhai:latest \
  --output type=oci,dest=/tmp/kisan-bhai-multiarch.oci.tar \
  .
```

To publish a multi-platform image to a registry, replace `registry-user` with the image namespace and run:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag devopsusr/kisan-bhai:latest \
  --push \
  .
```

Buildx publishes a manifest list, and Docker pulls the matching architecture on each host. `.dockerignore` keeps local virtual environments, caches, and `.env` secrets out of the build context.

### GitHub Actions publishing

The workflow in `.github/workflows/docker-publish.yml` builds `devopsusr/kisan-bhai` for `linux/amd64` and `linux/arm64`. It pushes branch and version tags to Docker Hub and builds pull requests without pushing.

Before the first push, create the `kisan-bhai` repository under the `devopsusr` Docker Hub account. In the GitHub repository, add an Actions repository secret named `DOCKERHUB_TOKEN` containing a Docker Hub access token with permission to push images. Pushes to `main` or `master`, version tags such as `v1.0.0`, and manual workflow runs will publish the image. Pull requests build without needing the Docker Hub secret.

The published image can be pulled with:

```bash
docker pull devopsusr/kisan-bhai:latest
```

### Local Kubernetes with kind

`k8s/kind/stack.yaml` deploys the app, MySQL, and Redis in the `kisan-bhai` namespace. It uses the official `mysql:8.0` and `redis:7-alpine` images; the app image is built locally and loaded into kind, so Docker Hub credentials are not needed for a local cluster.

When the container starts, it runs `seed.py` before Gunicorn. This inserts the built-in crop catalog and cultivation guides if the database is empty; an existing catalog is left unchanged. For running the app directly with Python rather than in Docker, run `python seed.py` once after configuring the database.

Create the namespace and a local Secret (the random database passwords are kept outside the manifest):

```bash
kubectl create namespace kisan-bhai --dry-run=client -o yaml | kubectl apply -f -
if ! kubectl -n kisan-bhai get secret kisan-bhai-secrets >/dev/null 2>&1; then
  kubectl -n kisan-bhai create secret generic kisan-bhai-secrets \
    --from-literal=SECRET_KEY="$(openssl rand -hex 32)" \
    --from-literal=MYSQL_USER=kisan \
    --from-literal=MYSQL_PASSWORD="$(openssl rand -hex 24)" \
    --from-literal=MYSQL_ROOT_PASSWORD="$(openssl rand -hex 24)" \
    --from-literal=OPENWEATHER_API_KEY="${OPENWEATHER_API_KEY:-}"
fi
```

Build and load the app image for the architecture of the local kind node, then deploy:

```bash
docker buildx build --platform linux/arm64 --tag devopsusr/kisan-bhai:kind --load .
kind load docker-image devopsusr/kisan-bhai:kind --name main-cluster
kubectl apply -f k8s/kind/stack.yaml
kubectl -n kisan-bhai rollout status statefulset/mysql
kubectl -n kisan-bhai rollout status deployment/redis
kubectl -n kisan-bhai rollout status deployment/kisan-bhai
kubectl -n kisan-bhai port-forward service/kisan-bhai 5001:5000
```

Open http://localhost:5001. If your kind node is `amd64`, change the build platform to `linux/amd64`. Add `OPENWEATHER_API_KEY` to your shell before creating the Secret if you want weather data. MySQL data is stored in a kind persistent volume; Redis is used as a cache.

## Features

Registration/login, six crop guides, cultivation steps, irrigation guidance, saved crops, browser location, current weather, five-day forecast, Redis weather caching, and rule-based weather-aware advice.
