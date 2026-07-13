import logging
import time
from pathlib import Path

import pika
import pika.exceptions
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import InterfaceError, OperationalError, PendingRollbackError
from sqlalchemy.exc import TimeoutError as SATimeoutError

from .config import settings
from .db import SessionLocal, wait_for_db
from .models import Profile
from .schemas import UserRegisteredV1

# user.registered olayının tüketicisi. Ayrı konteynerde `python -m app.consumer`
# olarak çalışır: çökerse docker restart policy kaldırır, canlılığı heartbeat
# dosyası üzerinden healthcheck'e yansır.

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("consumer")

EXCHANGE = "community.events"  # auth'taki events.py ile AYNI olmalı
QUEUE = "profile.user-registered"  # <sahip-servis>.<amaç> adlandırması
ROUTING_KEY = "user.registered"
HEARTBEAT_FILE = Path("/tmp/consumer-heartbeat")

# "Geçici" sayılan DB hataları: mesaj DÜŞÜRÜLMEZ, requeue edilip tekrar denenir.
# (Yalnızca OperationalError yetmez: kopan sürücü bağlantısı InterfaceError,
# havuz zaman aşımı TimeoutError, yarım kalan işlem PendingRollbackError verir.)
TRANSIENT_DB_ERRORS = (OperationalError, InterfaceError, PendingRollbackError, SATimeoutError)


def _beat() -> None:
    # Healthcheck bu dosyanın tazeliğine bakar. Bilinçli tercih: nabız yalnızca
    # bağlantı kurulunca/mesaj işlenince atılır — uzun süre bağlanamayan
    # tüketici docker ps'te "unhealthy" görünür (dürüst sinyal).
    HEARTBEAT_FILE.touch()


def _handle(channel, method, properties, body) -> None:
    _beat()
    try:
        event = UserRegisteredV1.model_validate_json(body)
    except ValidationError:
        # Zehirli mesaj: requeue edilirse sonsuz döngü olur. Logla ve düşür.
        # Gövde kırpılır — içinde e-posta gibi kişisel veri olabilir.
        logger.error("Zehirli mesaj DUSURULDU (ilk 200 bayt): %r", body[:200])
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return
    try:
        with SessionLocal() as session:
            # RETURNING: satır gerçekten eklendiyse PK döner, çakışmada boş.
            # (rowcount kullanmıyoruz — psycopg3 burada -1 dönebiliyor.)
            stmt = (
                pg_insert(Profile)
                .values(
                    user_id=event.user_id,
                    display_name=event.email.split("@")[0][:50] or "user",
                )
                .on_conflict_do_nothing(index_elements=["user_id"])
                .returning(Profile.user_id)
            )
            created = session.execute(stmt).scalar_one_or_none() is not None
            session.commit()
    except TRANSIENT_DB_ERRORS:
        # Mesajı DÜŞÜRME: hatayı dış döngüye fırlat; bağlantı kapanınca
        # ack'lenmemiş mesaj kuyruğa döner ve backoff sonrası tekrar denenir.
        logger.warning("Gecici DB hatasi; mesaj requeue edilip tekrar denenecek")
        raise
    except Exception:
        # Kod hatası: bu mesaj asla başarılı olmayacak. Logla (gövde değil,
        # kimlik — e-posta loglara yazılmaz) ve düşür.
        logger.exception("Beklenmeyen hata, mesaj DUSURULDU user_id=%s", event.user_id)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return
    # ACK, COMMIT'TEN SONRA: işlenmeden önce çökersek mesaj kaybolmaz.
    channel.basic_ack(delivery_tag=method.delivery_tag)
    logger.info("user.registered islendi user_id=%s created=%s", event.user_id, created)


def main() -> None:
    _beat()  # healthcheck dosyası en baştan var olsun (wait_for_db uzun sürebilir)
    wait_for_db()
    backoff = 1.0
    while True:
        connection = None
        connected_at = None  # yalnızca bağlantı BAŞARILI olunca doldurulur
        try:
            connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
            connected_at = time.monotonic()
            channel = connection.channel()
            # İdempotent tanımlar: taze ortamda tüketici üreticiden önce
            # başlasa bile exchange/kuyruk/binding hazır olur.
            channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
            channel.queue_declare(queue=QUEUE, durable=True)
            channel.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key=ROUTING_KEY)
            # prefetch=1: aynı anda tek mesaj işlenir; çökersek broker anında
            # requeue eder, yerelde mesaj biriktirmeyiz.
            channel.basic_qos(prefetch_count=1)

            def _timer() -> None:
                # Boşta beklerken de nabız at (pika'nın I/O döngüsü içinde çalışır)
                _beat()
                connection.call_later(15, _timer)

            _timer()
            channel.basic_consume(queue=QUEUE, on_message_callback=_handle)
            logger.info("Kuyruk dinleniyor: %s", QUEUE)
            channel.start_consuming()  # normalde buradan dönmez
        except (pika.exceptions.AMQPError, OSError, *TRANSIENT_DB_ERRORS) as exc:
            if connected_at is not None and time.monotonic() - connected_at > 60:
                backoff = 1.0  # uzun süre sorunsuz çalıştıysak yeni arıza say
            logger.warning(
                "Baglanti sorunu (%s: %s) — %.0f sn sonra tekrar",
                type(exc).__name__, exc, backoff,
            )
        finally:
            # Yarı ölü bağlantıyı açık bırakma: kapanınca ack'lenmemiş mesaj
            # ANINDA kuyruğa geri döner (heartbeat timeout beklemez).
            if connection is not None and connection.is_open:
                try:
                    connection.close()
                except Exception:
                    pass
        time.sleep(backoff)
        backoff = min(backoff * 2, 30.0)


if __name__ == "__main__":
    main()
