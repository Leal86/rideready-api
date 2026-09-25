# RideReady API

API REST do **RideReady**, uma aplicação para planeamento de atividades ao ar livre com apoio de dados meteorológicos e localização.

A API é responsável pela gestão das atividades, persistência dos dados em PostgreSQL, pesquisa e normalização de localidades, consulta das condições meteorológicas e avaliação das condições previstas para a realização de cada atividade.

## Funcionalidades

- Criar, consultar, atualizar e eliminar atividades.
- Pesquisar localidades através de autocomplete.
- Normalizar e armazenar a localização das atividades.
- Obter localização através de coordenadas geográficas.
- Consultar condições meteorológicas atuais.
- Consultar a previsão meteorológica associada a uma atividade.
- Avaliar as condições meteorológicas como `FAVORABLE`, `CAUTION` ou `UNFAVORABLE`.
- Persistir o último snapshot meteorológico consultado.
- Validar conflitos de data e hora entre atividades.
- Impedir a criação de atividades no passado.
- Impedir a conclusão antecipada de atividades futuras.
- Disponibilizar documentação interativa através do Swagger.

## Tecnologias utilizadas

- **Python 3.11** — linguagem utilizada no desenvolvimento.
- **FastAPI** — framework utilizado para implementação da API REST.
- **Pydantic** — validação e serialização dos dados.
- **SQLAlchemy 2** — ORM utilizado no acesso à base de dados.
- **PostgreSQL** — base de dados relacional.
- **Alembic** — gestão das migrations da base de dados.
- **psycopg** — driver PostgreSQL utilizado pelo SQLAlchemy.
- **httpx2** — cliente HTTP utilizado na comunicação com APIs externas.
- **pytest** — execução dos testes automatizados.
- **pytest-cov** — medição da cobertura dos testes.
- **Uvicorn** — servidor ASGI utilizado para executar a aplicação.
- **Docker** — criação do container da API.

## Estrutura do projeto

```text
rideready-api/
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── app/
│   ├── api/
│   │   ├── activities.py
│   │   ├── locations.py
│   │   └── weather.py
│   ├── core/
│   │   └── database.py
│   ├── models/
│   │   └── activity.py
│   ├── repositories/
│   │   └── activity.py
│   ├── schemas/
│   │   ├── activity.py
│   │   ├── location.py
│   │   └── weather.py
│   ├── services/
│   │   ├── activity.py
│   │   ├── assessment.py
│   │   ├── locations.py
│   │   └── weather.py
│   └── main.py
├── tests/
├── .dockerignore
├── .env.example
├── alembic.ini
├── Dockerfile
├── requirements.txt
└── README.md
```

A organização separa responsabilidades entre rotas HTTP, regras de negócio, persistência, schemas de validação e integrações externas.

## Modelo de atividade

Uma atividade possui os seguintes dados principais:

| Campo | Descrição |
| --- | --- |
| `id` | Identificador da atividade |
| `title` | Título da atividade |
| `activity_type` | Tipo da atividade |
| `location_name` | Localização normalizada |
| `latitude` | Latitude da localização |
| `longitude` | Longitude da localização |
| `timezone` | Fuso horário IANA associado à localização |
| `scheduled_date` | Data planeada |
| `scheduled_time` | Hora planeada |
| `notes` | Observações opcionais |
| `status` | Estado da atividade |
| `created_at` | Data/hora de criação |
| `updated_at` | Data/hora da última atualização |

Os tipos de atividade suportados são:

```text
WALKING
RUNNING
CYCLING
HIKING
OTHER
```

Os estados possíveis são:

```text
PLANNED
COMPLETED
CANCELLED
```

A atividade também pode armazenar o último snapshot meteorológico consultado, incluindo temperatura, sensação térmica, precipitação, vento, rajadas e avaliação das condições.

## Endpoints

### Estado da aplicação

| Método | Endpoint | Descrição |
| --- | --- | --- |
| `GET` | `/` | Informação básica da API |
| `GET` | `/health` | Verifica se a API está operacional |

### Atividades

| Método | Endpoint | Descrição |
| --- | --- | --- |
| `GET` | `/activities` | Lista as atividades |
| `GET` | `/activities/{activity_id}` | Consulta uma atividade |
| `POST` | `/activities` | Cria uma atividade |
| `PATCH` | `/activities/{activity_id}` | Atualiza uma atividade |
| `DELETE` | `/activities/{activity_id}` | Elimina uma atividade |
| `GET` | `/activities/{activity_id}/weather` | Consulta a previsão meteorológica da atividade |

O endpoint `POST /activities` suporta o parâmetro opcional:

```text
allow_conflict=true
```

Quando não é utilizado, a API impede por defeito a criação de duas atividades para a mesma data e hora.

### Localizações

| Método | Endpoint | Descrição |
| --- | --- | --- |
| `GET` | `/locations/search?q=...` | Pesquisa sugestões de localidades |
| `GET` | `/locations/reverse?latitude=...&longitude=...` | Obtém uma localização a partir de coordenadas |

### Meteorologia

| Método | Endpoint | Descrição |
| --- | --- | --- |
| `GET` | `/weather/current?latitude=...&longitude=...` | Obtém as condições meteorológicas atuais |

## Exemplo de criação de atividade

Requisição:

```http
POST /activities
Content-Type: application/json
```

```json
{
  "title": "Caminhada no parque",
  "activity_type": "WALKING",
  "location_name": "Lisboa",
  "scheduled_date": "2026-09-30",
  "scheduled_time": "09:30:00",
  "notes": "Caminhada matinal"
}
```

A localização fornecida pelo utilizador é pesquisada através do serviço de localização. A API guarda o nome normalizado e as respetivas coordenadas geográficas.

## Regras de negócio

A API aplica validações adicionais às atividades:

- uma atividade não pode ser criada para uma data e hora no passado;
- por defeito, duas atividades não podem ocupar exatamente a mesma data e hora;
- o conflito pode ser autorizado explicitamente através de `allow_conflict=true`;
- uma atividade futura não pode ser marcada como `COMPLETED` antes da data e hora agendadas, considerando o fuso horário da localização;
- a previsão meteorológica só pode ser atualizada para atividades com estado `PLANNED`;
- alterações em campos relevantes para a meteorologia invalidam o snapshot meteorológico anterior.

## Avaliação meteorológica

Ao consultar a previsão de uma atividade, a API analisa fatores meteorológicos como:

- sensação térmica;
- probabilidade de precipitação;
- precipitação;
- velocidade do vento;
- rajadas de vento.

O resultado é classificado num dos seguintes níveis:

```text
FAVORABLE
CAUTION
UNFAVORABLE
```

A avaliação considera também o tipo de atividade, permitindo aplicar critérios adequados às condições previstas.

Quando a atividade está fora do horizonte disponível de previsão, a API informa que a previsão ainda não está disponível e indica quando poderá ser consultada.

## APIs externas

As APIs externas são consumidas pelo backend do RideReady através de requisições HTTP. Os dados recebidos são tratados pela aplicação antes de serem apresentados ao utilizador, sem redirecionamento para aplicações externas.

### Geoapify

O RideReady utiliza a **Geoapify Geocoding API** para pesquisa de localidades, autocomplete e geocodificação reversa. Os dados tratados pelo backend incluem também o fuso horário IANA associado à localização, utilizado nas validações temporais das atividades.

Endpoints externos utilizados:

```text
GET https://api.geoapify.com/v1/geocode/autocomplete
GET https://api.geoapify.com/v1/geocode/reverse
```

A integração requer uma chave de API configurada através da variável:

```text
GEOAPIFY_API_KEY
```

Para obter a chave é necessário criar uma conta e um projeto na Geoapify. O serviço disponibiliza um plano gratuito, sujeito aos limites definidos pela Geoapify.

Site oficial:

```text
https://www.geoapify.com/
```

Documentação:

```text
https://apidocs.geoapify.com/
```

Planos e condições de utilização:

```text
https://www.geoapify.com/pricing/
```

A utilização da Geoapify está sujeita aos termos, limites e requisitos de atribuição aplicáveis ao plano utilizado.

### Open-Meteo

O RideReady utiliza a **Open-Meteo Weather API** para obter condições meteorológicas atuais e previsões utilizadas no planeamento das atividades.

Endpoint externo utilizado:

```text
GET https://api.open-meteo.com/v1/forecast
```

Para utilização gratuita não comercial, a integração não necessita de chave de API nem de cadastro.

Os dados meteorológicos disponibilizados pelo Open-Meteo estão sujeitos à licença **Creative Commons Attribution 4.0 International (CC BY 4.0)**, que requer atribuição da fonte.

Site oficial:

```text
https://open-meteo.com/
```

Documentação:

```text
https://open-meteo.com/en/docs
```

Termos e condições de utilização:

```text
https://open-meteo.com/en/terms
```

## Configuração do ambiente

Crie um ficheiro `.env` na raiz do projeto com base no `.env.example`:

```env
DATABASE_URL=postgresql+psycopg://<usuario>:<password>@localhost:5432/rideready
GEOAPIFY_API_KEY=your_geoapify_api_key_here
```

Substitua os valores de exemplo pelas credenciais do PostgreSQL configurado no seu ambiente e pela chave obtida na Geoapify.

O ficheiro `.env` não deve ser enviado para o repositório Git.

## Instalação local

### 1. Criar o ambiente virtual

No PowerShell:

```powershell
python -m venv .venv
```

### 2. Ativar o ambiente virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar as dependências

```powershell
python -m pip install -r requirements.txt
```

### 4. Configurar as variáveis de ambiente

Crie o `.env` conforme descrito anteriormente.

### 5. Disponibilizar o PostgreSQL

Disponibilize uma instância PostgreSQL acessível pela aplicação e configure a ligação através da variável:

```text
DATABASE_URL
```

### 6. Executar as migrations

```powershell
python -m alembic upgrade head
```

### 7. Iniciar a API

```powershell
python -m uvicorn app.main:app --reload
```

A API ficará disponível em:

```text
http://localhost:8000
```

## Swagger

O FastAPI gera automaticamente documentação interativa da API.

Swagger UI:

```text
http://localhost:8000/docs
```

OpenAPI:

```text
http://localhost:8000/openapi.json
```

Através do Swagger é possível consultar os schemas e testar diretamente os endpoints REST.

## Testes automatizados

Com o ambiente virtual ativo e o PostgreSQL de testes disponível, execute:

```powershell
python -m pytest
```

Para executar também a análise de cobertura:

```powershell
python -m pytest --cov=app --cov-report=term-missing
```

## Docker

A API possui um `Dockerfile` próprio e pode ser construída independentemente.

Construir a imagem:

```powershell
docker build -t rideready-api .
```

A execução completa do RideReady, incluindo Web, API e PostgreSQL, é orquestrada pelo `compose.yaml` existente no repositório principal `rideready-web`.

Os dois repositórios devem estar lado a lado:

```text
RideReady/
├── rideready-api/
└── rideready-web/
```

A partir de `rideready-web`, o ambiente completo pode ser iniciado com:

```powershell
docker compose up -d --build
```

O Compose executa as migrations do Alembic antes de iniciar a API.

## Persistência

Os dados são armazenados em PostgreSQL através do SQLAlchemy.

A estrutura da base de dados é versionada com Alembic. As migrations existentes criam a tabela `activities`, os índices utilizados para pesquisa e os campos responsáveis pelo último snapshot meteorológico.

No ambiente Docker Compose, os dados do PostgreSQL são mantidos num volume Docker, permitindo preservar as atividades mesmo após a recriação dos containers.

## Principais códigos HTTP

A API utiliza códigos HTTP coerentes com cada situação:

| Código | Utilização |
| --- | --- |
| `200` | Operação realizada com sucesso |
| `201` | Atividade criada |
| `204` | Atividade eliminada |
| `404` | Recurso não encontrado |
| `409` | Conflito de estado ou horário |
| `422` | Dados ou regra de negócio inválidos |
| `503` | Serviço externo indisponível ou não configurado |

## Integração com o RideReady Web

O frontend consome esta API através de HTTP/JSON.

No ambiente local utilizado pelo projeto:

```text
RideReady Web
    |
    | HTTP / JSON
    v
RideReady API
    |
    +---- PostgreSQL
    |
    +---- Geoapify
    |
    +---- Open-Meteo
```

Por defeito, a API permite requisições CORS provenientes do frontend executado em:

```text
http://localhost:5173
```

## Projeto académico

O RideReady foi desenvolvido como MVP académico com arquitetura baseada em componentes independentes, comunicação através de API REST, persistência de dados e integração com serviços externos.