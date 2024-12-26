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
