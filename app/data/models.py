import psycopg2

from app import config


class Database:
    """DB 연결을 열고, 블록이 끝나면 커밋 후 닫습니다."""

    def __enter__(self):
        self.connection = psycopg2.connect(
            dbname=config['DB']['DB_NAME'],
            user=config['DB']['USER'],
        )
        return self.connection.cursor()

    def __exit__(self, *args):
        try:
            self.connection.commit()
        except Exception:
            self.connection.rollback()
        finally:
            self.connection.close()


class CouponModel:
    def create_table(self) -> None:
        with Database() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS coupon (
                    id SERIAL PRIMARY KEY,
                    description TEXT NOT NULL,
                    code TEXT NOT NULL,
                    cost INTEGER NOT NULL
                )
            ''')

    def insert_model(self, description: str, code: str, cost: int) -> str:
        with Database() as cursor:
            try:
                cursor.execute(
                    'INSERT INTO coupon (description, code, cost) VALUES (%s, %s, %s)',
                    (description, code, cost))
            except Exception as error:
                return f'쿠폰 등록 실패: {error}'
            return '쿠폰을 등록했습니다.'

    def get_coupon(self, coupon_id: int):
        """쿠폰 코드와 가격을 돌려줍니다. 없으면 None."""
        try:
            coupon_id = int(coupon_id)
        except (TypeError, ValueError):
            return None
        with Database() as cursor:
            cursor.execute('SELECT code, cost FROM coupon WHERE id = %s', (coupon_id,))
            return cursor.fetchone()

    def show_coupons(self) -> list:
        """아직 팔리지 않은 쿠폰 목록: (id, 설명, 가격)"""
        with Database() as cursor:
            cursor.execute('''
                SELECT c.id, c.description, c.cost FROM coupon AS c
                LEFT JOIN tx AS t ON t.coupon_id = c.id
                WHERE t.coupon_id IS NULL
                ORDER BY c.id
            ''')
            return cursor.fetchall()


class TxModel:
    def create_table(self) -> None:
        with Database() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tx (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    value INTEGER NOT NULL,
                    coupon_id INTEGER UNIQUE,
                    FOREIGN KEY (coupon_id) REFERENCES coupon(id)
                )
            ''')

    def insert_model(self, user_id: str, value: int, coupon_id: int = None):
        """거래 기록. 성공이면 ('ok', 메시지), 실패면 ('err', 메시지)"""
        with Database() as cursor:
            try:
                cursor.execute('''
                    INSERT INTO tx (user_id, value, coupon_id)
                    VALUES (%s, %s, %s)
                ''', (str(user_id), value, coupon_id))
            except psycopg2.IntegrityError:
                return ('err', '이미 구매된 쿠폰입니다.')
            except Exception as error:
                return ('err', f'처리 중 오류: {error}')
            return ('ok', '처리되었습니다.')

    def view_balance(self, user_id: str) -> int:
        """유저의 크레딧 잔액. 쿠폰 구매는 차감, 지급은 가산."""
        with Database() as cursor:
            cursor.execute('''
                SELECT COALESCE(SUM(
                    CASE
                        WHEN coupon_id IS NOT NULL THEN value * (-1)
                        ELSE value
                    END), 0)
                FROM tx
                WHERE user_id = %s
            ''', (str(user_id),))
            return int(cursor.fetchone()[0])
