# language_model_gateway

## Overview

This project is a language model gateway that provides an OpenAI compatible API for language models. It is built using FastAPI and GraphQL.

## Prerequisites

- Docker
- Docker Compose
- Make

## Getting Started

To run the project locally, follow these steps:

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Create `docker.env` file in the root of the project based on the `docker.env.example`. 
Update the keys for the functionality/providers you're planning on using.
`AWS_CREDENTIALS_PROFILE` is the only one that is absolutely required to get going.  Set this to the AWS profile you're part of e.g., `admin_dev`.

3. Set up the development environment:
    ```sh
    make devsetup
    ```

4. Start the Docker containers:
    ```sh
    make down; make up
    ```


## Running without OAuth
Just run the following commands to run OpenWebUI without OAuth:

```sh
make down; make up; make up-open-webui
```


## Running with OAuth
Since the OpenWebUI uses Keycloak on both server side and browser side, you need to create a host mapping for `keycloak`.

On Macs, this can be done by adding an entry to `/etc/hosts`:

```sh
127.0.0.1   keycloak
```

Then run:
```shell
make down; make up; make up-open-webui-auth
```

## How to add a new AI Agent
[add_new_agent.md](add_new_agent.md)
