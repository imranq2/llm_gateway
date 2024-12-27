export LANG

.PHONY: Pipfile.lock
Pipfile.lock: # Locks Pipfile and updates the Pipfile.lock on the local file system
	docker compose --progress=plain build --no-cache --build-arg RUN_PIPENV_LOCK=true dev && \
	docker compose --progress=plain run dev sh -c "cp -f /tmp/Pipfile.lock /usr/src/language_model_gateway/Pipfile.lock"

.PHONY:devsetup
devsetup: ## one time setup for devs
	make update && \
	make up && \
	make setup-pre-commit && \
	make tests && \
	make up

.PHONY:build
build: ## Builds the docker for dev
	docker compose build --parallel

.PHONY: up
up: ## starts docker containers
	docker compose up --build -d && \
	echo "waiting for language_model_gateway service to become healthy" && \
	while [ "`docker inspect --format {{.State.Health.Status}} language_model_gateway`" != "healthy" ] && [ "`docker inspect --format {{.State.Health.Status}} language_model_gateway`" != "unhealthy" ] && [ "`docker inspect --format {{.State.Status}} language_model_gateway`" != "restarting" ]; do printf "." && sleep 2; done && \
	if [ "`docker inspect --format {{.State.Health.Status}} language_model_gateway`" != "healthy" ]; then docker ps && docker logs language_model_gateway && printf "========== ERROR: language_model_gateway did not start. Run docker logs language_model_gateway =========\n" && exit 1; fi && \
	echo ""
	@echo language_model_gateway Service: http://localhost:5050/graphql

.PHONY: up-open-webui
up-open-webui: ## starts docker containers
	docker compose --progress=plain -f docker-compose-openwebui.yml up --build -d
	echo "waiting for open-webui service to become healthy" && \
	while [ "`docker inspect --format {{.State.Health.Status}} language_model_gateway-open-webui-1`" != "healthy" ]; do printf "." && sleep 2; done && \
	while [ "`docker inspect --format {{.State.Health.Status}} language_model_gateway-open-webui-1`" != "healthy" ] && [ "`docker inspect --format {{.State.Health.Status}} language_model_gateway-open-webui-1`" != "unhealthy" ] && [ "`docker inspect --format {{.State.Status}} language_model_gateway-open-webui-1`" != "restarting" ]; do printf "." && sleep 2; done && \
	if [ "`docker inspect --format {{.State.Health.Status}} language_model_gateway-open-webui-1`" != "healthy" ]; then docker ps && docker logs language_model_gateway-open-webui-1 && printf "========== ERROR: language_model_gateway-open-webui-1 did not start. Run docker logs language_model_gateway-open-webui-1 =========\n" && exit 1; fi && \
	echo ""
	@echo OpenWebUI: http://localhost:3050

.PHONY: up-open-webui-auth
up-open-webui-auth: ## starts docker containers
	docker compose --progress=plain -f docker-compose-openwebui-auth.yml up --build -d
	echo "waiting for open-webui service to become healthy" && \
	while [ "`docker inspect --format {{.State.Health.Status}} language_model_gateway-open-webui-1`" != "healthy" ]; do printf "." && sleep 2; done && \
	while [ "`docker inspect --format {{.State.Health.Status}} language_model_gateway-open-webui-1`" != "healthy" ] && [ "`docker inspect --format {{.State.Health.Status}} language_model_gateway-open-webui-1`" != "unhealthy" ] && [ "`docker inspect --format {{.State.Status}} language_model_gateway-open-webui-1`" != "restarting" ]; do printf "." && sleep 2; done && \
	if [ "`docker inspect --format {{.State.Health.Status}} language_model_gateway-open-webui-1`" != "healthy" ]; then docker ps && docker logs language_model_gateway-open-webui-1 && printf "========== ERROR: language_model_gateway-open-webui-1 did not start. Run docker logs language_model_gateway-open-webui-1 =========\n" && exit 1; fi && \
	echo ""
	make insert-admin-user
	@echo OpenWebUI: http://localhost:3050 tester/password
	@echo Keycloak: http://keycloak:8080 admin/password
	@echo OIDC debugger: http://localhost:8085

.PHONY: down
down: ## stops docker containers
	docker compose down --remove-orphans

.PHONY:update
update: Pipfile.lock setup-pre-commit  ## Updates all the packages using Pipfile
	make build && \
	make run-pre-commit && \
	echo "In PyCharm, do File -> Invalidate Caches/Restart to refresh" && \
	echo "If you encounter issues with remote sources being out of sync, click on the 'Remote Python' feature on" && \
	echo "the lower status bar and reselect the same interpreter and it will rebuild the remote source cache." && \
	echo "See this link for more details:" && \
	echo "https://intellij-support.jetbrains.com/hc/en-us/community/posts/205813579-Any-way-to-force-a-refresh-of-external-libraries-on-a-remote-interpreter-?page=2#community_comment_360002118020"


.DEFAULT_GOAL := help
.PHONY: help
help: ## Show this help.
	# from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY:tests
tests: ## Runs all the tests
	docker compose run --rm --name language_model_gateway_tests dev pytest tests

.PHONY:tests-integration
tests-integration: ## Runs all the tests
	docker compose run --rm -e RUN_TESTS_WITH_REAL_LLM=1 --name language_model_gateway_tests dev pytest tests tests_integration

.PHONY:shell
shell: ## Brings up the bash shell in dev docker
	docker compose run --rm --name language_model_gateway_shell dev /bin/sh

.PHONY:clean-pre-commit
clean-pre-commit: ## removes pre-commit hook
	rm -f .git/hooks/pre-commit

.PHONY:setup-pre-commit
setup-pre-commit:
	cp ./pre-commit-hook ./.git/hooks/pre-commit

.PHONY:run-pre-commit
run-pre-commit: setup-pre-commit
	./.git/hooks/pre-commit pre_commit_all_files

.PHONY: clean
clean: down ## Cleans all the local docker setup
ifneq ($(shell docker volume ls | grep "language_model_gateway"| awk '{print $$2}'),)
	docker volume ls | grep "language_model_gateway" | awk '{print $$2}' | xargs docker volume rm
endif

.PHONY: insert-admin-user
insert-admin-user:
	docker exec -i language_model_gateway-open-webui-db-1 psql -U myapp_user -d myapp_db -p 5431 -c \
    "INSERT INTO public.\"user\" (id,name,email,\"role\",profile_image_url,api_key,created_at,updated_at,last_active_at,settings,info,oauth_sub) \
    SELECT '8d967d73-99b8-40ff-ac3b-c71ac19e1286','User','admin@localhost','admin','/user.png',NULL,1735089600,1735089600,1735089609,'{"ui": {"version": "0.4.8"}}','null',NULL \
    WHERE NOT EXISTS (SELECT 1 FROM public.\"user\" WHERE id = '8d967d73-99b8-40ff-ac3b-c71ac19e1286');"

CERT_DIR := certs
CERT_KEY := $(CERT_DIR)/localhost.key
CERT_CRT := $(CERT_DIR)/localhost.crt

.PHONY: all clean create-certs

all: create-certs

# Create certificates directory if it doesn't exist
$(CERT_DIR):
	mkdir -p $(CERT_DIR)

# Generate self-signed certificates for localhost
create-certs: $(CERT_DIR)
	openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout $(CERT_KEY) \
		-out $(CERT_CRT) \
		-subj "/CN=localhost" \
		-addext "subjectAltName = DNS:localhost,IP:127.0.0.1"
	@echo "Self-signed certificates generated in $(CERT_DIR)"
	@echo "Key: $(CERT_KEY)"
	@echo "Certificate: $(CERT_CRT)"

# Optional: Add a target to view certificate details
show-cert:
	@if [ -f "$(CERT_CRT)" ]; then \
		openssl x509 -in $(CERT_CRT) -text -noout; \
	else \
		echo "Certificate not found. Run 'make create-certs' first."; \
	fi

# Optional: Add a target to remove certificates
clean:
	rm -rf $(CERT_DIR)

# Optional: Add a target to trust the certificate on macOS
trust-cert-macos:
	@if [ -f "$(CERT_CRT)" ]; then \
		sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain $(CERT_CRT); \
		echo "Certificate added to system trust store"; \
	else \
		echo "Certificate not found. Run 'make create-certs' first."; \
	fi
