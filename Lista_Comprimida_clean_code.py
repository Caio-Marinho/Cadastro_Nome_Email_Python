import os
import random
import json
import uuid
from deep_translator import GoogleTranslator
from pathlib import Path
from typing import List, Set, Dict, Union
from pydantic import BaseModel, Field, EmailStr, StrictStr, field_validator, ValidationError, validate_call

# Constantes de Domínios e Caminho do Arquivo e Nomes
DOMINIOS_VALIDOS: List[str] = ["gmail.com",
                               "hotmail.com", "yahoo.com.br", "outlook.com"]
NOMES: List[str] = [
    "Ana Silva", "Pedro Souza", "Maria Oliveira", "João Santos", "Carla Pereira",
    "Lucas Rodrigues", "Fernanda Lima", "Ricardo Costa", "Juliana Gomes", "Bruno Fernandes"
]
CAMINHO_ARQUIVO: Path = Path("contatos.json")


class Contato(BaseModel):
    """
    Representa um contato com ID, nome e e-mail.

    Parâmetros:
    - id: Um identificador único para o contato, gerado automaticamente se não fornecido.
    - nome: O nome do contato.
    - email: O e-mail do contato.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()),
                    alias='contato_id')  # Gera um ID único
    nome: StrictStr
    email: EmailStr

    model_config = {
        "strict": True,
        "populate_by_name": True
    }

    @field_validator("nome")
    def validar_nome(cls, nome):
        tipo_nome = type(nome).__name__
        if not isinstance(nome, str):
            raise TypeError(
                f"O campo 'nome' deve ser uma string, mas recebeu {tipo_nome}.")
        return nome

    @field_validator("email")
    def validar_email(cls, email):
        tipo_email = type(email).__name__
        if not isinstance(email, str):
            raise TypeError(
                f"O campo 'email' deve ser uma string, mas recebeu {tipo_email}.")
        dominio = email.split('@')[-1]
        if dominio not in DOMINIOS_VALIDOS:
            raise ValueError(
                f"Domínio do e-mail '{dominio}' não é permitido. Permitidos: {', '.join(DOMINIOS_VALIDOS)}.")
        return email


"""class DicionarioComoObjeto:

    Converte um dicionário em um objeto acessível por atributos com ponto.

    Exemplo:
        obj = DicionarioComoObjeto({"nome": "Ana", "email": "ana@gmail.com"})
        print(obj.nome)  # Ana

    Parâmetros:
    - dados: Dicionário com chaves como 'nome' e 'email'.

    def __init__(self, dados: Dict[str, str]) -> None:
        # Itera sobre o dicionário e cria atributos no objeto com base nas chaves
        for chave, valor in dados.items():
            setattr(self, chave, valor)"""


@validate_call
def gerar_email_unico(nome: str, dominios: List[str], emails_existentes: Set[str]) -> str:
    """
    Gera um e-mail único baseado no nome do contato e na lista de e-mails já existentes.

    Parâmetros:
    - nome: O nome do contato, usado para gerar o nome de usuário do e-mail.
    - dominios: Lista de domínios válidos para gerar o e-mail (ex: "gmail.com").
    - emails_existentes: Conjunto de e-mails já criados, para evitar duplicação.

    Retorna:
    - Um e-mail único para o contato.
    """
    partes: List[str] = nome.lower().split()  # Divide o nome em partes
    # Gera o nome de usuário com o primeiro e o último nome
    usuario: str = f"{partes[0]}.{partes[-1]}"
    # Escolhe aleatoriamente um domínio válido
    dominio: str = random.choice(dominios)
    email: str = f"{usuario}@{dominio}"

    # Garante que o e-mail seja único, caso já exista, adiciona um número
    contador: int = 1
    while email in emails_existentes:
        # Modifica o e-mail adicionando um número
        email = f"{usuario}{contador}@{dominio}"
        contador += 1

    # Adiciona o novo e-mail à lista de e-mails existentes
    emails_existentes.add(email)
    return email


@validate_call
def criar_contato(nomes: List[str], dominios: List[str], emails_existentes: Set[str]) -> Contato | None:
    """
    Cria um contato com nome aleatório e e-mail único.

    Parâmetros:
    - nomes: Lista de nomes possíveis para o contato.
    - dominios: Lista de domínios válidos para o e-mail.
    - emails_existentes: Conjunto de e-mails já gerados, para garantir que o e-mail será único.

    Retorna:
    - Um objeto `Contato` com um nome e e-mail gerados aleatoriamente.
    """
    nome: str = random.choice(nomes)  # Escolhe um nome aleatório
    email: str = gerar_email_unico(
        nome, dominios, emails_existentes)  # Gera um e-mail único
    try:
        # Retorna um novo objeto Contato
        return Contato(nome=nome, email=email)
    except ValidationError as e:
        for erro in e.errors():
            campo = erro['loc'][0]
            tipo = erro['type']
            msg = GoogleTranslator(
                source='auto', target='pt').translate(erro['msg'])

            print(f"Erro no campo '{campo}': {msg}")


@validate_call
def gerar_contatos(quantidade: int, nomes: List[str], dominios_validos: List[str]) -> List[Contato]:
    """
    Gera uma lista de contatos únicos.

    Parâmetros:
    - quantidade: Número de contatos a serem gerados.
    - dominios_validos: Lista de domínios válidos para o e-mail.

    Retorna:
    - Uma lista com objetos `Contato` gerados.
    """
    emails_existentes: Set[str] = set(
    )  # Conjunto para armazenar e-mails já usados
    # Gera e retorna a lista de contatos
    return [criar_contato(nomes, dominios_validos, emails_existentes) for _ in range(quantidade)]


@validate_call
def filtrar_por_nome(contatos: List[Contato], termo: str) -> List[Contato]:
    """
    Filtra a lista de contatos pelo nome (case-insensitive).

    Parâmetros:
    - contatos: Lista de objetos `Contato` a ser filtrada.
    - termo: O termo a ser buscado no nome dos contatos.

    Retorna:
    - Uma lista de contatos cujo nome contém o termo informado.
    """
    return list(filter(lambda contato: termo.lower() in contato.nome.lower(), contatos))  # Filtra contatos por nome


@validate_call
def deletar_usuario_por_nome(contatos: List[Contato], nome: str) -> List[Contato]:
    """
    Remove um contato da lista com base no nome e, se necessário, no e-mail.

    Parâmetros:
    - contatos: Lista de objetos `Contato` onde o contato será removido.
    - nome: Nome do contato a ser removido.

    Retorna:
    - A lista de contatos atualizada, com o contato removido, se encontrado.
    """
    # Filtra os contatos cujo nome contenha o texto informado
    encontrados: List[Contato] = filtrar_por_nome(contatos, nome)

    # Se não encontrar nenhum contato com esse nome
    if not encontrados:
        print("Nenhum contato encontrado com esse nome.")
        return contatos

    # Se houver exatamente um contato com esse nome, remove diretamente
    if len(encontrados) == 1:
        contatos.remove(encontrados[0])  # Remove o único contato encontrado
        return contatos

    # Se houver mais de um contato com o mesmo nome
    print("Mais de um contato encontrado com esse nome.")
    for indice, contato in enumerate(encontrados, start=1):
        print(
            f"{indice} - ID: {contato.id} | Nome: {contato.nome} | Email: {contato.email}")

    # Solicita ao usuário o e-mail para identificar qual contato remover
    email = input(
        "Digite o e-mail exato do contato que deseja remover: ").strip().lower()

    # Procura o contato com o e-mail informado
    contato_para_remover: Contato | None = next(
        (contato for contato in encontrados if contato.email.lower() == email), None)

    # Se encontrar o contato com o e-mail informado, remove da lista
    if contato_para_remover:
        contatos.remove(contato_para_remover)
    else:
        print("Nenhum contato encontrado com esse e-mail.")

    return contatos  # Retorna a lista de contatos atualizada


@validate_call
def ordenar_por_nome(contatos: List[Contato]) -> List[Contato]:
    """
    Ordena a lista de contatos pelo nome em ordem alfabética.

    Parâmetros:
    - contatos: Lista de objetos `Contato` a ser ordenada.

    Retorna:
    - A lista de contatos ordenada por nome.
    """
    return sorted(contatos, key=lambda contato: contato.nome)  # Ordena os contatos pelo nome


@validate_call
def exibir_contatos(titulo: str, contatos: List[Contato]) -> None:
    """
    Exibe os contatos no terminal com título.

    Parâmetros:
    - titulo: Título a ser exibido antes da lista de contatos.
    - contatos: Lista de objetos `Contato` a ser exibida.

    Retorna:
    - None
    """
    print(f"\n{titulo}")
    for contato in contatos:
        # Exibe informações de cada contato
        print(f"ID: {contato.id} | Nome: {contato.nome} | Email: {contato.email}")


@validate_call
def exportar_para_json(contatos: List[Contato], caminho_arquivo: Path) -> None:
    """
    Exporta a lista de contatos para um arquivo JSON.

    Parâmetros:
    - contatos: Lista de objetos `Contato` a ser exportada.
    - caminho_arquivo: Caminho do arquivo onde os contatos serão salvos.

    Retorna:
    - None
    """
    contatos_dict: List[Dict[str, str]] = [contato.model_dump(
        # Converte os contatos para dicionários
        by_alias=False) for contato in contatos]

    with open(caminho_arquivo, 'w', encoding='utf-8') as arquivo:
        json.dump(contatos_dict, arquivo, ensure_ascii=False,
                  indent=4)  # Escreve os dados no arquivo JSON

    print(f"Contatos exportados para {caminho_arquivo}")


@validate_call
def carregar_json(caminho_arquivo: Path) -> List[Contato] | List:
    """
    Carrega um arquivo JSON e converte em objetos com acesso por atributos.

    Parâmetros:
    - caminho_arquivo: Caminho do arquivo JSON a ser carregado.

    Retorna:
    - Uma lista de objetos `Contato`, onde cada objeto pode ser acessado por atributos.

    Erros:
    - FileNotFoundError: Se o arquivo não existir.
    - ValidationError: Se os dados JSON não corresponderem ao modelo `Contato`.
    """
    if os.path.getsize(caminho_arquivo) == 0:
        # Arquivo vazio: retorna lista vazia ou trata como quiser
        return []
    with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
        dados: List[Dict[str, str]] = json.load(
            arquivo)  # Carrega os dados do arquivo JSON
        # Converte os dados para objetos
        return [Contato(**dado) for dado in dados]


def main() -> None:
    """
    Exibe o menu de opções para o usuário e executa a ação escolhida.

    Parâmetros:
    - Nenhum

    Retorna:
    - None
    """
    try:
        # Carrega os contatos do arquivo JSON
        contatos: List[Contato] = carregar_json(CAMINHO_ARQUIVO)
    except FileNotFoundError:
        print("Arquivo de contatos não encontrado. Iniciando lista vazia.")
        # Cria uma lista vazia se o arquivo não for encontrado
        contatos: List[Contato] = []
    except ValidationError as e:
        for erro in e.errors():
            campo = erro['loc'][0]
            tipo = erro['type']
            msg = GoogleTranslator(
                source='auto', target='pt').translate(erro['msg'])
            print(f"Erro no campo '{campo}': {msg}")

    while True:
        print("\nMenu:")
        print("1 - Gerar Contatos")
        print("2 - Filtrar Contatos por Nome")
        print("3 - Ordenar Contatos por Nome")
        print("4 - Exibir Contatos")
        print("5 - Exportar para JSON")
        print("6 - Carregar Contatos do JSON")
        print("7 - Deletar Contato")
        print("8 - Sair")

        try:
            # Solicita a escolha do usuário
            escolha = int(input("Escolha uma opção: "))
            match escolha:
                case 1:
                    try:
                        # Solicita a quantidade
                        quantidade: int = int(
                            input("Quantos contatos deseja gerar? ").strip())
                        contatos = gerar_contatos(
                            quantidade, NOMES, DOMINIOS_VALIDOS)  # Gera os contatos
                        print(f"{quantidade} contatos gerados com sucesso!")
                    except ValidationError as e:
                        for erro in e.errors():
                            campo = erro['loc'][0]
                            tipo = erro['type']
                            msg = GoogleTranslator(
                                source='auto', target='pt').translate(erro['msg'])
                            print(f"Erro no campo '{campo}': {msg}")

                case 2:
                    try:
                        # Solicita o nome a ser buscado
                        termo_busca: str = input(
                            "Digite o nome a ser buscado: ").strip().lower()
                        contatos_filtrados: List[Contato] = ordenar_por_nome(
                            # Filtra e ordena
                            filtrar_por_nome(contatos, termo_busca))
                        exibir_contatos(
                            f"Contatos filtrados por '{termo_busca}':", contatos_filtrados)
                    except ValidationError as e:
                        for erro in e.errors():
                            campo = erro['loc'][0]
                            tipo = erro['type']
                            msg = GoogleTranslator(
                                source='auto', target='pt').translate(erro['msg'])
                            print(f"Erro no campo '{campo}': {msg}")

                case 3:
                    try:
                        contatos = ordenar_por_nome(
                            contatos)  # Ordena os contatos
                        exibir_contatos("Contatos Ordenados:", contatos)
                    except ValidationError as e:
                        for erro in e.errors():
                            campo = erro['loc'][0]
                            tipo = erro['type']
                            msg = GoogleTranslator(
                                source='auto', target='pt').translate(erro['msg'])
                            print(f"Erro no campo '{campo}': {msg}")

                case 4:
                    if contatos:
                        try:
                            exibir_contatos("Contatos Gerados:", contatos)
                        except ValidationError as e:
                            for erro in e.errors():
                                campo = erro['loc'][0]
                                tipo = erro['type']
                                msg = GoogleTranslator(
                                    source='auto', target='pt').translate(erro['msg'])
                                print(f"Erro no campo '{campo}': {msg}")
                    else:
                        print(
                            "Nenhum contato gerado. Por favor, gere contatos primeiro.")

                case 5:
                    try:
                        # Exporta para JSON
                        exportar_para_json(contatos, CAMINHO_ARQUIVO)
                    except ValidationError as e:
                        for erro in e.errors():
                            campo = erro['loc'][0]
                            tipo = erro['type']
                            msg = GoogleTranslator(
                                source='auto', target='pt').translate(erro['msg'])
                            print(f"Erro no campo '{campo}': {msg}")

                case 6:
                    try:
                        objetos_json: List[Contato] = carregar_json(
                            CAMINHO_ARQUIVO)  # Carrega os contatos do JSON
                        print("Contatos carregados do JSON:")
                        list(map(lambda contato: print(
                            f"ID: {contato.id} | Nome: {contato.nome} | Email: {contato.email}"), objetos_json))
                    except FileNotFoundError:
                        print(
                            "Arquivo não encontrado. Verifique o caminho e tente novamente.")

                case 7:
                    try:
                        deletar_usuario = input(
                            "Informe o contato que deseja deletar: ")
                        contatos = deletar_usuario_por_nome(
                            contatos, deletar_usuario)  # Deleta o contato
                        # Atualiza o arquivo JSON
                        exportar_para_json(contatos, CAMINHO_ARQUIVO)
                        print(
                            f"Contato '{deletar_usuario}' deletado com sucesso!")
                    except ValidationError as e:
                        for erro in e.errors():
                            campo = erro['loc'][0]
                            tipo = erro['type']
                            msg = GoogleTranslator(
                                source='auto', target='pt').translate(erro['msg'])
                            print(f"Erro no campo '{campo}': {msg}")

                case 8:
                    print("Saindo...")
                    break  # Sai do loop e encerra o programa

                case _:
                    print("Opção inválida. Tente novamente.")

        except ValueError:
            # Trata erros de entrada inválida
            print("Por favor, digite um número válido.")


# Execução Principal do Programa
if __name__ == "__main__":
    main()
