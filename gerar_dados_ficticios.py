"""
Gera funcionários e batidas de ponto FICTÍCIOS no MESMO formato que o sistema Java grava
(tabela pontos_registrados: 1 linha por batida, data dd/MM/yyyy e hora HH:mm:ss).

Inclui anomalias de propósito (atrasos, almoço curto, hora extra, saída esquecida,
jornada muito longa e um funcionário que bate sempre no mesmo horário).

Uso:  python gerar_dados_ficticios.py
Depois execute o arquivo seed_ficticio_java.sql no MySQL Workbench.
"""
import random
from datetime import date, datetime, timedelta

random.seed(42)

NOMES = [
    "Ana Souza", "Bruno Lima", "Carla Mendes", "Diego Alves", "Elisa Ramos",
    "Felipe Costa", "Gabriela Nunes", "Hugo Pereira", "Isabela Rocha", "João Barros",
    "Karen Dias", "Lucas Freitas", "Marina Teixeira", "Nicolas Prado", "Olivia Castro",
]
DIAS = 60  # quantos dias para trás


def hhmm(base, var_min):
    h, m = map(int, base.split(":"))
    t = datetime(2000, 1, 1, h, m) + timedelta(minutes=random.randint(-var_min, var_min))
    return t.strftime("%H:%M:%S")


def soma(hora, minutos):
    t = datetime.strptime(hora, "%H:%M:%S") + timedelta(minutes=minutos)
    return t.strftime("%H:%M:%S")


def gerar_batidas():
    """Devolve (funcionarios, batidas). funcionarios = [(nome, email)];
    batidas = [(email, 'dd/MM/yyyy', 'HH:mm:ss')]."""
    funcionarios = [(nome, f"func{i:02d}@exemplo.com") for i, nome in enumerate(NOMES, start=1)]

    perfil = {}
    for _, email in funcionarios:
        perfil[email] = random.choices(
            ["pontual", "atrasado_frequente", "hora_extra", "almoco_curto", "robotico"],
            weights=[50, 15, 15, 10, 10],
        )[0]
    perfil["func03@exemplo.com"] = "robotico"  # garante um caso de "horário idêntico"

    batidas = []
    hoje = date.today()
    for _, email in funcionarios:
        p = perfil[email]
        for d in range(DIAS, 0, -1):
            dia = hoje - timedelta(days=d)
            if dia.weekday() >= 5:      # sem sábado e domingo
                continue
            if random.random() < 0.04:  # falta o dia inteiro
                continue

            if p == "robotico":
                ent, sal_alm, volta, sai = "08:00:00", "12:00:00", "13:00:00", "17:00:00"
            else:
                ent = hhmm("08:00", 5)
                sal_alm = hhmm("12:00", 8)
                volta = soma(sal_alm, random.randint(60, 75))
                sai = hhmm("17:00", 8)

            if p == "atrasado_frequente" and random.random() < 0.5:
                ent = hhmm("08:35", 15)
            if p == "hora_extra" and random.random() < 0.5:
                sai = hhmm("19:30", 30)
            if p == "almoco_curto" and random.random() < 0.6:
                volta = soma(sal_alm, random.randint(15, 35))

            r = random.random()
            if r < 0.03:
                sai = None                  # esqueceu de bater a saída
            elif r < 0.05:
                sal_alm = volta = None      # não bateu o almoço
            elif r < 0.06:
                sai = "22:40:00"            # jornada muito longa

            for hora in (ent, sal_alm, volta, sai):
                if hora is not None:
                    batidas.append((email, dia.strftime("%d/%m/%Y"), hora))
    return funcionarios, batidas


def montar_sql(funcionarios, batidas):
    linhas = [
        "USE mypoint_db;",
        "SET SQL_SAFE_UPDATES = 0;",
        # limpa só os dados fictícios anteriores (e-mails @exemplo.com)
        "DELETE FROM pontos_registrados WHERE email_funcionario LIKE '%@exemplo.com';",
        "DELETE FROM registros_ponto WHERE usuario_id IN "
        "(SELECT id FROM usuarios WHERE email LIKE '%@exemplo.com');",
        # usuários de teste (não duplica se já existirem)
        "INSERT IGNORE INTO usuarios (nome, email, senha, perfil) VALUES "
        "('Admin Teste', 'admin@exemplo.com', 'ficticia123', 'admin');",
    ]
    for nome, email in funcionarios:
        linhas.append(
            "INSERT IGNORE INTO usuarios (nome, email, senha, perfil) VALUES "
            f"('{nome}', '{email}', 'ficticia123', 'funcionario');"
        )

    por_email = {}
    for email, data, hora in batidas:
        por_email.setdefault(email, []).append((data, hora))
    for email, itens in por_email.items():
        valores = ",\n  ".join(f"('{email}', '{d}', '{h}')" for d, h in itens)
        linhas.append(
            "INSERT INTO pontos_registrados (email_funcionario, data_ponto, hora_ponto) VALUES\n  "
            + valores + ";"
        )
    linhas.append("SET SQL_SAFE_UPDATES = 1;")
    return "\n".join(linhas) + "\n"


if __name__ == "__main__":
    funcionarios, batidas = gerar_batidas()
    with open("seed_ficticio_java.sql", "w", encoding="utf-8") as f:
        f.write(montar_sql(funcionarios, batidas))
    print(f"Gerado seed_ficticio_java.sql com {len(funcionarios)} funcionários e {len(batidas)} batidas.")