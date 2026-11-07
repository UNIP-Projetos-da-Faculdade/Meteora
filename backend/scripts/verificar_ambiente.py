"""Confere o .env e o MongoDB antes de abrir o servidor."""

from pydantic import ValidationError
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.config import Settings


def main() -> int:
    try:
        settings = Settings()
    except ValidationError:
        print("Confira MONGODB_URI e MONGODB_DATABASE em backend/.env.")
        return 1
    try:
        with MongoClient(
            settings.mongodb_uri.get_secret_value(),
            serverSelectionTimeoutMS=settings.mongodb_timeout_ms,
        ) as client:
            client.admin.command("ping")
            count = client[settings.mongodb_database].medicoes.count_documents({})
    except PyMongoError:
        print("Nao foi possivel acessar o MongoDB. Confira se o servico MongoDB esta em execucao")
        print("e se MONGODB_URI em backend/.env aponta para a instalacao correta.")
        return 1
    print(f"MongoDB conectado. Banco: {settings.mongodb_database}; colecao: medicoes; registros: {count}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
