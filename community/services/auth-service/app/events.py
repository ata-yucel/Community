import json
import logging
from datetime import datetime, timezone

import pika

from .config import settings

logger = logging.getLogger("uvicorn.error")

# Tüm servisler olaylarını bu ortak exchange'e basar; her tüketici kendi
# kuyruğunu bağlar. "topic" tipi: routing key kalıbıyla abone olunabilir
# (ör. "user.*").
EXCHANGE = "community.events"


def publish_user_registered(user_id: str, email: str) -> None:
    # Her yayında kısa ömürlü bir bağlantı açılır: kayıt nadir bir işlem,
    # basitlik > mikro-optimizasyon (yoğunlaşırsa kalıcı bağlantıya geçilir).
    #
    # Broker çökük olsa bile KAYIT BAŞARISIZ OLMAZ: olay loglanır ve yutulur.
    # Garantili teslim (outbox pattern) bilinçli olarak sonraki fazlara
    # bırakıldı — bkz. README "Bilinçli teknik sınırlar".
    event = {
        "event": "user.registered",
        "version": 1,  # şema değişirse tüketici hangi sürümü okuduğunu bilsin
        "user_id": user_id,
        "email": email,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        params = pika.URLParameters(settings.rabbitmq_url)
        # Broker "kapalı ama route edilebilir" ise pika varsayılanı ~15 sn bekler;
        # /register o kadar asılı kalmasın.
        params.socket_timeout = 3
        params.stack_timeout = 5
        params.blocked_connection_timeout = 3
        with pika.BlockingConnection(params) as conn:
            channel = conn.channel()
            channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
            channel.basic_publish(
                exchange=EXCHANGE,
                routing_key="user.registered",
                body=json.dumps(event),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,  # kalıcı: broker yeniden başlasa da mesaj kaybolmaz
                ),
            )
        logger.info("Event yayinlandi: user.registered user_id=%s", user_id)
    except Exception:
        logger.exception(
            "user.registered yayinlanamadi (kayit etkilenmedi) user_id=%s", user_id
        )
