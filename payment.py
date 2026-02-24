import mercadopago
import os
from dotenv import load_dotenv

load_dotenv()

PLANOS = {
    "1": {"titulo": "1 Mês", "valor": 12.90},
    "2": {"titulo": "2 Meses", "valor": 20.00},
    "3": {"titulo": "3 Meses", "valor": 30.00},
}


def gerar_pagamento_pix(plano: str, user_id: int) -> dict:
    sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))  # criado aqui dentro

    plano_info = PLANOS[plano]

    payment_data = {
        "transaction_amount": plano_info["valor"],
        "description": f"Plano {plano_info['titulo']} - SluttyPrinceBot",
        "payment_method_id": "pix",
        "payer": {
            "email": f"user_{user_id}@sluttyprince.bot",
        },
    }

    result = sdk.payment().create(payment_data)
    payment = result["response"]

    if result["status"] == 201:
        return {
            "id": payment["id"],
            "qr_code": payment["point_of_interaction"]["transaction_data"]["qr_code"],
            "qr_code_base64": payment["point_of_interaction"]["transaction_data"][
                "qr_code_base64"
            ],
            "valor": plano_info["valor"],
            "titulo": plano_info["titulo"],
        }
    else:
        raise Exception(f"Erro ao gerar pagamento: {payment}")
