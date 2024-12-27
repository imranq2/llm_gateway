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

2. Set up the development environment:
    ```sh
    make devsetup
    ```

3. Start the Docker containers:
    ```sh
    make up
    ```

4. Navigate to the GraphQL endpoint:
    ```
    http://localhost:5050/graphql
    ```

## Example Query

Here is a simple GraphQL query to get providers:

```graphql
query getProviders {
    providers(
        query_id: "foo"
    ) {
        total_count
        results {
            result_id
        }
    }
}
```

## Development
There are two things that have to be done on the local developer setup.

Since the OpenWebUI uses Keycloak on both server side and browser side, you need to create a host mapping for `keycloak`.

On Macs, this can be done by adding an entry to `/etc/hosts`:

```sh
127.0.0.1   keycloak
```

## Workaround for bug in OpenWebUI for OAuth
OpenWebUI (at least till v0.5.1) has a bug where it will not create the first user via OAuth.  

So you have to insert the first user into the db manually:

```sql
INSERT INTO public."user" (id,name,email,"role",profile_image_url,api_key,created_at,updated_at,last_active_at,settings,info,oauth_sub) VALUES
	 ('8d967d73-99b8-40ff-ac3b-c71ac19e1286','User','admin@localhost','admin','/user.png',NULL,1735089600,1735089600,1735089609,'{"ui": {"version": "0.4.8"}}','null',NULL);
```

If you don't do this, the UI will just hang on the first page.
